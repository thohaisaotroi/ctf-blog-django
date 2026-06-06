import re
import json
import markdown as _md
import cloudinary.uploader
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.contrib.auth import (
    authenticate, get_user_model,
    login as auth_login, logout as auth_logout,
)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import F, Q, Count, Sum, Value
from django.db.models.functions import Coalesce, Greatest

from blog.models import (
    Post, Category, BlogUser, Comment, Tag, PostTag, PostLike, NewsletterSubscriber
)


# ── Helpers ───────────────────────────────────────────────────────────────────

staff_required = user_passes_test(
    lambda u: u.is_active and u.is_staff,
    login_url='/admin-login/',
)


def _build_comment_tree(flat):
    by_id = {}
    for c in flat:
        c['replies'] = []
        by_id[c['id']] = c

    roots = []
    for c in flat:
        pid = c.get('parent_id')
        if pid and pid in by_id:
            c['parent_author'] = by_id[pid]['author_name']
            by_id[pid]['replies'].append(c)
        else:
            c['parent_author'] = None
            roots.append(c)
    return roots


def _md_to_html(text):
    return _md.markdown(text, extensions=['fenced_code', 'tables', 'nl2br'])


def _extract_toc(html):
    toc = []
    seen = {}

    def _replace(m):
        level = int(m.group(1))
        inner = m.group(2)
        text = re.sub(r'<[^>]+>', '', inner).strip()
        base_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'heading'
        seen[base_id] = seen.get(base_id, 0) + 1
        uid = base_id if seen[base_id] == 1 else f'{base_id}-{seen[base_id]}'
        toc.append({'level': level, 'text': text, 'id': uid})
        return f'<h{level} id="{uid}">{inner}</h{level}>'

    modified = re.sub(r'<h([23])>(.*?)</h\1>', _replace, html,
                      flags=re.IGNORECASE | re.DOTALL)
    return modified, toc


def _make_slug(title, existing_id=None):
    base = slugify(title)[:200] or 'post'
    qs = Post.objects.filter(slug=base)
    if existing_id:
        qs = qs.exclude(id=existing_id)
    if not qs.exists():
        return base
    for n in range(2, 1000):
        candidate = f'{base}-{n}'
        qs2 = Post.objects.filter(slug=candidate)
        if existing_id:
            qs2 = qs2.exclude(id=existing_id)
        if not qs2.exists():
            return candidate
    return base


def _post_to_dict(p):
    """Convert a Post ORM instance (with select_related) to a template-compatible dict."""
    return {
        'id':           p.id,
        'title':        p.title,
        'slug':         p.slug,
        'content':      p.content,
        'excerpt':      p.excerpt or '',
        'is_published': p.is_published,
        'status':       p.status,
        'views':        p.views,
        'likes':        p.likes,
        'cover_image':  p.cover_image,
        'created_at':   p.created_at,
        'secret_flag':  p.secret_flag,
        'author':       p.author.username,
        'category':     p.category.name,
        'cat_slug':     p.category.slug,
    }


def _enrich_post(post):
    """Add tags list and TOC to a post dict. Mutates in place, returns post."""
    if not post:
        return post
    post['tags'] = list(
        Tag.objects.filter(posttag__post_id=post['id']).values('name', 'slug')
    )
    post['content'], post['toc'] = _extract_toc(post['content'] or '')
    return post


def _get_comments(post_id):
    flat = list(
        Comment.objects.filter(post_id=post_id)
        .order_by('created_at')
        .values('id', 'post_id', 'parent_id', 'author_name', 'content', 'created_at')
    )
    return flat, _build_comment_tree(flat)


def _get_related(post_id, cat_slug, limit=4):
    return list(
        Post.objects.filter(status='published', category__slug=cat_slug)
        .exclude(id=post_id)
        .select_related('author')
        .order_by('-created_at')[:limit]
        .values('id', 'title', 'slug', 'cover_image', 'created_at')
    )


# ── Public Views ──────────────────────────────────────────────────────────────

def index(request):
    featured_qs = (
        Post.objects.filter(status='published', category__slug='featured')
        .select_related('author', 'category')
        .order_by('-views')
    )
    featured_obj = featured_qs.first()
    featured = _post_to_dict(featured_obj) if featured_obj else None

    posts_qs = (
        Post.objects.filter(status='published')
        .select_related('author', 'category')
        .order_by('-created_at')[:6]
    )
    posts = [_post_to_dict(p) for p in posts_qs]

    return render(request, 'index.html', {'featured': featured, 'posts': posts})


