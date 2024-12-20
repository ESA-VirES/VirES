"""
VirES Oauth development server - instance settings
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
#BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '{{SECRET_KEY}}'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*','127.0.0.1','::1'] # set to specific host in production
USE_X_FORWARDED_HOST = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'vires_oauth',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_countries',
    'oauth2_provider',
]

SOCIALACCOUNT_PROVIDERS = {}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'vires_oauth.middleware.session_idle_timeout',
    'vires_oauth.middleware.access_logging_middleware',
    'vires_oauth.middleware.inactive_user_logout_middleware',
    'vires_oauth.middleware.oauth_user_permissions_middleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.gzip.GZipMiddleware',
]

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of allauth
    'django.contrib.auth.backends.ModelBackend',
    # allauth specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Django oauth2_provider
OAUTH2_PROVIDER = {
    'SCOPES_BACKEND_CLASS': 'vires_oauth.scopes.ViresScopes',
    'ALLOWED_REDIRECT_URI_SCHEMES': ['http'], # change to 'https' in production!
    'PKCE_REQUIRED': False,
}

# Django allauth
SITE_ID = 1 # ID from django.contrib.sites
CSRF_COOKIE_NAME = "oauth:csrftoken"
SESSION_COOKIE_NAME = "oauth:sessionid"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSIONS_IDLE_TIMEOUT = 600
LOGIN_URL = "/oauth/accounts/login/"
LOGIN_REDIRECT_URL = "/oauth"
ACCOUNT_LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
#ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/accounts/vires/login/?process=login"
ACCOUNT_UNIQUE_EMAIL = True
#ACCOUNT_EMAIL_SUBJECT_PREFIX = [vires.services]
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'
ACCOUNT_PASSWORD_MIN_LENGTH = 8
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_USERNAME_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_EMAIL_REQUIRED = True
#SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_EMAIL_VERIFICATION = ACCOUNT_EMAIL_VERIFICATION
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_LOGIN_ON_GET = False
ACCOUNT_SIGNUP_FORM_CLASS = 'vires_oauth.forms.SignupForm'
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = True

VIRES_OAUTH_DEFAULT_GROUPS = ["default", "swarm_vre"]
VIRES_SERVICE_TERMS_VERSION = "2019-11-12V2.0.0"

VIRES_APPS = [
    app for app in [
        {
            "name": "VirES for Swarm",
            "required_permission": "swarm",
            "url": "/accounts/vires/login/?process=login",
        },
        {
            "name": "VRE (JupyterLab)",
            "required_permission": "swarm_vre",
            "url": None
        },
    ] if app["url"]
]

ROOT_URLCONF = 'oauth.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'vires_oauth.context_processors.vires_oauth',
            ],
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = 'oauth.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '{{DBNAME}}',
        'USER': '{{DBUSER}}',
        'PASSWORD': '{{DBPASSWD}}',
        'HOST': '::1',
        'PORT': '5432',
    }
}


# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False, # Set False to preserve Gunicorn access logging.
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s.%(msecs)03d %(name)s %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
        },
        'access': {
            'format': '%(asctime)s.%(msecs)03d %(remote_addr)s %(username)s %(name)s %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
        },
    },
    'handlers': {
        'oauth_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '{{INSTANCE_LOG}}',
            'formatter': 'default',
            'filters': [],
        },
        'access_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '{{ACCESS_LOG}}',
            'formatter': 'access',
            'filters': [],
        },
        'stderr_stream': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'filters': [],
        },
    },
    'loggers': {
        'vires_oauth': {
            'handlers': ['oauth_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'access': {
            'handlers': ['access_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        '': {
            'handlers': ['oauth_file'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
}


# Static file
STATIC_ROOT = '/srv/vires/oauth_static'
STATIC_URL = '/oauth_static/'
