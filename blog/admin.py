from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import BlogUser, Category, Post, Comment, Tag, PostTag, PostLike, NewsletterSubscriber


# ── BlogUser ──────────────────────────────────────────────────────────────────

@admin.register(BlogUser)
class BlogUserAdmin(UserAdmin):
    list_display  = ('id', 'username', 'email', 'role_badge', 'is_staff', 'date_joined')
    list_filter   = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering      = ('id',)

    fieldsets = UserAdmin.fieldsets + (
        ('Role', {
            'fields': ('role',),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {
            'fields': ('role',),
        }),
    )

    def role_badge(self, obj):
        colour = '#00ff41' if obj.role == 'admin' else '#00d4ff'
        return format_html(
            '<span style="color:{c};font-family:monospace;font-weight:bold">[{}]</span>',
            obj.role.upper(), c=colour,
        )
    role_badge.short_description = 'ROLE'


# ── Category ──────────────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('id', 'name', 'slug', 'description')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering      = ('name',)


# ── Post ──────────────────────────────────────────────────────────────────────

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display   = ('id', 'title', 'author', 'category', 'status_badge',
                      'views', 'likes', 'flag_cell', 'created_at')
    list_filter    = ('status', 'category', 'author')
    search_fields  = ('title', 'content', 'secret_flag')
    ordering       = ('-created_at',)
    readonly_fields = ('created_at', 'views')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'cover_image')
        }),
        ('Taxonomy', {
            'fields': ('author', 'category')
        }),
        ('Visibility', {
            'fields': ('status', 'is_published', 'secret_flag'),
        }),
        ('Stats', {
            'fields': ('views', 'created_at'),
            'classes': ('collapse',),
        }),
    )
    prepopulated_fields = {'slug': ('title',)}

    def status_badge(self, obj):
        colours = {'published': '#00ff41', 'draft': '#ffe600', 'private': '#ff003c'}
        c = colours.get(obj.status, '#888')
        return format_html(
            '<span style="color:{};font-family:monospace">● {}</span>',
            c, obj.status.upper()
        )
    status_badge.short_description = 'STATUS'

    def flag_cell(self, obj):
        if obj.secret_flag:
            return format_html(
                '<code style="color:#ff003c;font-size:12px">{}</code>',
                obj.secret_flag,
            )
        return format_html('<span style="color:#444">—</span>')
    flag_cell.short_description = 'SECRET_FLAG'


# ── Comment ───────────────────────────────────────────────────────────────────

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display   = ('id', 'author_name', 'post', 'content_preview', 'created_at')
    list_filter    = ('post',)
    search_fields  = ('author_name', 'content')
    ordering       = ('-created_at',)
    readonly_fields = ('created_at',)

    def content_preview(self, obj):
        txt = obj.content or ''
        return txt[:80] + '…' if len(txt) > 80 else txt
    content_preview.short_description = 'CONTENT'


# ── Tag ───────────────────────────────────────────────────────────────────────

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# ── PostTag ───────────────────────────────────────────────────────────────────

class PostTagInline(admin.TabularInline):
    model = PostTag
    extra = 1


# ── NewsletterSubscriber ──────────────────────────────────────────────────────

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display  = ('id', 'post', 'user', 'created_at')
    list_filter   = ('post',)
    ordering      = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display   = ('id', 'email', 'name', 'subscribed_at')
    search_fields  = ('email', 'name')
    ordering       = ('-subscribed_at',)
    readonly_fields = ('subscribed_at',)
