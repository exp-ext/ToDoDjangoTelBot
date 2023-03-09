"""
Django settings for todo project.

Generated by 'django-admin startproject' using Django 4.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
import socket
from pathlib import Path, PurePath

import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.django import DjangoIntegration

load_dotenv()

# bots settings
TOKEN = os.getenv('TOKEN')
OW_API_ID = os.getenv('OW_API_ID')
YANDEX_GEO_API = os.getenv('YANDEX_GEO_API')
DOMEN = os.getenv('DOMEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# mail service
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = 587

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

WEB_DIR = f'{BASE_DIR.resolve().parent}/web/'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.environ.get('DEBUG', default=0))

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(" ")

SENTRY_KEY = os.getenv('SENTRY_KEY')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    # login defender
    'defender',
    # backup db & media
    'dbbackup',
    # images
    'sorl.thumbnail',
    # celery
    'django_celery_beat',
    # debugger
    'debug_toolbar',
    # user agents parser
    'django_user_agents',
    # WYSIWYG editor
    'ckeditor_uploader',
    'ckeditor',
    # my app
    'core.apps.CoreConfig',
    'users.apps.UsersConfig',
    'tasks.apps.TasksConfig',
    'telbot.apps.TelbotConfig',
    'posts.apps.PostsConfig',
]

MIDDLEWARE = [
    # django
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # Authentication
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # login defender
    'defender.middleware.FailedLoginMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # user agents parser
    'django_user_agents.middleware.UserAgentMiddleware',
    # debug_toolbar
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'todo.urls'
TEMPLATES_DIR = os.fspath(PurePath(BASE_DIR, 'templates'))
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'todo.wsgi.application'
ASGI_APPLICATION = 'todo.asgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

SQLITE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'TIME_ZONE': 'UTC',
    }
}

POSTGRES = {
    'default': {
        'ENGINE': os.environ.get('POSTGRES_ENGINE'),
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT'),
    }
}

DATABASES = SQLITE if DEBUG else POSTGRES

# django-dbbackup
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {
    'location': os.fspath(PurePath(WEB_DIR, 'backup')),
}

DBBACKUP_CONNECTORS = {
    'default': {
        'CONNECTOR': 'dbbackup.db.postgresql.PgDumpBinaryConnector',
    }
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Password validation and security
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'users.User'

CSRF_FAILURE_VIEW = 'core.views.csrf_failure'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# LOGOUT_REDIRECT_URL = 'index'
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'index'

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Для корректной работы виджета в форме профиля
USE_L10N = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

STATIC_URL = '/static/'

STATIC_DIR = os.fspath(PurePath(BASE_DIR, 'static'))

if DEBUG:
    STATICFILES_DIRS = (STATIC_DIR,)
else:
    STATIC_ROOT = STATIC_DIR

# MEDIA
MEDIA_URL = '/media/'

MEDIA_ROOT = os.fspath(PurePath(WEB_DIR, 'media'))

# Django-ckeditor
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_BASEPATH = f'{STATIC_DIR}/ckeditor/ckeditor/'

# Setting for working with Jupiter
if DEBUG:
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = ([ip[: ip.rfind(".")] + ".1" for ip in ips]
                    + ["127.0.0.1", "10.0.2.2"])

# REDIS
# https://python-scripts.com/redis
# https://redis.io/docs/
# CELERY
# https://django.fun/ru/docs/celery/5.1/getting-started/introduction/
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379')
BROKER_URL = REDIS_URL
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_DEFAULT_QUEUE = 'default'

# CELERY BEAT
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# CACHE BACKEND
REDISCACHE = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_URL}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

LOCMEMCACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

CACHES = LOCMEMCACHE if DEBUG else REDISCACHE

# USER AGENTS PARSING
# Cache backend is optional, but recommended to speed up user agent parsing
# Name of cache backend to cache user agents. If it not specified default
# cache alias will be used. Set to `None` to disable caching.
# https://pypi.org/project/django-user-agents/
USER_AGENTS_CACHE = 'default'


#  DJANGO-DEFENDER
# https://django-defender.readthedocs.io/en/latest/#
DEFENDER_REDIS_URL = None if DEBUG else REDIS_URL
DEFENDER_LOCKOUT_URL = 'block'
DEFENDER_COOLOFF_TIME = 600

# SENTRY MONITORING
sentry_sdk.init(
    dsn=f'https://{SENTRY_KEY}',
    integrations=(DjangoIntegration(),),

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)
