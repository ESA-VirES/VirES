#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer instance configuration
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_apache.sh

info "Configuring EOxServer instance ... "

# Configuration switches - all default to YES
CONFIGURE_VIRES=${CONFIGURE_VIRES:-YES}
CONFIGURE_ALLAUTH=${CONFIGURE_ALLAUTH:-YES}

# NOTE: Multiple EOxServer instances are not foreseen in VIRES.

#[ -z "$VIRES_HOSTNAME" ] && error "Missing the required VIRES_HOSTNAME variable!"
[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"
[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"
[ -z "$VIRES_GROUP" ] && error "Missing the required VIRES_GROUP variable!"
[ -z "$VIRES_LOGDIR" ] && error "Missing the required VIRES_LOGDIR variable!"
[ -z "$VIRES_TMPDIR" ] && error "Missing the required VIRES_TMPDIR variable!"

#HOSTNAME="$VIRES_HOSTNAME"
INSTANCE="`basename "$VIRES_SERVER_HOME"`"
INSTROOT="`dirname "$VIRES_SERVER_HOME"`"

SETTINGS="${INSTROOT}/${INSTANCE}/${INSTANCE}/settings.py"
WSGI_FILE="${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
URLS="${INSTROOT}/${INSTANCE}/${INSTANCE}/urls.py"
FIXTURES_DIR="${INSTROOT}/${INSTANCE}/${INSTANCE}/data/fixtures"
INSTSTAT_DIR="${INSTROOT}/${INSTANCE}/${INSTANCE}/static"
WSGI="${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
MNGCMD="${INSTROOT}/${INSTANCE}/manage.py"
#BASE_URL_PATH="/${INSTANCE}" # DO NOT USE THE TRAILING SLASH!!!
BASE_URL_PATH="/"
STATIC_URL_PATH="/${INSTANCE}_static" # DO NOT USE THE TRAILING SLASH!!!

DBENGINE="django.contrib.gis.db.backends.postgis"
DBNAME="eoxs_${INSTANCE}"
DBUSER="eoxs_admin_${INSTANCE}"
DBPASSWD="${INSTANCE}_admin_eoxs_`head -c 24 < /dev/urandom | base64 | tr '/' '_'`"
DBHOST=""
DBPORT=""

PG_HBA="`sudo -u postgres psql -qA -d template_postgis -c "SHOW data_directory;" | grep -m 1 "^/"`/pg_hba.conf"

EOXSLOG="${VIRES_LOGDIR}/eoxserver/${INSTANCE}/eoxserver.log"
EOXSCONF="${INSTROOT}/${INSTANCE}/${INSTANCE}/conf/eoxserver.conf"
EOXSURL="${BASE_URL_PATH}/ows?"
EOXSMAXSIZE="20480"
EOXSMAXPAGE="200"

# process group label
EOXS_WSGI_PROCESS_GROUP=${EOXS_WSGI_PROCESS_GROUP:-eoxs_ows}

#-------------------------------------------------------------------------------
# STEP 1: CREATE INSTANCE

info "Creating EOxServer instance '${INSTANCE}' in '$INSTROOT/$INSTANCE' ..."

if [ -d "$INSTROOT/$INSTANCE" ]
then
    info " The instance seems to already exist. All files will be removed!"
    rm -fvR "$INSTROOT/$INSTANCE"
fi

# check availability of the EOxServer
#HINT: Does python complain that the apparently installed EOxServer
#      package is not available? First check that the 'eoxserver' tree is
#      readable by anyone. (E.g. in case of read protected home directory when
#      the development setup is used.)
sudo -u "$VIRES_USER" python -c 'import eoxserver' || {
    error "EOxServer does not seem to be installed!"
    exit 1
}

sudo -u "$VIRES_USER" mkdir -p "$INSTROOT/$INSTANCE"
sudo -u "$VIRES_USER" eoxserver-admin.py create_instance "$INSTANCE" "$INSTROOT/$INSTANCE"

#-------------------------------------------------------------------------------
# STEP 2: CREATE POSTGRES DATABASE

info "Creating EOxServer instance's Postgres database '$DBNAME' ..."

# deleting any previously existing database
sudo -u postgres psql -q -c "DROP DATABASE $DBNAME ;" 2>/dev/null \
  && warn " The already existing database '$DBNAME' was removed." || /bin/true

# deleting any previously existing user
TMP=`sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DBUSER' ;"`
if [ 1 == "$TMP" ]
then
    sudo -u postgres psql -q -c "DROP USER $DBUSER ;"
    warn " The alredy existing database user '$DBUSER' was removed"
fi

# create new users
sudo -u postgres psql -q -c "CREATE USER $DBUSER WITH ENCRYPTED PASSWORD '$DBPASSWD' NOSUPERUSER NOCREATEDB NOCREATEROLE ;"
sudo -u postgres psql -q -c "CREATE DATABASE $DBNAME WITH OWNER $DBUSER TEMPLATE template_postgis ENCODING 'UTF-8' ;"

# prepend to the beginning of the acess list
{ sudo -u postgres ex "$PG_HBA" || /bin/true ; } <<END
g/# EOxServer instance:.*\/$INSTANCE/d
g/^\s*local\s*$DBNAME/d
/#\s*TYPE\s*DATABASE\s*USER\s*.*ADDRESS\s*METHOD/a
# EOxServer instance: $INSTROOT/$INSTANCE
local	$DBNAME	$DBUSER	md5
local	$DBNAME	all	reject
.
wq
END

systemctl restart postgresql.service
systemctl status postgresql.service

#-------------------------------------------------------------------------------
# STEP 3: SETUP DJANGO DB BACKEND

sudo -u "$VIRES_USER" ex "$SETTINGS" <<END
1,\$s/\('ENGINE'[	 ]*:[	 ]*\).*\(,\)/\1'$DBENGINE',/
1,\$s/\('NAME'[	 ]*:[	 ]*\).*\(,\)/\1'$DBNAME',/
1,\$s/\('USER'[	 ]*:[	 ]*\).*\(,\)/\1'$DBUSER',/
1,\$s/\('PASSWORD'[	 ]*:[	 ]*\).*\(,\)/\1'$DBPASSWD',/
1,\$s/\('HOST'[	 ]*:[	 ]*\).*\(,\)/#\1'$DBHOST',/
1,\$s/\('PORT'[	 ]*:[	 ]*\).*\(,\)/#\1'$DBPORT',/
1,\$s:\(STATIC_URL[	 ]*=[	 ]*\).*:\1'$STATIC_URL_PATH/':
wq
END
#ALLOWED_HOSTS = []

#-------------------------------------------------------------------------------
# STEP 4: APACHE WEB SERVER INTEGRATION

info "Mapping EOxServer instance '${INSTANCE}' to URL path '${INSTANCE}' ..."

# locate proper configuration file (see also apache configuration)
{
    locate_apache_conf 80
    locate_apache_conf 443
} | while read CONF
do
    { ex "$CONF" || /bin/true ; } <<END
/EOXS00_BEGIN/,/EOXS00_END/de
/^[ 	]*<\/VirtualHost>/i
    # EOXS00_BEGIN - EOxServer instance - Do not edit or remove this line!

    # EOxServer instance configured by the automatic installation script

    # static content
    Alias "$STATIC_URL_PATH" "$INSTSTAT_DIR"
    <Directory "$INSTSTAT_DIR">
        Options -MultiViews +FollowSymLinks
        Header set Access-Control-Allow-Origin "*"
    </Directory>

    # WSGI service endpoint
    WSGIScriptAlias "$BASE_URL_PATH" "${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
    <Directory "${INSTROOT}/${INSTANCE}/${INSTANCE}">
        <Files "wsgi.py">
            WSGIProcessGroup $EOXS_WSGI_PROCESS_GROUP
            WSGIApplicationGroup %{GLOBAL}
            Header set Access-Control-Allow-Origin "*"
            Header set Access-Control-Allow-Headers Content-Type
            Header set Access-Control-Allow-Methods "POST, GET"
        </Files>
    </Directory>

    # EOXS00_END - EOxServer instance - Do not edit or remove this line!
.
wq
END
done

#-------------------------------------------------------------------------------
# STEP 5: EOXSERVER CONFIGURATION

# remove any previous configuration blocks
{ sudo -u "$VIRES_USER" ex "$EOXSCONF" || /bin/true ; } <<END
/^# WMS_SUPPORTED_CRS - BEGIN/,/^# WMS_SUPPORTED_CRS - END/d
/^# WCS_SUPPORTED_CRS - BEGIN/,/^# WCS_SUPPORTED_CRS - END/d
wq
END

# set the new configuration
sudo -u "$VIRES_USER" ex "$EOXSCONF" <<END
/^[	 ]*http_service_url[	 ]*=/s;\(^[	 ]*http_service_url[	 ]*=\).*;\1${EOXSURL};
g/^#.*supported_crs/,/^$/d
/\[services\.ows\.wms\]/a
# WMS_SUPPORTED_CRS - BEGIN - Do not edit or remove this line!
supported_crs=4326,3857,#900913, # WGS84, WGS84 Pseudo-Mercator, and GoogleEarth spherical mercator
        3035, #ETRS89
        2154, # RGF93 / Lambert-93
        32601,32602,32603,32604,32605,32606,32607,32608,32609,32610, # WGS84 UTM  1N-10N
        32611,32612,32613,32614,32615,32616,32617,32618,32619,32620, # WGS84 UTM 11N-20N
        32621,32622,32623,32624,32625,32626,32627,32628,32629,32630, # WGS84 UTM 21N-30N
        32631,32632,32633,32634,32635,32636,32637,32638,32639,32640, # WGS84 UTM 31N-40N
        32641,32642,32643,32644,32645,32646,32647,32648,32649,32650, # WGS84 UTM 41N-50N
        32651,32652,32653,32654,32655,32656,32657,32658,32659,32660, # WGS84 UTM 51N-60N
        32701,32702,32703,32704,32705,32706,32707,32708,32709,32710, # WGS84 UTM  1S-10S
        32711,32712,32713,32714,32715,32716,32717,32718,32719,32720, # WGS84 UTM 11S-20S
        32721,32722,32723,32724,32725,32726,32727,32728,32729,32730, # WGS84 UTM 21S-30S
        32731,32732,32733,32734,32735,32736,32737,32738,32739,32740, # WGS84 UTM 31S-40S
        32741,32742,32743,32744,32745,32746,32747,32748,32749,32750, # WGS84 UTM 41S-50S
        32751,32752,32753,32754,32755,32756,32757,32758,32759,32760  # WGS84 UTM 51S-60S
        #32661,32761, # WGS84 UPS-N and UPS-S
# WMS_SUPPORTED_CRS - END - Do not edit or remove this line!
.
/\[services\.ows\.wcs\]/a
# WCS_SUPPORTED_CRS - BEGIN - Do not edit or remove this line!
supported_crs=4326,3857,#900913, # WGS84, WGS84 Pseudo-Mercator, and GoogleEarth spherical mercator
        3035, #ETRS89
        2154, # RGF93 / Lambert-93
        32601,32602,32603,32604,32605,32606,32607,32608,32609,32610, # WGS84 UTM  1N-10N
        32611,32612,32613,32614,32615,32616,32617,32618,32619,32620, # WGS84 UTM 11N-20N
        32621,32622,32623,32624,32625,32626,32627,32628,32629,32630, # WGS84 UTM 21N-30N
        32631,32632,32633,32634,32635,32636,32637,32638,32639,32640, # WGS84 UTM 31N-40N
        32641,32642,32643,32644,32645,32646,32647,32648,32649,32650, # WGS84 UTM 41N-50N
        32651,32652,32653,32654,32655,32656,32657,32658,32659,32660, # WGS84 UTM 51N-60N
        32701,32702,32703,32704,32705,32706,32707,32708,32709,32710, # WGS84 UTM  1S-10S
        32711,32712,32713,32714,32715,32716,32717,32718,32719,32720, # WGS84 UTM 11S-20S
        32721,32722,32723,32724,32725,32726,32727,32728,32729,32730, # WGS84 UTM 21S-30S
        32731,32732,32733,32734,32735,32736,32737,32738,32739,32740, # WGS84 UTM 31S-40S
        32741,32742,32743,32744,32745,32746,32747,32748,32749,32750, # WGS84 UTM 41S-50S
        32751,32752,32753,32754,32755,32756,32757,32758,32759,32760  # WGS84 UTM 51S-60S
        #32661,32761, # WGS84 UPS-N and UPS-S
# WCS_SUPPORTED_CRS - END - Do not edit or remove this line!
.
wq
END

#set the limits
sudo -u "$VIRES_USER" ex "$EOXSCONF" <<END
g/^[ 	#]*maxsize[ 	]/d
/\[services\.ows\.wcs\]/a
# maximum allowed output coverage size
# (nether width nor height can exceed this limit)
maxsize = $EOXSMAXSIZE
.
/^[	 ]*source_to_native_format_map[	 ]*=/s#\(^[	 ]*source_to_native_format_map[	 ]*=\).*#\1application/x-esa-envisat,application/x-esa-envisat#
/^[	 ]*paging_count_default[	 ]*=/s/\(^[	 ]*paging_count_default[	 ]*=\).*/\1${EOXSMAXPAGE}/

wq
END

# set the allowed hosts
# NOTE: Set the exact hostname manually if needed.
sudo -u "$VIRES_USER" ex "$SETTINGS" <<END
1,\$s/\(^ALLOWED_HOSTS\s*=\s*\).*/\1['*','127.0.0.1','::1']/
wq
END

# set-up logging
sudo -u "$VIRES_USER" ex "$SETTINGS" <<END
g/^DEBUG\s*=/s#\(^DEBUG\s*=\s*\).*#\1False#
g/^LOGGING\s*=/,/^}/d
i
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'simple': {
            'format': '[%(module)s] %(levelname)s: %(message)s'
        },
        'verbose': {
            'format': '[%(asctime)s][%(module)s] %(levelname)s: %(message)s'
        }
    },
    'handlers': {
        'eoxserver_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '${EOXSLOG}',
            'formatter': 'verbose',
            'filters': [],
        },
        'stderr_stream': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': [],
        },
    },
    'loggers': {
        'eoxserver': {
            'handlers': ['eoxserver_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'vires': {
            'handlers': ['eoxserver_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        '': {
            'handlers': ['eoxserver_file'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
    }
}
.
wq
END

# touch the logfile and set the right permissions
[ ! -f "$EOXSLOG" ] || rm -fv "$EOXSLOG"
[ -d "`dirname "$EOXSLOG"`" ] || mkdir -p "`dirname "$EOXSLOG"`"
touch "$EOXSLOG"
chown -v "$VIRES_USER:$VIRES_GROUP" "$EOXSLOG"
chmod -v 0664 "$EOXSLOG"

#setup logrotate configuration
cat >"/etc/logrotate.d/vires_eoxserver_${INSTANCE}" <<END
$EOXSLOG {
    copytruncate
    daily
    minsize 1M
    compress
    rotate 7
    missingok
}
END

# create fixtures directory
sudo -u "$VIRES_USER" mkdir -p "$FIXTURES_DIR"

#-------------------------------------------------------------------------------
# STEP 6: APPLICATION SPECIFIC SETTINGS

info "Application specific configuration ..."

# remove any previous configuration blocks
{ sudo -u "$VIRES_USER" ex "$SETTINGS" || /bin/true ; } <<END
/^# VIRES APPS - BEGIN/,/^# VIRES APPS - END/d
/^# VIRES COMPONENTS - BEGIN/,/^# VIRES COMPONENTS - END/d
/^# ALLAUTH APPS - BEGIN/,/^# ALLAUTH APPS - END/d
/^# ALLAUTH MIDDLEWARE_CLASSES - BEGIN/,/^# ALLAUTH MIDDLEWARE_CLASSES - END/d
wq
END

{ sudo -u "$VIRES_USER" ex "$URLS" || /bin/true ; } <<END
/^# ALLAUTH URLS - BEGIN/,/^# ALLAUTH URLS - END/d
wq
END

# configure the apps ...

if [ "$CONFIGURE_VIRES" != "YES" ]
then
    warn "VIRES specific configuration is disabled."
else
    info "VIRES specific configuration ..."

    # extending the EOxServer settings.py
    sudo -u "$VIRES_USER" ex "$SETTINGS" <<END
/^INSTALLED_APPS\s*=/
/^)/
a
# VIRES APPS - BEGIN - Do not edit or remove this line!
INSTALLED_APPS += (
    'vires',
)
# VIRES APPS - END - Do not edit or remove this line!
.
/^COMPONENTS\s*=/
/^)/a
# VIRES COMPONENTS - BEGIN - Do not edit or remove this line!
COMPONENTS += (
    'vires.processes.*',
    'vires.ows.**',
    'vires.forward_models.*',
    'vires.mapserver.**'
)
# VIRES COMPONENTS - END - Do not edit or remove this line!
.
wq
END

fi # end of VIRES configuration


if [ "$CONFIGURE_ALLAUTH" != "YES" ]
then
    warn "ALLAUTH specific configuration is disabled."
else
    info "ALLAUTH specific configuration ..."

    # extending the EOxServer settings.py
    sudo -u "$VIRES_USER" ex "$SETTINGS" <<END
/^INSTALLED_APPS\s*=/
/^)/
a
# ALLAUTH APPS - BEGIN - Do not edit or remove this line!
INSTALLED_APPS += (
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    #'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.facebook',
    #'allauth.socialaccount.providers.twitter',
    #'allauth.socialaccount.providers.dropbox_oauth2',
    #'eoxs_allauth',
)
# ALLAUTH APPS - END - Do not edit or remove this line!
.
/^MIDDLEWARE_CLASSES\s*=/
/^)/a
# ALLAUTH MIDDLEWARE_CLASSES - BEGIN - Do not edit or remove this line!

