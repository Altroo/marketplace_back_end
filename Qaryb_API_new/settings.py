import os
from datetime import timedelta
from decouple import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ac@k!7n8s#f(dbbv92(ya_!68%tvi=x&o*k5fp72qt+vkua0=f'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    config('API_IP'),
    config('API_DOMAIN'),
]

# ALLOWED_HOSTS = ["*"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.postgres',
    'corsheaders',
    # 'channels',
    'rest_framework',
    'colorfield',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'dj_rest_auth',
    'allauth',
    'allauth.account',
    'dj_rest_auth.registration',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'account.apps.AccountConfig',
    'temp_shop.apps.TempShopConfig',
    'auth_shop.apps.AuthShopConfig',
    'temp_offer.apps.TempOfferConfig',
    'offer.apps.OfferConfig',
    'places.apps.PlacesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

# CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOW_CREDENTIALS = True

CORS_ORIGIN_WHITELIST = [
     'http://localhost:3000',
]

ROOT_URLCONF = 'Qaryb_API_new.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = "Qaryb_API_new.asgi.application"
WSGI_APPLICATION = "Qaryb_API_new.wsgi.application"

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': "django.db.backends.postgresql_psycopg2",
        'NAME': config('QARYB_DB_NAME'),
        'USER': config('QARYB_DB_USER'),
        'PASSWORD': config('QARYB_DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '',
    },
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

AUTH_USER_MODEL = "accounts.CustomUser"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"
# STATIC_ROOT = "static"
STATIC_PATH = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
PRODUCT_IMAGES_BASE_NAME = "/media/shop_products"
IMAGES_ROOT_NAME = "/"

# REST_FRAMEWORK

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
SITE_ID = 1

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ("dj_rest_auth.jwt_auth.JWTAuthentication",),
    'DEFAULT_PERMISSION_CLASSES': ("rest_framework.permissions.IsAuthenticated",),
    'DEFAULT_VERSIONING_CLASS': "rest_framework.versioning.NamespaceVersioning",
    'ALLOWED_VERSIONS': ('1.0.0',),
    'DEFAULT_VERSION': "1.0.0",
    'DEFAULT_PAGINATION_CLASS': "rest_framework.pagination.PageNumberPagination",
    'PAGE_SIZE': 10,
    'DEFAULT_RENDERER_CLASSES': ("rest_framework.renderers.JSONRenderer",),
    'DEFAULT_SCHEMA_CLASS': "rest_framework.schemas.coreapi.AutoSchema",
    'DEFAULT_FILTER_BACKENDS': ("django_filters.rest_framework.DjangoFilterBackend",),
}

REST_USE_JWT = True
JWT_AUTH_RETURN_EXPIRATION = True
JWT_AUTH_COOKIE = 'qaryb-jwt-access'
JWT_AUTH_REFRESH_COOKIE = 'qaryb-jwt-refresh'
REST_AUTH_TOKEN_MODEL = None

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            'style': "{",
        },
        'simple': {
            'format': "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            'style': "{",
        },
    },
    'handlers': {
        'file': {
            'level': "WARNING",
            'class': "logging.FileHandler",
            'filename': os.path.join(BASE_DIR, "logs/debug.log"),
        },
    },
    'loggers': {
        'django': {
            'handlers': ["file"],
            'level': "WARNING",
            'propagate': True,
        },
    },
}

API_URL = config('API_URL')

# Nominatim settings
NOMINATIM_PROTOCOL = config('NOMINATIM_PROTOCOL')
MAP_DOMAIN = config('MAP_DOMAIN')

# SIMPLE_JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365),
}

# Celery, Redis settings
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': "channels_redis.core.RedisChannelLayer",
        'CONFIG': {
            "hosts": ["127.0.0.1", "6379"],
        },
    },
}
CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND')
# Celery Debug localhost
# Doesn't call eta shift
# CELERY_TASK_ALWAYS_EAGER = True

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
# Gmail
EMAIL_HOST_USER = "no-reply@qaryb.com"
EMAIL_HOST_PASSWORD = "24YAqua09"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = "587"

SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'LOCALE_FUNC': lambda request: 'en_US',
        'INIT_PARAMS': {'cookie': False},
        'FIELDS': [
            'id',
            'email',
            'first_name',
            'last_name',
            'middle_name',
            'name',
            'name_format',
            'picture',
            'short_name',
        ],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': True,
        'VERSION': 'v13.0',
        # 'APP': {
        #     'client_id': '326143142278628',
        #     'secret': '0a7e23977e803570152550112950ac1f',
        # },
        'APP': {
            'client_id': '701041004404458',
            'secret': '6892529099e635e5e74a31ea2f8cc00a'
        }
    },
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': '258566616875-3tja0a0j92vd5obg3d9i5ku8veqi18rm.apps.googleusercontent.com',
            'secret': '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',
        },
    }
}
# FB TEST
# 326143142278628
# 0a7e23977e803570152550112950ac1f
# FB REAL
# 426465588803536
# ce3005c5ae846c6487b82e441b548597
SOCIALACCOUNT_ADAPTER = "account.adapters.BaseSocialAccountAdapter"
SOCIALACCOUNT_STORE_TOKENS = True

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"

ACCOUNT_DEFAULT_HTTP_PROTOCOL = config('ACCOUNT_DEFAULT_HTTP_PROTOCOL')
# LOGIN_REDIRECT_URL = "/api/account/home/"
