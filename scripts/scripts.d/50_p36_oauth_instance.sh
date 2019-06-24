#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: OAuth instance configuration
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_apache.sh
. `dirname $0`/../lib_python3_venv.sh
. `dirname $0`/../lib_oauth.sh

info "Configuring OAuth instance ... "

# number of server processes
OAUTH_SERVER_NPROC=${OAUTH_SERVER_NPROC:-2}

# number of threds per server process
OAUTH_SERVER_NTHREAD=${OAUTH_SERVER_NTHREAD:-2}

DEBUG="True"

activate_venv

required_variables VIRES_USER VIRES_GROUP VIRES_INSTALL_USER VIRES_INSTALL_GROUP
required_variables P3_VENV_ROOT

set_instance_variables

required_variables INSTANCE INSTROOT
required_variables SETTINGS WSGI_FILE URLS WSGI MNGCMD
required_variables STATIC_URL_PATH STATIC_DIR
required_variables OAUTHLOG ACCESSLOG
required_variables OAUTH_SERVER_HOST OAUTH_SERVICE_NAME
required_variables GUNICORN_ACCESS_LOG GUNICORN_ERROR_LOG
required_variables OAUTH_BASE_URL_PATH


if [ -z "$DBENGINE" -o -z "$DBNAME" ]
then
    load_db_conf `dirname $0`/../db_oauth.conf
fi
required_variables DBENGINE DBNAME

#-------------------------------------------------------------------------------
# STEP 1: CREATE INSTANCE (if not already present)

info "Creating OAuth instance '${INSTANCE}' in '$INSTROOT/$INSTANCE' ..."

if [ ! -d "$INSTROOT/$INSTANCE" ]
then
    mkdir -p "$INSTROOT/$INSTANCE"
    django-admin startproject "$INSTANCE" "$INSTROOT/$INSTANCE"
fi

#-------------------------------------------------------------------------------
# STEP 2: SETUP DJANGO DB BACKEND

# clear previous settings
{ ex "$SETTINGS" || /bin/true ; } <<END
g/^PROJECT_DIR\\s*=/d
g/^USE_X_FORWARDED_HOST\\s*=/d
g/^STATIC_ROOT\\s*=/d
wq
END

# enter new settings
{ ex "$SETTINGS" || /bin/true ; } <<END
/BASE_DIR/
i
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
.
g/^DEBUG\s*=/s#\(^DEBUG\s*=\s*\).*#\1$DEBUG#
1,\$s:\(STATIC_URL[	 ]*=[	 ]*\).*:\1'$STATIC_URL_PATH/':
i
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')
.
1,\$s/\(^ALLOWED_HOSTS\s*=\s*\).*/\1['*','127.0.0.1','::1']/
a
USE_X_FORWARDED_HOST = True
.
/^DATABASES\\s*=/
.,/^}$/d
i
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
.
$
/^LOGGING\\s*=/
.,/^}$/d
a
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False, # Set False to preserve Gunicorn access logging.
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        #'request_filter': {
        #    '()': 'django_requestlogging.logging_filters.RequestFilter'
        #},
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
        'server_log_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '${OAUTHLOG}',
            'formatter': 'default',
            'filters': [],
        },
        #'access_log_file': {
        #    'level': 'DEBUG',
        #    'class': 'logging.handlers.WatchedFileHandler',
        #    'filename': '${ACCESSLOG}',
        #    'formatter': 'access',
        #    'filters': ['request_filter'],
        #},
        'stderr_stream': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'filters': [],
        },
    },
    'loggers': {
        #'access': {
        #    'handlers': ['access_file'],
        #    'level': 'DEBUG' if DEBUG else 'INFO',
        #    'propagate': False,
        #},
        '': {
            'handlers': ['server_log_file'],
            #'level': 'INFO' if DEBUG else 'WARNING',
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}
.
/^TEMPLATES = \\[/
.,/^]/d
i
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
            ],
            'debug': DEBUG,
        },
    },
]
.
wq
END

# Remove original url patterns
{ ex "$URLS" || /bin/true ; } <<END
/^urlpatterns = \\[/,/^]/s/^\\s\\+/&# /
wq
END

# create fixtures directory
#mkdir -p "$FIXTURES_DIR"

#-------------------------------------------------------------------------------
# STEP 4: APACHE WEB SERVER INTEGRATION

#info "Mapping OAuth server instance '${INSTANCE}' to URL path '${INSTANCE}' ..."

