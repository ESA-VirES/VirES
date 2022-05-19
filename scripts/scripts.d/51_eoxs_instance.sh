#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES-Server instance configuration
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_apache.sh
. `dirname $0`/../lib_python_venv.sh
. `dirname $0`/../lib_vires.sh

info "Configuring VirES-Server instance ... "

activate_venv "$VIRES_VENV_ROOT"

HAPI_SERVER_ID=${HAPI_SERVER_ID:-VirES-dev}

VIRES_PERMISSION=${VIRES_PERMISSION:-swarm}

# Configuration switches - all default to YES
CONFIGURE_VIRES=${CONFIGURE_VIRES:-YES}
CONFIGURE_ALLAUTH=${CONFIGURE_ALLAUTH:-YES}
CONFIGURE_WPSASYNC=${CONFIGURE_WPSASYNC:-YES}

required_variables VIRES_SERVER_HOME
required_variables VIRES_SERVER_HOST VIRES_SERVICE_NAME
required_variables VIRES_SERVER_NPROC VIRES_SERVER_NTHREAD
required_variables VIRES_USER VIRES_GROUP VIRES_INSTALL_USER VIRES_INSTALL_GROUP
required_variables VIRES_LOGDIR VIRES_TMPDIR VIRES_CACHE_DIR
required_variables VIRES_WPS_SERVICE_NAME VIRES_WPS_URL_PATH
required_variables VIRES_WPS_TEMP_DIR VIRES_WPS_PERM_DIR VIRES_WPS_TASK_DIR
required_variables VIRES_WPS_SOCKET VIRES_WPS_NPROC VIRES_WPS_MAX_JOBS
required_variables VIRES_UPLOAD_DIR

set_instance_variables

#required_variables HOSTNAME
required_variables INSTANCE INSTROOT
required_variables FIXTURES_DIR STATIC_DIR
required_variables SETTINGS WSGI_FILE URLS WSGI MNGCMD EOXSCONF
required_variables STATIC_URL_PATH OWS_URL
required_variables VIRESLOG ACCESSLOG
required_variables OAUTH_SERVER_HOST

if [ -z "$DBENGINE" -o -z "$DBNAME" ]
then
    load_db_conf "`dirname $0`/../db_eoxs.conf"
fi
required_variables DBENGINE DBNAME

HTTP_TIMEOUT=600

#-------------------------------------------------------------------------------
# STEP 1: CREATE INSTANCE (if not already present)

info "Creating VirES-Server instance '${INSTANCE}' in '$INSTROOT/$INSTANCE' ..."

# check availability of the EOxServer
#HINT: Does python complain that the apparently installed EOxServer
#      package is not available? First check that the 'eoxserver' tree is
#      readable by anyone. (E.g. in case of read protected home directory when
#      the development setup is used.)
python -c 'import eoxserver' || error "EOxServer does not seem to be installed!"

if [ ! -d "$INSTROOT/$INSTANCE" ]
then
    mkdir -p "$INSTROOT/$INSTANCE"
    eoxserver-instance.py "$INSTANCE" "$INSTROOT/$INSTANCE"
fi

# WPS directories
for DIR in "$VIRES_WPS_TEMP_DIR" "$VIRES_WPS_PERM_DIR" "$VIRES_WPS_TASK_DIR" "`dirname "$VIRES_WPS_SOCKET"`"
do
    if [ ! -d "$DIR" ]
    then
        mkdir -p "$DIR"
        chown -v "$VIRES_USER:$VIRES_GROUP" "$DIR"
        chmod -v 0755 "$DIR"
    fi
done

#-------------------------------------------------------------------------------
# STEP 2-1: INSTANCE CONFIGURATION - common

# if possible extract secret key from the existing settings
[ ! -f "$SETTINGS" ] || SECRET_KEY="`sed -ne 's/^SECRET_KEY\s*=\s*'\''\([^'\'']*\)'\''.*$/\1/p' "$SETTINGS" `"
[ -n "$SECRET_KEY" ] || SECRET_KEY="`python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`"

cat > "$SETTINGS" <<END
# generated by VirES-for-Swarm configuration scrip

