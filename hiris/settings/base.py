"""
Django settings for hiris project.

Generated by 'django-admin startproject' using Django 4.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/

For inspiration look at:
https://djangostars.com/blog/category/python-django/
https://djangostars.com/blog/configuring-django-settings-best-practices/

"""
import os,sys
import environ
from pathlib import Path
from django.conf.urls.static import static

# For UW_SAML
from django.urls import reverse_lazy


# Build paths inside the project like this: BASE_DIR / 'subdir'.

# BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = Path(__file__).resolve().parent.parent

#print(BASE_DIR, PROJECT_DIR)

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

environ.Env.read_env()  # reading .env file
# Take environment variables from .env file
environ.Env.read_env(os.path.join(PROJECT_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
# False if not in os.environ because of casting above
DEBUG = env('DEBUG')

# SECURITY WARNING: keep the secret key used in production secret!
# Raises Django's ImproperlyConfigured
# exception if SECRET_KEY not in os.environ

SECRET_KEY = env('SECRET_KEY')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS').split(" ")
# ALLOWED_HOSTS = []
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # tools
    'django_extensions',
    # 'uw_saml'

    # HIRIS apps
    'hiris.apps.core',
]

AUTHENTICATION_BACKENDS = [
    # For UW_SAML
    'django.contrib.auth.backends.RemoteUserBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # For UW_SAML
    'django.contrib.auth.middleware.PersistentRemoteUserMiddleware'
]

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
            ],
        },
    },
]

WSGI_APPLICATION = 'hiris.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_NAME'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
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
    BASE_DIR / 'hiris/assets',
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# For UW_SAML
LOGIN_URL = reverse_lazy('saml_login')

UW_SAML = {
    'strict': False,
    'debug': True,
    'sp': {
        'entityId': 'https://example.uw.edu/saml2',
        'assertionConsumerService': {
            'url': 'https://example.uw.edu/saml/sso',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
        },
        'singleLogoutService': {
            'url': 'https://example.uw.edu/saml/logout',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'NameIDFormat': 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified',
        'x509cert': '',
        # for encrypted saml assertions uncomment and add the private key
        # 'privateKey': '',
    },
    'idp': {
        'entityId': 'urn:mace:incommon:washington.edu',
        'singleSignOnService': {
            'url': 'https://idp.u.washington.edu/idp/profile/SAML2/Redirect/SSO',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'singleLogoutService': {
            'url': 'https://idp.u.washington.edu/idp/logout',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'x509cert': '',
    },
    'security': {
        # for encrypted saml assertions
        # 'wantAssertionsEncrypted': True,
        # for 2FA uncomment this line
        # 'requestedAuthnContext':  ['urn:oasis:names:tc:SAML:2.0:ac:classes:TimeSyncToken']
    }
}