# locate proper configuration file (see also apache configuration)
{
    locate_apache_conf 80
    locate_apache_conf 443
} | while read CONF
do
    { ex "$CONF" || /bin/true ; } <<END
/OAUTH_BEGIN/,/OAUTH_END/de
/^[ 	]*<\/VirtualHost>/i
    # OAUTH_BEGIN - OAuth server instance - Do not edit or remove this line!
    # OAuth server instance configured by the automatic installation script

    <Location "$OAUTH_BASE_URL_PATH">
        ProxyPass "http://$OAUTH_SERVER_HOST$OAUTH_BASE_URL_PATH"
        #ProxyPassReverse "http://$OAUTH_SERVER_HOST$OAUTH_BASE_URL_PATH"
        RequestHeader set SCRIPT_NAME "$OAUTH_BASE_URL_PATH"
    </Location>

    # static content
    Alias "$STATIC_URL_PATH" "$STATIC_DIR"
    <Directory "$STATIC_DIR">
        Options -MultiViews +FollowSymLinks
        Header set Access-Control-Allow-Origin "*"
    </Directory>

    # OAUTH_END - OAuth server instance - Do not edit or remove this line!
.
wq
END
done

#-------------------------------------------------------------------------------
# STEP 6: APPLICATION SPECIFIC SETTINGS

info "Application specific configuration ..."

# remove any previous configuration blocks
{ ex "$URLS" || /bin/true ; } <<END
/^# OAUTH URLS - BEGIN/,/^# OAUTH URLS - END/d
wq
END

{ ex "$SETTINGS" || /bin/true ; } <<END
/^# OAUTH APPS - BEGIN/,/^# OAUTH APPS - END/d
/^# OAUTH MIDDLEWARE - BEGIN/,/^# OAUTH MIDDLEWARE - END/d
/^# OAUTH LOGGING - BEGIN/,/^# OAUTH LOGGING - END/d
/^# EMAIL_BACKEND - BEGIN/,/^# EMAIL_BACKEND - END/d
/^# OAUTH TEMPLATES - BEGIN/,/^# OAUTH TEMPLATES - END/d
wq
END

info "OAUTH specific configuration ..."

# extending urls.py
ex "$URLS" <<END
$ a
# OAUTH URLS - BEGIN - Do not edit or remove this line!
from django.urls import include
urlpatterns += [
    path('', include('vires_oauth.urls')),
]
# OAUTH URLS - END - Do not edit or remove this line!
.
wq
END


# extending settings.py
ex "$SETTINGS" <<END
/^INSTALLED_APPS\s*=/
/^]$/
a
# OAUTH APPS - BEGIN - Do not edit or remove this line!
INSTALLED_APPS += [
    'django.contrib.sites',
    'vires_oauth',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    #'allauth.socialaccount.providers.facebook',
    #'allauth.socialaccount.providers.twitter',
    #'allauth.socialaccount.providers.linkedin_oauth2',
    #'allauth.socialaccount.providers.google',
    #'allauth.socialaccount.providers.github',
    #'allauth.socialaccount.providers.dropbox_oauth2',
    'django_countries',
    'oauth2_provider',
]

SOCIALACCOUNT_PROVIDERS = {
    'linkedin_oauth2': {
        'SCOPE': [
            'r_emailaddress',
            'r_basicprofile',
        ],
       'PROFILE_FIELDS': [
            'id',
            'first-name',
            'last-name',
            'email-address',
            'picture-url',
            'public-profile-url',
            'industry',
            'positions',
            'location',
        ],
    },
}

# OAUTH APPS - END - Do not edit or remove this line!
.
/^MIDDLEWARE\s*=/
/^]/a
# OAUTH MIDDLEWARE - BEGIN - Do not edit or remove this line!