from os.path import join, abspath, dirname

DEBUG = False

PROJECT_DIR = dirname(abspath(__file__))
PROJECT_URL_PREFIX = ''

MANAGERS = ADMINS = (
)

HAPI_ABOUT = {
  'id': '$HAPI_SERVER_ID',
  'contact': 'feedback@vires.services',
  'description': 'Web API for the ESA Swarm mission products.',
}

DATABASES = {
    'default': {
        'ENGINE': '$DBENGINE',
        'NAME': '$DBNAME',
        'USER': '$DBUSER',
        'PASSWORD': '$DBPASSWD',
        'HOST': '$DBHOST',
        'PORT': '$DBPORT',
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

STATIC_ROOT = join(PROJECT_DIR, 'static')
STATIC_URL = '$STATIC_URL_PATH/'

STATICFILES_DIRS = []

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

SECRET_KEY = '$SECRET_KEY'

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = '$INSTANCE.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = '$INSTANCE.wsgi.application'

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
            'filename': '${VIRESLOG}',
            'formatter': 'default',
            'filters': [],
        },
        'access_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '${ACCESSLOG}',
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
    'vires.processes.retrieve_field_lines.RetrieveFieldLines',
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

VIRES_UPLOAD_DIR = "$VIRES_UPLOAD_DIR"
VIRES_CACHE_DIR = "$VIRES_CACHE_DIR"

END

ex "$EOXSCONF" <<END
/\[services\.owscommon\]
.,/^\[/g/^\s*[^[]/d
.i
http_service_url=/ows?
.
/\[services\.ows\]
.,/^\[/g/^\s*[^[]/d
.i
update_sequence=`date -u +'%Y%m%dT%H%M%SZ'`
onlineresource=https://vires.services
keywords=ESA, Swarm Mission, Magnetic Field
fees=none
access_constraints=none
name=VirES for Swarm
title=VirES for Swarm
abstract=VirES for Swarm
provider_name=EOX IT Services, GmbH
provider_site=https://eox.at
individual_name=
position_name=
phone_voice=
phone_facsimile=
delivery_point=Thurngasse 8/4
city=Wein
administrative_area=Wien
postal_code=1090
country=AT
electronic_mail_address=office@eox.at
hours_of_service=
contact_instructions=
role=Service provider
.
wq
END

{ ex "$EOXSCONF" || /bin/true ; } <<END
/^# WPSASYNC - BEGIN/,/^# WPSASYNC - END/d
wq
END

ex "$EOXSCONF" <<END
/\[services\.ows\.wps\]/a
# WPSASYNC - BEGIN - Do not edit or remove this line!
path_temp=$VIRES_WPS_TEMP_DIR
path_perm=$VIRES_WPS_PERM_DIR
path_task=$VIRES_WPS_TASK_DIR
url_base=$VIRES_URL_ROOT$VIRES_WPS_URL_PATH
socket_file=$VIRES_WPS_SOCKET
max_queued_jobs=$VIRES_WPS_MAX_JOBS
num_workers=$VIRES_WPS_NPROC
# WPSASYNC - END - Do not edit or remove this line!
.
wq
END

#-------------------------------------------------------------------------------
# STEP 2-2: INSTANCE CONFIGURATION - optional - no authentication

[ "$CONFIGURE_ALLAUTH" != "YES" ] && cat > "$URLS" <<END
from django.urls import include, path, re_path
from eoxserver.services.views import ows
from vires.views import custom_data #, custom_model, client_state
from vires.hapi.urls import urlpatterns as hapi_urlpatterns

urlpatterns = [
    path('ows', ows, name="ows"),
    path('hapi/', include(hapi_urlpatterns)),
    re_path(r'^custom_data/(?P<identifier>[0-9a-f-]{36,36})?$', custom_data),
    #re_path(r'^custom_model/(?P<identifier>[0-9a-f-]{36,36})?$', custom_model),
    #re_path(r'^client_state/(?P<identifier>[0-9a-f-]{36,36})?$', client_state),
]
END

#-------------------------------------------------------------------------------
# STEP 2-3: INSTANCE CONFIGURATION - optional - authentication enabled

[ "$CONFIGURE_ALLAUTH" == "YES" ] && cat > "$URLS" <<END
from django.urls import include, path, re_path
from eoxserver.services.views import ows
from eoxs_allauth.views import wrap_protected_api, wrap_open_api, workspace
from eoxs_allauth.urls import document_urlpatterns
from vires.client_state import parse_client_state
from vires.views import custom_data #, custom_model, client_state
from vires.hapi.urls import urlpatterns as hapi_urlpatterns

urlpatterns = [
    path('', workspace(parse_client_state), name="workspace"),
    path('ows', wrap_protected_api(ows), name="ows"),
    path('hapi/', include(hapi_urlpatterns)),
    path('accounts/', include('eoxs_allauth.urls')),
    re_path(r'^custom_data/(?P<identifier>[0-9a-f-]{36,36})?$', wrap_protected_api(custom_data)),
    #re_path(r'^custom_model/(?P<identifier>[0-9a-f-]{36,36})?$', wrap_protected_api(custom_model)),
    #re_path(r'^client_state/(?P<identifier>[0-9a-f-]{36,36})?$', wrap_protected_api(client_state)),
] + document_urlpatterns
END

[ "$CONFIGURE_ALLAUTH" == "YES" ] && cat >> "$SETTINGS" <<END

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
        'DIRECT_SERVER_URL': 'http://$OAUTH_SERVER_HOST',
        'SCOPE': ['read_id', 'read_permissions'],
        'PERMISSION': '$VIRES_PERMISSION',
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
VIRES_VRE_JHUB_URL = ${VIRES_VRE_JHUB_URL:+"'"}${VIRES_VRE_JHUB_URL:-None}${VIRES_VRE_JHUB_URL:+"'"}
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
END

#-------------------------------------------------------------------------------
# STEP 3: APACHE WEB SERVER INTEGRATION

info "Mapping VirES-Server instance '${INSTANCE}' to URL path '${INSTANCE}' ..."

# locate proper configuration file (see also apache configuration)
{
    locate_apache_conf 80
    locate_apache_conf 443
} | while read CONF
do
    { ex "$CONF" || /bin/true ; } <<END
/EOXS00_BEGIN/,/EOXS00_END/de
/^\s*<\/VirtualHost>/i
    # EOXS00_BEGIN - VirES-Server instance - Do not edit or remove this line!

    # VirES-Server instance configured by the automatic installation script

    # static content
    Alias "$STATIC_URL_PATH" "$STATIC_DIR"
    ProxyPass "$STATIC_URL_PATH" !
    <Directory "$STATIC_DIR">
        Options -MultiViews +FollowSymLinks
        Header set Access-Control-Allow-Origin "*"
    </Directory>

    # favicon redirect
    Alias "/favicon.ico" "$INSTSTAT_DIR/other/favicon/favicon.ico"
    ProxyPass "/favicon.ico" !

    # WPS static content
    Alias "$VIRES_WPS_URL_PATH" "$VIRES_WPS_PERM_DIR"
    ProxyPass "$VIRES_WPS_URL_PATH" !
    <Directory "$VIRES_WPS_PERM_DIR">
        EnableSendfile off
        Options -MultiViews +FollowSymLinks
        Header set Access-Control-Allow-Origin "*"
    </Directory>

    # Heilophysics API
    <Location "/hapi">
        Header unset X-Frame-Options
        Header set Access-Control-Allow-Origin "*"
    </Location>

    ProxyPass "${BASE_URL_PATH:-/}" "http://$VIRES_SERVER_HOST${BASE_URL_PATH:-/}" connectiontimeout=60 timeout=$HTTP_TIMEOUT
    #ProxyPassReverse "${BASE_URL_PATH:-/}" "http://$VIRES_SERVER_HOST${BASE_URL_PATH:-/}"
    #RequestHeader set SCRIPT_NAME "${BASE_URL_PATH:-/}"

    # EOXS00_END - VirES-Server instance - Do not edit or remove this line!
.
wq
END
done

#-------------------------------------------------------------------------------
# STEP 4: setup logfiles

# touch the logfile and set the right permissions
_create_log_file() {
    [ -d "`dirname "$1"`" ] || mkdir -p "`dirname "$1"`"
    touch "$1"
    chown "$VIRES_USER:$VIRES_GROUP" "$1"
    chmod 0664 "$1"
}
_create_log_file "$VIRESLOG"
_create_log_file "$ACCESSLOG"
_create_log_file "$GUNICORN_ACCESS_LOG"
_create_log_file "$GUNICORN_ERROR_LOG"

#setup logrotate configuration
cat >"/etc/logrotate.d/vires_server_${INSTANCE}" <<END
$VIRESLOG {
    copytruncate
    weekly
    minsize 1M
    rotate 560
    compress
    missingok
}
$ACCESSLOG {
    copytruncate
    weekly
    minsize 1M
    rotate 560
    compress
    missingok
}
$GUNICORN_ACCESS_LOG {
    copytruncate
    weekly
    minsize 1M
    rotate 560
    compress
}
$GUNICORN_ERROR_LOG {
    copytruncate
    weekly
    minsize 1M
    rotate 560
    compress
}
END

#-------------------------------------------------------------------------------
# STEP 5: CHANGE OWNERSHIP OF THE CONFIGURATION FILES

info "Changing ownership of $INSTROOT/$INSTANCE to $VIRES_INSTALL_USER"
chown -R "$VIRES_INSTALL_USER:$VIRES_INSTALL_GROUP" "$INSTROOT/$INSTANCE"

#-------------------------------------------------------------------------------
# STEP 6: DJANGO INITIALISATION
info "Initializing VirES-Server instance '${INSTANCE}' ..."

# collect static files
python "$MNGCMD" collectstatic -l --noinput

# setup new database
python "$MNGCMD" migrate --noinput

# initialize product types and collections
python "$MNGCMD" product_type import --default
python "$MNGCMD" product_collection import --default

#-------------------------------------------------------------------------------
# STEP 7: SERVICE SETUP

info "Setting up ${VIRES_SERVICE_NAME}.service"
cat > "/etc/systemd/system/${VIRES_SERVICE_NAME}.service" <<END
[Unit]
Description=VirES-Server instance
After=network.target
Before=httpd.service

[Service]
PIDFile=/run/${VIRES_SERVICE_NAME}.pid
Type=simple
WorkingDirectory=$INSTROOT/$INSTANCE
ExecStart=${VIRES_VENV_ROOT}/bin/gunicorn \\
    --preload \\
    --name ${VIRES_SERVICE_NAME} \\
    --user $VIRES_USER \\
    --group $VIRES_GROUP \\
    --workers $VIRES_SERVER_NPROC \\
    --threads $VIRES_SERVER_NTHREAD \\
    --timeout $HTTP_TIMEOUT \\
    --pid /run/${VIRES_SERVICE_NAME}.pid \\
    --access-logfile $GUNICORN_ACCESS_LOG \\
    --error-logfile $GUNICORN_ERROR_LOG \\
    --capture-output \\
    --bind "$VIRES_SERVER_HOST" \\
    --chdir $INSTROOT/$INSTANCE \\
    ${INSTANCE}.wsgi
ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s TERM \$MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target
END

info "Setting up ${VIRES_WPS_SERVICE_NAME}.service"
cat > "/etc/systemd/system/${VIRES_WPS_SERVICE_NAME}.service" <<END
[Unit]
Description=Asynchronous EOxServer WPS Daemon
After=network.target
Before=httpd.service

[Service]
Type=simple
User=$VIRES_USER
ExecStartPre=/usr/bin/rm -fv $VIRES_WPS_SOCKET
ExecStart=${VIRES_VENV_ROOT}/bin/python -EsOm eoxs_wps_async.daemon ${INSTANCE}.settings $INSTROOT/$INSTANCE

[Install]
WantedBy=multi-user.target
END

systemctl daemon-reload
systemctl enable "${VIRES_SERVICE_NAME}.service"
systemctl enable "${VIRES_WPS_SERVICE_NAME}.service"