# allauth specific middleware classes
MIDDLEWARE_CLASSES += (
    'django.middleware.csrf.CsrfViewMiddleware',
    # SessionAuthenticationMiddleware is only available in django 1.7
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
)

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of allauth
    'django.contrib.auth.backends.ModelBackend',
    # allauth specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Django allauth
SITE_ID = 1 # ID from django.contrib.sites
LOGIN_URL = "accounts/login/"
LOGIN_REDIRECT_URL = "$BASE_URL_PATH"
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_UNIQUE_EMAIL = True
#ACCOUNT_EMAIL_SUBJECT_PREFIX = [vires.services]
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'
ACCOUNT_PASSWORD_MIN_LENGTH = 8
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_USERNAME_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_QUERY_EMAIL = True

TEMPLATE_CONTEXT_PROCESSORS = (
    # Required by allauth template tags
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth'
)

EOXS_ALLAUTH_WORKSPACE_TEMPLATE="vires/workspace.html"

# ALLAUTH MIDDLEWARE_CLASSES - END - Do not edit or remove this line!
.
wq
END

# Remove original url patterns
{ sudo -u "$VIRES_USER" ex "$URLS" || /bin/true ; } <<END
/^urlpatterns = patterns(/,/^)/s/^\\s/# /
wq
END

    # extending the EOxServer settings.py
    sudo -u "$VIRES_USER" ex "$URLS" <<END
$ a
# ALLAUTH URLS - BEGIN - Do not edit or remove this line!
from eoxs_allauth.views import workspace as eoxs_allauth_workspace

urlpatterns += patterns('',
    url(r'^/?$', eoxs_allauth_workspace),
    url(r'^ows$', include("eoxs_allauth.urls")),
    # enable authentication urls
    url(r'^accounts/', include('allauth.urls')),
)
# ALLAUTH URLS - END - Do not edit or remove this line!
.
wq
END

fi # end of ALLAUTH configuration

#-------------------------------------------------------------------------------
# STEP 7: EOXSERVER INITIALISATION
info "Initializing EOxServer instance '${INSTANCE}' ..."

# collect static files
sudo -u "$VIRES_USER" python "$MNGCMD" collectstatic -l --noinput

# setup new database
sudo -u "$VIRES_USER" python "$MNGCMD" migrate

#-------------------------------------------------------------------------------
# STEP 8: FINAL WEB SERVER RESTART
systemctl restart httpd.service
systemctl status httpd.service