# app specific middlewares
MIDDLEWARE += [
    'vires_oauth.middleware.access_logging_middleware',
    'vires_oauth.middleware.inactive_user_logout_middleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # SessionAuthenticationMiddleware is only available in django 1.7
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# general purpose middleware classes
MIDDLEWARE += [
    'django.middleware.gzip.GZipMiddleware',
]

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of allauth
    'django.contrib.auth.backends.ModelBackend',
    # allauth specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Django allauth
SITE_ID = 1 # ID from django.contrib.sites
LOGIN_URL = "$OAUTH_BASE_URL_PATH/accounts/login/"
LOGIN_REDIRECT_URL = "$OAUTH_BASE_URL_PATH"
ACCOUNT_LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
#ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
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
ACCOUNT_SIGNUP_FORM_CLASS = 'vires_oauth.forms.SignupForm'
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = True

#PROFILE_UPDATE_SUCCESS_URL = "/accounts/profile/"
#PROFILE_UPDATE_SUCCESS_MESSAGE = "Profile was updated successfully."
#PROFILE_UPDATE_TEMPLATE = "account/userprofile_update_form.html"
#WORKSPACE_TEMPLATE="vires/workspace.html"
#OWS11_EXCEPTION_XSL = join(STATIC_URL, "other/owserrorstyle.xsl")

# OAUTH MIDDLEWARE - END - Do not edit or remove this line!
.
\$a
# OAUTH LOGGING - BEGIN - Do not edit or remove this line!
LOGGING['loggers'].update({
    'vires_oauth': {
        'handlers': ['server_log_file'],
        'level': 'DEBUG' if DEBUG else 'INFO',
        'propagate': False,
    },
    #'django.request': {
    #    'handlers': ['access_log_file'],
    #    'level': 'DEBUG' if DEBUG else 'INFO',
    #    'propagate': False,
    #},
})
# OAUTH LOGGING - END - Do not edit or remove this line!
.
/^TEMPLATES\s*=/
/^]/a
# OAUTH TEMPLATES - BEGIN - Do not edit or remove this line!
# OAUTH TEMPLATES - END - Do not edit or remove this line!
.
wq
END

#-------------------------------------------------------------------------------
# STEP 7: setup logfiles


_create_log_file() {
    [ -d "`dirname "$1"`" ] || mkdir -p "`dirname "$1"`"
    touch "$1"
    chown "$VIRES_USER:$VIRES_GROUP" "$1"
    chmod 0664 "$1"
}
_create_log_file "$OAUTHLOG"
_create_log_file "$ACCESSLOG"
_create_log_file "$GUNICORN_ACCESS_LOG"
_create_log_file "$GUNICORN_ERROR_LOG"

#setup logrotate configuration
cat >"/etc/logrotate.d/vires_oauth_${INSTANCE}" <<END
$OAUTHLOG {
    copytruncate
    weekly
    minsize 1M
    rotate 560
    compress
}
$ACCESSLOG {
    copytruncate
    weekly
    minsize 1M
    rotate 560
    compress
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
# STEP 8: DJANGO INITIALISATION
info "Initializing Django instance '${INSTANCE}' ..."

# collect static files
python "$MNGCMD" collectstatic -l --noinput

# setup new database
python "$MNGCMD" migrate --noinput

#-------------------------------------------------------------------------------
# STEP 9: CHANGE OWNERSHIP OF THE CONFIGURATION FILES

info "Changing ownership of $INSTROOT/$INSTANCE to $VIRES_INSTALL_USER"
chown -R "$VIRES_INSTALL_USER:$VIRES_INSTALL_GROUP" "$INSTROOT/$INSTANCE"

#-------------------------------------------------------------------------------
# STEP 10: GUNICORN SETUP

echo "/etc/systemd/system/${OAUTH_SERVICE_NAME}.service"
cat > "/etc/systemd/system/${OAUTH_SERVICE_NAME}.service" <<END
[Unit]
Description=VirES OAuth2 Authorization server
After=network.target
Before=httpd.service

[Service]
PIDFile=/run/${OAUTH_SERVICE_NAME}.pid
Type=simple
WorkingDirectory=$INSTROOT/$INSTANCE
ExecStart=${P3_VENV_ROOT}/bin/gunicorn \\
    --preload \\
    --name ${OAUTH_SERVICE_NAME} \\
    --user $VIRES_USER \\
    --group $VIRES_GROUP \\
    --workers $OAUTH_SERVER_NPROC \\
    --threads $OAUTH_SERVER_NTHREAD \\
    --pid /run/${OAUTH_SERVICE_NAME}.pid \\
    --access-logfile $GUNICORN_ACCESS_LOG \\
    --error-logfile $GUNICORN_ERROR_LOG \\
    --capture-output \\
    --bind "$OAUTH_SERVER_HOST" \\
    --chdir $INSTROOT/$INSTANCE \\
    $INSTANCE.wsgi
ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s TERM \$MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target
END

systemctl daemon-reload
systemctl enable "${OAUTH_SERVICE_NAME}.service"
