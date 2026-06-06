import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'ctf-lab-dev-secret-key-not-for-production')

DEBUG = True

ALLOWED_HOSTS = ['*']

# ── Custom user model ─────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'blog.BlogUser'

INSTALLED_APPS = [
    # jazzmin MUST come before django.contrib.admin
    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'blog.waf_middleware.SimpleWAFMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ctf_blog.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ctf_blog.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'ctf_blog'),
        'USER': os.environ.get('DB_USER', 'ctf_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'ctf_pass'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ── Auth redirects ────────────────────────────────────────────────────────────
LOGIN_URL          = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ── Email (password reset) ────────────────────────────────────────────────────
EMAIL_BACKEND       = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', 'vutiendat0302@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'sxcx zost ldqp pdbh')
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', 'NEURAL_FEED <vutiendat0302@gmail.com>')

# ── Cloudinary ────────────────────────────────────────────────────────────────
import cloudinary
cloudinary.config(
    cloud_name  = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dlpsakhdd'),
    api_key     = os.environ.get('CLOUDINARY_API_KEY',    '989734166586527'),
    api_secret  = os.environ.get('CLOUDINARY_API_SECRET', 'G20A1XVDRDF7cWECLyqEpmYGeF0'),
    secure      = True,
)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_PASSWORD_VALIDATORS = []

# ── Jazzmin — Cyberpunk Dark Admin Theme ─────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title":        "NEURAL_FEED",
    "site_header":       "NEURAL_FEED",
    "site_brand":        "NEURAL_FEED",
    "site_logo":         None,
    "welcome_sign":      "[ ADMIN_PORTAL :: NEURAL_FEED ]",
    "copyright":         "NEURAL_FEED 2035",
    "search_model":      ["blog.Post", "blog.BlogUser"],
    "topmenu_links": [
        {"name": "🌐 View Site",      "url": "/",                      "new_window": True},
        {"name": "📝 Posts",           "url": "/manage/blog/post/"},
        {"name": "👥 Users",           "url": "/manage/blog/bloguser/"},
        {"name": "📂 Categories",      "url": "/manage/blog/category/"},
        {"name": "📊 Dashboard",        "url": "/admin-dashboard/",      "new_window": True},
    ],
    "usermenu_links": [
        {"name": "View Site", "url": "/", "new_window": True},
    ],
    "show_sidebar":           True,
    "navigation_expanded":    True,
    "hide_apps":              [],
    "hide_models":            [],
    "order_with_respect_to": ["blog", "blog.Post", "blog.Category", "blog.BlogUser", "blog.Comment", "blog.Tag"],
    "icons": {
        "auth":             "fas fa-users-cog",
        "auth.user":        "fas fa-user",
        "auth.Group":       "fas fa-users",
        "blog.Post":        "fas fa-file-alt",
        "blog.BlogUser":    "fas fa-user-secret",
        "blog.Category":    "fas fa-folder",
        "blog.Comment":     "fas fa-comments",
        "blog.Tag":         "fas fa-tags",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active":  True,
    "custom_css":            None,
    "custom_js":             None,
    "use_google_fonts_cdn":  True,
    "show_ui_builder":       False,
    "changeform_format":     "horizontal_tabs",
    "language_chooser":      False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text":     False,
    "footer_small_text":     False,
    "body_small_text":       False,
    "brand_small_text":      False,
    "brand_colour":          "navbar-success",
    "accent":                "accent-teal",
    "navbar":                "navbar-dark",
    "no_navbar_border":      True,
    "navbar_fixed":          True,
    "layout_boxed":          False,
    "footer_fixed":          False,
    "sidebar_fixed":         True,
    "sidebar":               "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme":                 "cyborg",      # Bootswatch: darkly / cyborg / slate / superhero
    "dark_mode_theme":       "cyborg",
    "button_classes": {
        "primary":   "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info":      "btn-outline-info",
        "warning":   "btn-outline-warning",
        "danger":    "btn-outline-danger",
        "success":   "btn-outline-success",
    },
}
