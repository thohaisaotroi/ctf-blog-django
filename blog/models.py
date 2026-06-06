from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class BlogUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Inherits: username, email, password (hashed), first_name, last_name,
              is_active, is_staff, is_superuser, date_joined, last_login.
    Adds: role (admin / user) for admin panel access control.
    """
    role = models.CharField(max_length=10, default='user')

    class Meta:
        db_table = 'blog_user'

    def __str__(self):
        return self.username


class Category(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'blog_category'

    def __str__(self):
        return self.name


STATUS_CHOICES = [
    ('published', 'Published'),
    ('draft',     'Draft'),
    ('private',   'Private'),
]


class Post(models.Model):
    title        = models.CharField(max_length=255)
    slug         = models.SlugField(max_length=255, unique=True)
    content      = models.TextField()
    excerpt      = models.TextField(blank=True)
    author       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='author_id')
    category     = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_id')
    is_published = models.BooleanField(default=True)
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published')
    views        = models.IntegerField(default=0)
    likes        = models.IntegerField(default=0)
    secret_flag  = models.CharField(max_length=100, blank=True, null=True)
    cover_image  = models.CharField(max_length=500, blank=True, null=True)
    created_at   = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'blog_post'

    def __str__(self):
        return self.title


class Comment(models.Model):
    post        = models.ForeignKey(Post, on_delete=models.CASCADE, db_column='post_id')
    # Link to registered user (null = legacy / anonymous comment)
    author      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='comments',
    )
    parent      = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True, default=None,
        related_name='replies',
        db_column='parent_id',
    )
    author_name = models.CharField(max_length=100)   # auto-filled from user.username
    content     = models.TextField()
    created_at  = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'blog_comment'

    def __str__(self):
        return f'{self.author_name} on {self.post_id}'


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        db_table = 'blog_tag'

    def __str__(self):
        return self.name


class PostTag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, db_column='post_id')
    tag  = models.ForeignKey(Tag,  on_delete=models.CASCADE, db_column='tag_id')

    class Meta:
        db_table = 'blog_post_tag'
        unique_together = [['post', 'tag']]


class PostLike(models.Model):
    """Tracks per-user likes — replaces session-based deduplication."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='liked_posts',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_postlike'
        unique_together = [['post', 'user']]


class NewsletterSubscriber(models.Model):
    email         = models.EmailField(unique=True)
    name          = models.CharField(max_length=100, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_subscriber'

    def __str__(self):
        return self.email
