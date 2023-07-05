import os #,sys
import environ
from pathlib import Path
from django.conf.urls.static import static
import logging
import logging.config
from django.utils.log import DEFAULT_LOGGING
from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
env = environ.Env(DEBUG=(int, 0))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
# False if not in os.environ because of casting above
DEBUG = int(env("DEBUG", default=0))

# SECURITY WARNING: keep the secret key used in production secret!
# Raises Django's ImproperlyConfigured
# exception if SECRET_KEY not in os.environ

SECRET_KEY = env('SECRET_KEY')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS').split(" ")

# Manage sso/dual/local login differences
LOGIN_TYPE = env('LOGIN_TYPE')
LOGIN_URL = env('LOGIN_URL')
LOGIN_REDIRECT_URL = "/"
LOGIN_SSO_TITLE = ''
LOGIN_SSO_COLLABORATOR_TITLE = ''

if LOGIN_TYPE == "dual":
    LOGIN_SSO_TITLE = env('LOGIN_SSO_TITLE')
    LOGIN_SSO_COLLABORATOR_TITLE = env('LOGIN_SSO_COLLABORATOR_TITLE')

if LOGIN_TYPE == "sso":
    LOGIN_URL = reverse_lazy('saml_login')

# The ports are only needed to get UW_SAML to not redirect to a bad port on login
if LOGIN_TYPE in ("dual", "sso"):
    WEB_PORT = env("WEB_PORT")
    EXTERNAL_WEB_PORT = env("EXTERNAL_WEB_PORT")
else:
    WEB_PORT = None
    EXTERNAL_WEB_PORT = None

LOGOUT_REDIRECT_URL = "/"

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # tools
    'django_extensions',
    'uw_saml',
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    "guardian",

    # HIRIS apps
    'hiris.apps.core',
    'ml_import_wizard',
    'ml_export_wizard',
]

AUTHENTICATION_BACKENDS = [
    # For UW_SAML
    'django.contrib.auth.backends.RemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]

MIDDLEWARE = list(filter(None, [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.PersistentRemoteUserMiddleware',
    
    "hiris.middleware.AddHTTP_X_FORWARDED_PORTMiddleware" if LOGIN_TYPE in ("dual", "sso") and EXTERNAL_WEB_PORT else None,
]))

ROOT_URLCONF = 'hiris.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ os.path.join(BASE_DIR, 'hiris/templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',
            ],
        },
    },
]

WSGI_APPLICATION = 'hiris.wsgi.application'

CSRF_TRUSTED_ORIGINS = ['http://localhost', 'https://dev.hiris.washington.edu', 'https://idp.u.washington.edu']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_NAME'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': 'db',
        'PORT': 5432,
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    PROJECT_DIR / 'static/',
]
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# STATIC_ROOT = os.path.join(BASE_DIR,"static")

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# adding django debug toolbar
if DEBUG and int(env('DEBUG_TOOLBAR')):
    import socket  # only if you haven't already imported this
    MIDDLEWARE.insert(0,'debug_toolbar.middleware.DebugToolbarMiddleware')
    INSTALLED_APPS += 'debug_toolbar',
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]
    RESULT_CACHE=100


# django restframework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        ['django_filters.rest_framework.DjangoFilterBackend',]

    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 1000,
     'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}


# Set up Logging
LOG_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

LOGLEVEL = env('LOGLEVEL').upper() or 'INFO'

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
       'handlers': ['console', 'requests.log'],
       'level': LOGLEVEL
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} [{asctime}] {pathname}:{lineno} {message}',
            'datefmt' : '%Y-%m-%d %H:%M:%S',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'django.server': DEFAULT_LOGGING['formatters']['django.server'],
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },

        'hiris.log': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR,'hiris.log'),
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'verbose',
        },

        'test.log': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR,'test.log'),
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'verbose',
        },

        'requests.log': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename':  os.path.join(LOG_DIR,'requests.log'),
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'verbose',
        },

        # 'django.server': {
        #     'level':'DEBUG',
        #     'class':'logging.handlers.RotatingFileHandler',
        #     'filename':  os.path.join(LOG_DIR,'requests.log'),
        #     'maxBytes': 1024*1024*5, # 5 MB
        #     'backupCount': 5,
        #     'formatter':'verbose',
        # },

        'django.server': DEFAULT_LOGGING['handlers']['django.server'],
    },
    
    'loggers': {

        # default for all undefined Python modules
        'default': {
            'level': 'WARNING',
            'handlers': ['console', 'hiris.log'],
        },

        # Logging for http requests
        "django.request": {
            'level': LOGLEVEL,
            'handlers': ['console', 'requests.log'],
        },

        # Logging for our apps
        'app': {
            'level': LOGLEVEL,
            'handlers': ['console', 'hiris.log'],
        },

        # Logging for tests
        'test': {
            'level': LOGLEVEL,
            'handlers': ['console', 'test.log'],
        },

        # Default runserver request logging
        'django.server': DEFAULT_LOGGING['loggers']['django.server'],

        #  Logging SQL for DEBUG Begin
        'django.db.backends': {
             'level': 'DEBUG',
             'handlers': ['console'],
         }
    
    },
})


# Crispy Forms Settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

SETTINGS_EXPORT = [
    'LOGIN_TYPE',
    'LOGIN_SSO_TITLE',
    'LOGIN_SSO_COLLABORATOR_TITLE',
]