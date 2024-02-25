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
from pathlib import Path

import boto3
import redis
from core.keygen import get_key
from dotenv import load_dotenv

load_dotenv()

# bots settings
DOMAIN = os.getenv('DOMAIN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_BOT_NAME = os.getenv('TELEGRAM_BOT_NAME')
OW_API_TOKEN = os.getenv('OW_API_TOKEN', default='some_token_to_pass_test')
YANDEX_GEO_API_TOKEN = os.getenv('YANDEX_GEO_API_TOKEN', default='some_token_to_pass_test')

CHAT_GPT_TOKEN = os.getenv('CHAT_GPT_TOKEN')
TELEGRAM_ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')
SOCKS5 = os.getenv('SOCKS5')

# mail service
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = 587

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    SECRET_KEY = get_key(50)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.getenv('DEBUG', default=0))

# HOSTS
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', default='localhost').split(' ')

USE_X_FORWARDED_HOST = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = (f'https://*.{DOMAIN}',)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_FAILURE_VIEW = 'core.views.csrf_failure'

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
]

THIRD_PARTY_APPS = [
    'defender',
    'dbbackup',
    'sorl.thumbnail',
    'django_celery_beat',
    'debug_toolbar',
    'django_user_agents',
    'django_ckeditor_5',
    'treebeard',
    'storages',
]

PROJECT_APPS = [
    'core.apps.CoreConfig',
    'users.apps.UsersConfig',
    'tasks.apps.TasksConfig',
    'telbot.apps.TelbotConfig',
    'posts.apps.PostsConfig',
    'ai.apps.AiConfig',
    'advertising.apps.AdvertisingConfig',
    'stats.apps.StatsConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

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
TEMPLATES_DIR = Path(BASE_DIR).joinpath('templates').resolve()
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

DATABASES = {
    'default': {
        'ENGINE': os.getenv('POSTGRES_ENGINE'),
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT'),
    }
}

# django-dbbackup
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

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_USE_SSL = int(os.getenv('AWS_S3_USE_SSL', default=0))
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

STATIC_BUCKET_NAME = 'todo-static'
MEDIA_BUCKET_NAME = 'todo-media'
CKEDITOR_BUCKET_NAME = 'todo-ckeditor'
DATABASE_BUCKET_NAME = 'todo-database'

USE_S3 = int(os.getenv('USE_S3', default=0))

if USE_S3:
    STATIC_URL = f'{AWS_S3_ENDPOINT_URL}/{STATIC_BUCKET_NAME}/'
    STATICFILES_STORAGE = 'todo.storages.StaticStorage'

    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{MEDIA_BUCKET_NAME}/'
    DEFAULT_FILE_STORAGE = 'todo.storages.MediaStorage'
    CKEDITOR_5_FILE_STORAGE = 'todo.storages.CkeditorCustomStorage'

    DBBACKUP_STORAGE = 'todo.storages.DataBaseStorage'
    DBBACKUP_STORAGE_OPTIONS = {
        'access_key': AWS_ACCESS_KEY_ID,
        'secret_key': AWS_SECRET_ACCESS_KEY,
        'bucket_name': DATABASE_BUCKET_NAME,
        'default_acl': 'private',
    }
else:
    STATIC_URL = '/static/'

    MEDIA_URL = '/media/'
    MEDIA_ROOT = Path(BASE_DIR).joinpath('media').resolve()

    DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
    DBBACKUP_STORAGE_OPTIONS = {
        'location': Path(BASE_DIR).joinpath('backup').resolve()
    }

STATICFILES_DIRS = (BASE_DIR / 'static',)
STATIC_ROOT = Path(BASE_DIR).joinpath('staticfiles').resolve()

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

S3_CLIENT = boto3.client(
    's3',
    use_ssl=AWS_S3_USE_SSL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=AWS_S3_ENDPOINT_URL
)

# Django-ckeditor
CustomColorPalette = [
    {
        'color': 'hsl(4, 90%, 58%)',
        'label': 'Red'
    },
    {
        'color': 'hsl(340, 82%, 52%)',
        'label': 'Pink'
    },
    {
        'color': 'hsl(291, 64%, 42%)',
        'label': 'Purple'
    },
    {
        'color': 'hsl(262, 52%, 47%)',
        'label': 'Deep Purple'
    },
    {
        'color': 'hsl(231, 48%, 48%)',
        'label': 'Indigo'
    },
    {
        'color': 'hsl(207, 90%, 54%)',
        'label': 'Blue'
    },
]

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'link',
                    'bulletedList', 'numberedList', 'blockQuote', 'imageUpload', ],
    },
    'extends': {
        'blockToolbar': [
            'paragraph', 'heading1', 'heading2', 'heading3',
            '|',
            'bulletedList', 'numberedList',
            '|',
            'blockQuote',
        ],
        'toolbar': ['heading', '|', 'outdent', 'indent', '|', 'bold', 'italic', 'link', 'underline', 'strikethrough',
                    'code', 'subscript', 'superscript', 'highlight', '|', 'codeBlock', 'sourceEditing', 'insertImage',
                    'bulletedList', 'numberedList', 'todoList', '|', 'blockQuote', '|',
                    'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 'mediaEmbed', 'removeFormat',
                    'insertTable', ],
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft',
                        'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side', '|'],
            'styles': [
                'full',
                'side',
                'alignLeft',
                'alignRight',
                'alignCenter',
            ]

        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells',
                               'tableProperties', 'tableCellProperties'],
            'tableProperties': {
                'borderColors': CustomColorPalette,
                'backgroundColors': CustomColorPalette
            },
            'tableCellProperties': {
                'borderColors': CustomColorPalette,
                'backgroundColors': CustomColorPalette
            }
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading4', 'view': 'h4', 'title': 'Heading 4', 'class': 'ck-heading_heading4'}
            ]
        },
    },
    'list': {
        'properties': {
            'styles': 'true',
            'startIndex': 'true',
            'reversed': 'true',
        }
    }
}