def blog(request):
    category = request.GET.get('category', '')
    try:
        page = max(1, int(request.GET.get('page', 1) or 1))
    except (ValueError, TypeError):
        page = 1
    per_page = 6

    categories = list(Category.objects.order_by('name').values('id', 'name', 'slug', 'description'))

    qs = Post.objects.filter(status='published').select_related('author', 'category')
    if category:
        qs = qs.filter(category__slug=category)
    qs = qs.order_by('-created_at')

    total = qs.count()
    offset = (page - 1) * per_page
    posts_page = qs[offset: offset + per_page]

    posts = []
    for p in posts_page:
        d = _post_to_dict(p)
        d['tags'] = list(Tag.objects.filter(posttag__post_id=p.id).values('name', 'slug'))
        posts.append(d)

    total_pages = max(1, (total + per_page - 1) // per_page)
    page_range  = list(range(max(1, page - 2), min(total_pages + 1, page + 3)))

    return render(request, 'blog.html', {
        'posts':           posts,
        'categories':      categories,
        'active_category': category,
        'page':            page,
        'total_pages':     total_pages,
        'page_range':      page_range,
        'total':           total,
    })


def search(request):
    query = request.GET.get('q', '').strip()
    posts = []
    if query:
        qs = (
            Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                status='published',
            )
            .select_related('author', 'category')
            .order_by('-created_at')[:50]
        )
        for p in qs:
            d = _post_to_dict(p)
            d['tags'] = list(Tag.objects.filter(posttag__post_id=p.id).values('name', 'slug'))
            posts.append(d)

    return render(request, 'search.html', {'posts': posts, 'query': query})


def _render_post_detail(request, post_obj, post_id_ctx, sql_error=None, slug_view=False):
    """Shared render logic for post_detail and post_detail_by_slug."""
    post = _post_to_dict(post_obj) if post_obj else None
    comments = []
    comment_count = 0
    related_posts = []

    if post:
        Post.objects.filter(id=post['id']).update(views=F('views') + 1)
        post['views'] += 1
        _enrich_post(post)
        flat, comments = _get_comments(post['id'])
        comment_count = len(flat)
        related_posts = _get_related(post['id'], post['cat_slug'])

    user_liked = (
        PostLike.objects.filter(post_id=post['id'], user=request.user).exists()
        if post and request.user.is_authenticated else False
    )

    return render(request, 'post.html', {
        'post':          post,
        'comments':      comments,
        'comment_count': comment_count,
        'tags':          post.get('tags', []) if post else [],
        'toc':           post.get('toc', []) if post else [],
        'related_posts': related_posts,
        'sql_error':     sql_error,
        'post_id':       post_id_ctx,
        'user_liked':    user_liked,
        'slug_view':     slug_view,
    })


def post_detail_by_slug(request, slug):
    post_obj = (
        Post.objects.filter(slug=slug, status='published')
        .select_related('author', 'category')
        .first()
    )
    return _render_post_detail(request, post_obj, post_id_ctx=slug, slug_view=True)


def post_detail(request):
    post_id = request.GET.get('id', '1')
    post_id_int = None
    try:
        post_id_int = int(post_id)
    except (ValueError, TypeError):
        pass

    post_obj = None
    if post_id_int is not None:
        post_obj = (
            Post.objects.filter(id=post_id_int, is_published=True)
            .select_related('author', 'category')
            .first()
        )

    return _render_post_detail(request, post_obj, post_id_ctx=post_id)


# ── Like Toggle ───────────────────────────────────────────────────────────────

