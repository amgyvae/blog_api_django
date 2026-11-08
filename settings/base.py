from django.urls import reverse_lazy
from .conf import BASE_DIR, config

# Secret key
SECRET_KEY = config("BLOG_SECRET_KEY")

# Django Installed apps
DJANGO_AND_THIRD_PARTY_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
]

PROJECT_APPS = [
    'apps.auths',
    'apps.blog',
]

INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        }
    }
]

# wsgi and asgi
WSGI_APPLICATION = "settings.wsgi.application"
ASGI_APPLICATION = "settings.asgi.application"

# auth user model
AUTH_USER_MODEL = "auths.User"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Unfolg
UNFOLD = {
    "SITE_TITLE": "Blog API Admin",
    "SITE_HEADER": "Blog API Management",
    "SITE_SUBHEADER": "Administration & Content Management",
    "SITE_SYMBOL": "feed",
    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",
    "DASHBOARD_CALLBACK": "apps.blog.callbacks.dashboard_callback",
    "SITE_DROPDOWN": [
        {
            "icon": "code",
            "title": "GitHub Repository",
            "link": "https://github.com/amgyvae/blog_api_django",
        },
        {
            "icon": "menu_book",
            "title": "Unfold Docs",
            "link": "https://unfoldadmin.com/docs/",
        },
    ],
    "COLORS": {
        "primary": {
            "50": "240 249 255",
            "100": "224 242 254",
            "200": "186 230 253",
            "300": "125 211 252",
            "400": "56 189 248",
            "500": "14 165 233",
            "600": "2 132 199",
            "700": "3 105 161",
            "800": "7 89 133",
            "900": "12 74 110",
            "950": "8 47 73",
        },
    },
    "COMMAND": {
        "search_fields": {
            "auths.User": ["email", "first_name", "last_name"],
            "blog.Post": ["title", "body"],
            "blog.Category": ["name"],
            "blog.Tag": ["name"],
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Overview",
                "separator": False,
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Content",
                "separator": True,
                "items": [
                    {
                        "title": "Posts",
                        "icon": "article",
                        "link": reverse_lazy("admin:blog_post_changelist"),
                        "badge": "apps.blog.callbacks.drafts_badge",
                    },
                    {
                        "title": "Comments",
                        "icon": "chat",
                        "link": reverse_lazy("admin:blog_comment_changelist"),
                    },
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": reverse_lazy("admin:blog_category_changelist"),
                    },
                    {
                        "title": "Tags",
                        "icon": "label",
                        "link": reverse_lazy("admin:blog_tag_changelist"),
                    },
                ],
            },
            {
                "title": "Users & Access",
                "separator": True,
                "permission": lambda request: request.user.is_superuser,
                "items": [
                    {
                        "title": "Users",
                        "icon": "group",
                        "link": reverse_lazy("admin:auths_user_changelist"),
                    },
                    {
                        "title": "Groups",
                        "icon": "lock",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": ["blog.post"],
            "items": [
                {
                    "title": "All",
                    "link": reverse_lazy("admin:blog_post_changelist"),
                },
                {
                    "title": "Published",
                    "link": lambda request: f"{reverse_lazy('admin:blog_post_changelist')}?status__exact=published",
                },
                {
                    "title": "Drafts",
                    "link": lambda request: f"{reverse_lazy('admin:blog_post_changelist')}?status__exact=draft",
                },
            ],
        },
    ],
}