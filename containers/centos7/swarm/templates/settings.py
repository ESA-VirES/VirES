# VirES for Swarm development server settings
from os.path import join, abspath, dirname

PROJECT_DIR = dirname(abspath(__file__))

DEBUG = True

MANAGERS = ADMINS = ()

HAPI_ABOUT = {
  'id': 'VirES-dev',
  'contact': 'feedback@vires.services',
  'description': 'Web API for the ESA Swarm mission products.',
}

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': '{{DBNAME}}',
        'USER': '{{DBUSER}}',
        'PASSWORD': '{{DBPASSWD}}',
        'HOST': '::1',
        'PORT': '5432',
    }
}

SITE_ID = 1
ALLOWED_HOSTS = ['*', '127.0.0.1', '::1']
USE_X_FORWARDED_HOST = True

LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True

TIME_ZONE = 'UTC'
USE_TZ = True
MEDIA_ROOT = ''
MEDIA_URL = ''

STATIC_ROOT = '/srv/vires/swarm_static'
STATIC_URL = '/swarm_static/'

STATICFILES_DIRS = []

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

SECRET_KEY = '{{SECRET_KEY}}'

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'swarm.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'swarm.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            join(PROJECT_DIR, 'templates'),
        ],
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
            ],
        }
    }
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.gis',
    'django.contrib.staticfiles',
    'vires',
]

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
        'vires_file': {
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
        'eoxserver': {
            'handlers': ['vires_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'vires': {
            'handlers': ['vires_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'vires_sync': {
            'handlers': ['vires_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'eoxs_wps_async': {
            'handlers': ['vires_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'access': {
            'handlers': ['access_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        '': {
            'handlers': ['vires_file'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
}

EOXS_SERVICE_HANDLERS = [
    'vires.ows.wms.getmap_v11.WMS11GetMapHandler',
    'vires.ows.wms.getmap_v13.WMS13GetMapHandler',
    'eoxserver.services.ows.wps.v10.getcapabilities.WPS10GetCapabilitiesHandler',
    'eoxserver.services.ows.wps.v10.describeprocess.WPS10DescribeProcessHandler',
    'eoxserver.services.ows.wps.v10.execute.WPS10ExecuteHandler',
]

EOXS_PROCESSES = [
    'vires.processes.get_time_data.GetTimeDataProcess',
    'vires.processes.get_model_info.GetModelInfo',
    'vires.processes.get_collection_info.GetCollectionInfo',
    'vires.processes.get_indices.GetIndices',
    'vires.processes.get_orbit_timerange.GetOrbitTimeRange',
    'vires.processes.get_observatories.GetObservatories',
    'vires.processes.get_conjunctions.GetConjunctions',
    'vires.processes.eval_model.EvalModel',
    'vires.processes.retrieve_continuous_segments.RetrieveContinuousSegments',
    'vires.processes.retrieve_bubble_index.RetrieveBubbleIndex',
    'vires.processes.fetch_data.FetchData',
    'vires.processes.fetch_filtered_data.FetchFilteredData',
    'vires.processes.fetch_filtered_data_async.FetchFilteredDataAsync',
    'vires.processes.fetch_fieldlines.FetchFieldlines',
    'vires.processes.list_jobs.ListJobs',
    'vires.processes.remove_job.RemoveJob',
]

EOXS_ASYNC_BACKENDS = [
    'eoxs_wps_async.backend.WPSAsyncBackendBase',
]

VIRES_UPLOAD_DIR = "{{VIRES_UPLOAD_DIR}}"
VIRES_CACHE_DIR = "{{VIRES_PRODUCT_CACHE_DIR}}"
VIRES_MODEL_CACHE_DIR = "{{VIRES_MODEL_CACHE_DIR}}"
VIRES_MODEL_CACHE_READ_ONLY = False


# Django-Allauth settings

INSTALLED_APPS += [
    'eoxs_allauth',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'eoxs_allauth.vires_oauth', # VirES-OAuth2 "social account provider"
    'django_countries',
]

SOCIALACCOUNT_PROVIDERS = {
    'vires': {
        'SERVER_URL': '/oauth/',
        'DIRECT_SERVER_URL': 'http://[::1]:80/oauth',
        'SCOPE': ['read_id', 'read_permissions'],
        'PERMISSION': 'swarm',
    },
}

MIDDLEWARE += [
    'eoxs_allauth.middleware.inactive_user_logout_middleware',
    'eoxs_allauth.middleware.access_logging_middleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.gzip.GZipMiddleware',
]

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of allauth
    'django.contrib.auth.backends.ModelBackend',
    # allauth specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Django allauth
SITE_ID = 1 # ID from django.contrib.sites
VIRES_VRE_JHUB_PERMISSION = "swarm_vre"
VIRES_VRE_JHUB_URL = None
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/vires/login/"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = False
SOCIALACCOUNT_LOGIN_ON_GET = False
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

TEMPLATES[0]['OPTIONS']['context_processors'] = [
    # Required by allauth template tags
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'eoxs_allauth.vires_oauth.context_processors.vires_oauth',
    'eoxs_allauth.context_processors.vre_jhub', # required by VRE/JupyterHub integration
]

# VirES-Server AllAuth settings
WORKSPACE_TEMPLATE="vires/workspace.html"
OWS11_EXCEPTION_XSL = join(STATIC_URL, "other/owserrorstyle.xsl")

LOGGING['loggers'].update({
    'eoxs_allauth': {
        'handlers': ['vires_file'],
        'level': 'DEBUG' if DEBUG else 'INFO',
        'propagate': False,
    },
})