# Setting for working with Jupiter
if DEBUG:
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = ([ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"])

# REDIS
# https://python-scripts.com/redis
# https://redis.io/docs/
# CELERY
# https://django.fun/ru/docs/celery/5.1/getting-started/introduction/

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

IS_TEST = int(os.getenv('IS_TEST', default=0))

if IS_TEST:
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
    REDIS_CLIENT_DATA = {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'db': 0,
    }
else:
    REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'
    REDIS_CLIENT_DATA = {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'db': 0,
        'password': REDIS_PASSWORD
    }

REDIS_CLIENT = redis.StrictRedis(**REDIS_CLIENT_DATA)

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_DEFAULT_QUEUE = 'default'

# CELERY BEAT
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# CACHE BACKEND
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# USER AGENTS PARSING
# Cache backend is optional, but recommended to speed up user agent parsing
# Name of cache backend to cache user agents. If it not specified default
# cache alias will be used. Set to `None` to disable caching.
# https://pypi.org/project/django-user-agents/
USER_AGENTS_CACHE = 'default'


#  DJANGO-DEFENDER
# https://django-defender.readthedocs.io/en/latest/#
DEFENDER_REDIS_URL = REDIS_URL
DEFENDER_LOCKOUT_URL = 'block'
DEFENDER_COOLOFF_TIME = 600


if DEBUG:
    # Celery debugger
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_TASK_IGNORE_RESULT = True


EXTRA_LOGGING = int(os.getenv('EXTRA_LOGGING', default=0))
if EXTRA_LOGGING:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            }
        },
        'formatters': {
            'console': {
                'format': '[%(levelname)s: %(asctime)s] %(name)s.%(funcName)s:%(lineno)s- %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'console',
            },
            'django.server': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'console',
            },
            'django.request': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'console',
            },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler',
                'formatter': 'console',
            },
        },
        'loggers': {
            '': {
                'handlers': ['console', 'mail_admins', 'django.request'],
                'level': 'DEBUG' if DEBUG else 'INFO',
            },
            'django.server': {
                'handlers': ['django.server'],
                'propagate': False,
            },
        },
    }