@require_POST
def toggle_like(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required'}, status=401)

    like, created = PostLike.objects.get_or_create(post_id=post_id, user=request.user)
    if created:
        Post.objects.filter(id=post_id).update(likes=F('likes') + 1)
        action = 'liked'
    else:
        like.delete()
        Post.objects.filter(id=post_id).update(likes=Greatest(F('likes') - 1, Value(0)))
        action = 'unliked'

    likes = Post.objects.filter(id=post_id).values_list('likes', flat=True).first() or 0
    return JsonResponse({'action': action, 'likes': likes})


# ── Newsletter ────────────────────────────────────────────────────────────────

@require_POST
def newsletter_subscribe(request):
    email   = request.POST.get('email', '').strip()
    name    = request.POST.get('name', '').strip()
    consent = request.POST.get('consent')

    if not email or not consent:
        return JsonResponse({'status': 'error', 'message': 'Email and consent required.'}, status=400)

    try:
        NewsletterSubscriber.objects.get_or_create(
            email=email[:254],
            defaults={'name': name[:100]},
        )
        return JsonResponse({'status': 'ok', 'message': 'Subscribed successfully!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ── About / Contact ───────────────────────────────────────────────────────────

def about(request):
    return render(request, 'about.html')


def contact(request):
    sent = False
    if request.method == 'POST':
        sent = True
    return render(request, 'contact.html', {'sent': sent})


@require_POST
def add_comment(request):
    if not request.user.is_authenticated:
        return redirect(f'/auth/login/?next={request.POST.get("next", "/")}')

    post_id_raw   = request.POST.get('post_id', '').strip()
    content       = request.POST.get('content', '').strip()
    parent_id_raw = request.POST.get('parent_id', '').strip()

    parent_id = None
    if parent_id_raw:
        try:
            parent_id = int(parent_id_raw)
        except ValueError:
            parent_id = None

    try:
        post_id = int(post_id_raw)
    except (ValueError, TypeError):
        return redirect('/')

    if post_id and content:
        Comment.objects.create(
            post_id=post_id,
            author=request.user,
            author_name=request.user.username,
            parent_id=parent_id,
            content=content,
        )

    slug = Post.objects.filter(id=post_id).values_list('slug', flat=True).first()
    anchor = f'#comment-{parent_id}' if parent_id else '#comments'
    if slug:
        return redirect(f'/blog/{slug}/{anchor}')
    return redirect(f'/post/?id={post_id}{anchor}')


# ── Admin Views ──────────────────────────────────────────────────────────────

def admin_login(request):
    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            auth_login(request, user)
            return redirect('/admin-dashboard/')
        else:
            error = 'ACCESS_DENIED :: Invalid credentials or insufficient role.'

    return render(request, 'ctf_admin/login.html', {'error': error})


@staff_required
def admin_dashboard(request):

    success_msg = request.GET.get('msg', '')

    users = list(BlogUser.objects.order_by('id').values(
        'id', 'username', 'email', 'role', 'date_joined'
    ))

    posts = list(
        Post.objects.select_related('author', 'category')
        .order_by('id')
        .annotate(
            author_name=F('author__username'),
            category_name=F('category__name'),
        )
        .values(
            'id', 'title', 'status', 'is_published', 'views', 'likes',
            'secret_flag', 'created_at', 'author_name', 'category_name',
        )
    )

    stats = Post.objects.aggregate(
        post_count  = Count('id', filter=Q(status='published')),
        draft_count = Count('id', filter=Q(status='draft')),
        total_views = Coalesce(Sum('views', filter=Q(status='published')), Value(0)),
    )

    categories = list(
        Category.objects.annotate(post_count=Count('post'))
        .order_by('id')
        .values('id', 'name', 'slug', 'description', 'post_count')
    )

    return render(request, 'ctf_admin/dashboard.html', {
        'users':            users,
        'posts':            posts,
        'categories':       categories,
        'post_count':       stats['post_count'],
        'draft_count':      stats['draft_count'],
        'user_count':       BlogUser.objects.count(),
        'comment_count':    Comment.objects.count(),
        'total_views':      stats['total_views'],
        'subscriber_count': NewsletterSubscriber.objects.count(),
        'success_msg':      success_msg,
    })


def admin_logout(request):
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    request.session.flush()
    return redirect('/admin-login/')


# ── Admin CRUD ────────────────────────────────────────────────────────────────

def _save_post_tags(post_id, tags_str):
    PostTag.objects.filter(post_id=post_id).delete()
    for tag_name in tags_str.split(','):
        tag_name = tag_name.strip()
        if not tag_name:
            continue
        tag_slug = slugify(tag_name)[:50]
        tag, _ = Tag.objects.get_or_create(
            slug=tag_slug, defaults={'name': tag_name[:50]}
        )
        PostTag.objects.get_or_create(post_id=post_id, tag=tag)


@staff_required
def admin_post_create(request):
    error = None
    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        content_raw = request.POST.get('content', '')
        excerpt     = request.POST.get('excerpt', '').strip()
        category_id = request.POST.get('category_id', '')
        status      = request.POST.get('status', 'draft')
        tags_str    = request.POST.get('tags', '').strip()
        cover_image = request.POST.get('cover_image', '').strip() or None
        is_published = status == 'published'

        if not title or not category_id:
            error = 'ERR :: Title and category are required.'
        else:
            try:
                content_html = _md_to_html(content_raw)
                slug = _make_slug(title)
                author = request.user
                post = Post.objects.create(
                    title=title, slug=slug, content=content_html, excerpt=excerpt,
                    author=author, category_id=category_id,
                    is_published=is_published, status=status,
                    views=0, likes=0, cover_image=cover_image,
                )
                if tags_str:
                    _save_post_tags(post.id, tags_str)
                return redirect('/admin-dashboard/?msg=post_created')
            except Exception as e:
                error = f'DB_ERROR :: {e}'

    categories = list(Category.objects.order_by('name').values('id', 'name'))
    return render(request, 'ctf_admin/post_form.html', {
        'categories': categories, 'action': 'create',
        'error': error, 'post': {}, 'post_tags': '',
    })


@staff_required
def admin_post_edit(request, post_id):
    error = None
    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        content_raw = request.POST.get('content', '')
        excerpt     = request.POST.get('excerpt', '').strip()
        category_id = request.POST.get('category_id', '')
        status      = request.POST.get('status', 'draft')
        tags_str    = request.POST.get('tags', '').strip()
        cover_image = request.POST.get('cover_image', '').strip() or None
        is_published = status == 'published'

        if not title or not category_id:
            error = 'ERR :: Title and category are required.'
        else:
            try:
                content_html = _md_to_html(content_raw)
                slug = _make_slug(title, existing_id=post_id)
                Post.objects.filter(id=post_id).update(
                    title=title, slug=slug, content=content_html, excerpt=excerpt,
                    category_id=category_id, is_published=is_published,
                    status=status, cover_image=cover_image,
                )
                _save_post_tags(post_id, tags_str)
                return redirect('/admin-dashboard/?msg=post_updated')
            except Exception as e:
                error = f'DB_ERROR :: {e}'

    post = Post.objects.filter(id=post_id).values(
        'id', 'title', 'slug', 'content', 'excerpt',
        'category_id', 'is_published', 'status', 'cover_image',
    ).first()
    if not post:
        return redirect('/admin-dashboard/')

    categories = list(Category.objects.order_by('name').values('id', 'name'))
    post_tags = ', '.join(
        Tag.objects.filter(posttag__post_id=post_id).values_list('name', flat=True)
    )
    return render(request, 'ctf_admin/post_form.html', {
        'categories': categories, 'action': 'edit',
        'error': error, 'post': post, 'post_tags': post_tags,
    })


@staff_required
@require_POST
def admin_post_delete(request, post_id):
    PostTag.objects.filter(post_id=post_id).delete()
    Comment.objects.filter(post_id=post_id).delete()
    Post.objects.filter(id=post_id).delete()
    return redirect('/admin-dashboard/?msg=post_deleted')


# ── Admin User CRUD ───────────────────────────────────────────────────────────

@staff_required
def admin_user_create(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        email    = request.POST.get('email', '').strip()
        role     = request.POST.get('role', 'user')

        if not username or not password or not email:
            error = 'ERR :: Username, password and email are required.'
        else:
            try:
                BlogUser.objects.create_user(
                    username=username, password=password,
                    email=email, role=role,
                )
                return redirect('/admin-dashboard/?msg=user_created')
            except Exception as e:
                error = f'DB_ERROR :: {e}'

    return render(request, 'ctf_admin/user_form.html', {
        'action': 'create', 'error': error, 'user': {},
    })


@staff_required
def admin_user_edit(request, user_id):
    error = None
    if request.method == 'POST':
        username     = request.POST.get('username', '').strip()
        email        = request.POST.get('email', '').strip()
        role         = request.POST.get('role', 'user')
        new_password = request.POST.get('password', '').strip()

        if not username or not email:
            error = 'ERR :: Username and email are required.'
        else:
            try:
                updates = {'username': username, 'email': email, 'role': role}
                BlogUser.objects.filter(id=user_id).update(**updates)
                if new_password:
                    user_obj = BlogUser.objects.get(id=user_id)
                    user_obj.set_password(new_password)
                    user_obj.save(update_fields=['password'])
                return redirect('/admin-dashboard/?msg=user_updated')
            except Exception as e:
                error = f'DB_ERROR :: {e}'

    user = BlogUser.objects.filter(id=user_id).values(
        'id', 'username', 'email', 'role'
    ).first()
    if not user:
        return redirect('/admin-dashboard/')

    return render(request, 'ctf_admin/user_form.html', {
        'action': 'edit', 'error': error, 'user': user,
    })


@staff_required
@require_POST
def admin_user_delete(request, user_id):
    user = BlogUser.objects.filter(id=user_id).values('username').first()
    if user and user['username'] == request.user.username:
        return redirect('/admin-dashboard/?msg=user_self_delete')
    Post.objects.filter(author_id=user_id).update(author_id=1)
    BlogUser.objects.filter(id=user_id).delete()
    return redirect('/admin-dashboard/?msg=user_deleted')


# ── Admin Category CRUD ───────────────────────────────────────────────────────

@staff_required
def admin_category_create(request):
    error = None
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        slug        = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()

        if not name or not slug:
            error = 'ERR :: Name and slug are required.'
        else:
            try:
                Category.objects.create(name=name, slug=slug, description=description)
                return redirect('/admin-dashboard/?msg=cat_created')
            except Exception as e:
                error = f'DB_ERROR :: {e}'

    return render(request, 'ctf_admin/category_form.html', {
        'action': 'create', 'error': error, 'cat': {},
    })


@staff_required
def admin_category_edit(request, cat_id):
    error = None
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        slug        = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()

        if not name or not slug:
            error = 'ERR :: Name and slug are required.'
        else:
            try:
                Category.objects.filter(id=cat_id).update(
                    name=name, slug=slug, description=description
                )
                return redirect('/admin-dashboard/?msg=cat_updated')
            except Exception as e:
                error = f'DB_ERROR :: {e}'

    cat = Category.objects.filter(id=cat_id).values(
        'id', 'name', 'slug', 'description'
    ).first()
    if not cat:
        return redirect('/admin-dashboard/')

    return render(request, 'ctf_admin/category_form.html', {
        'action': 'edit', 'error': error, 'cat': cat,
    })


@staff_required
@require_POST
def admin_category_delete(request, cat_id):
    try:
        Category.objects.filter(id=cat_id).delete()
        return redirect('/admin-dashboard/?msg=cat_deleted')
    except Exception:
        return redirect('/admin-dashboard/?msg=cat_delete_error')


# ── Public Auth Views ─────────────────────────────────────────────────────────

def register(request):
    error = None
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username or not email or not password1:
            error = 'ERR :: All fields are required.'
        elif password1 != password2:
            error = 'ERR :: Passwords do not match.'
        elif len(password1) < 6:
            error = 'ERR :: Password must be at least 6 characters.'
        elif BlogUser.objects.filter(username=username).exists():
            error = f'ERR :: Username "{username}" is already taken.'
        elif BlogUser.objects.filter(email=email).exists():
            error = 'ERR :: Email is already registered.'
        else:
            user = BlogUser.objects.create_user(
                username=username, email=email, password=password1, role='user'
            )
            auth_login(request, user)
            return redirect('/')

    return render(request, 'auth/register.html', {'error': error})


@login_required
def user_profile(request):
    user     = request.user
    comments = Comment.objects.filter(author=user).select_related('post').order_by('-created_at')[:10]
    likes    = PostLike.objects.filter(user=user).select_related('post').order_by('-created_at')[:10]
    return render(request, 'auth/profile.html', {
        'profile_user': user,
        'comments':     comments,
        'likes':        likes,
    })


# ── Cloudinary Image Upload ───────────────────────────────────────────────────

@require_POST
def admin_upload_image(request):
    """
    AJAX endpoint: receives a file, uploads to Cloudinary with auto-resize
    and optimization, returns the secure URL.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    file = request.FILES.get('image')
    if not file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    allowed = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    if file.content_type not in allowed:
        return JsonResponse({'error': 'Invalid file type'}, status=400)

    if file.size > 10 * 1024 * 1024:  # 10 MB limit
        return JsonResponse({'error': 'File too large (max 10 MB)'}, status=400)

    try:
        result = cloudinary.uploader.upload(
            file,
            folder='neural_feed',
            transformation=[
                {'width': 1200, 'crop': 'limit'},   # max width 1200px, keep ratio
                {'quality': 'auto:good'},            # auto compress
                {'fetch_format': 'auto'},            # serve webp/avif to modern browsers
            ],
            resource_type='image',
        )
        return JsonResponse({'url': result['secure_url']})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def posts_list(request):
    sort_param    = request.GET.get('sort', 'created_at')
    category_slug = request.GET.get('category', '')
    sql_error     = None
    posts         = []

    try:
        qs = (
            Post.objects
            .filter(status='published')
            .select_related('author', 'category')
        )
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        posts = list(qs.order_by(sort_param))
    except Exception as exc:
        sql_error = str(exc)

    categories = list(Category.objects.order_by('name'))

    return render(request, 'posts_list.html', {
        'posts':           posts,
        'categories':      categories,
        'sort_param':      sort_param,
        'active_category': category_slug,
        'sql_error':       sql_error,
    })
