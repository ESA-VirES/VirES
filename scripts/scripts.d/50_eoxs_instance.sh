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
CONFIGURE_WPSASYNC=${CONFIGURE_WPSASYNC:-YES}

# NOTE: Multiple EOxServer instances are not foreseen in VIRES.

#[ -z "$VIRES_HOSTNAME" ] && error "Missing the required VIRES_HOSTNAME variable!"
[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"
[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"
[ -z "$VIRES_GROUP" ] && error "Missing the required VIRES_GROUP variable!"
[ -z "$VIRES_LOGDIR" ] && error "Missing the required VIRES_LOGDIR variable!"
[ -z "$VIRES_TMPDIR" ] && error "Missing the required VIRES_TMPDIR variable!"
[ -z "$VIRES_WPS_SERVICE_NAME" ] && error "Missing the required VIRES_WPS_SERVICE_NAME variable!"
[ -z "$VIRES_WPS_TEMP_DIR" ] && error "Missing the required VIRES_WPS_TEMP_DIR variable!"
[ -z "$VIRES_WPS_PERM_DIR" ] && error "Missing the required VIRES_WPS_PERM_DIR variable!"
[ -z "$VIRES_WPS_TASK_DIR" ] && error "Missing the required VIRES_WPS_TASK_DIR variable!"
[ -z "$VIRES_WPS_URL_PATH" ] && error "Missing the required VIRES_WPS_URL_PATH variable!"
[ -z "$VIRES_WPS_SOCKET" ] && error "Missing the required VIRES_WPS_SOCKET variable!"
[ -z "$VIRES_WPS_NPROC" ] && error "Missing the required VIRES_WPS_NPROC variable!"
[ -z "$VIRES_WPS_MAX_JOBS" ] && error "Missing the required VIRES_WPS_MAX_JOBS variable!"

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
BASE_URL_PATH=""
STATIC_URL_PATH="/${INSTANCE}_static" # DO NOT USE THE TRAILING SLASH!!!

DBENGINE="django.contrib.gis.db.backends.postgis"
DBNAME="eoxs_${INSTANCE}"
DBUSER="eoxs_admin_${INSTANCE}"
DBPASSWD="${INSTANCE}_admin_eoxs_`head -c 24 < /dev/urandom | base64 | tr '/' '_'`"
DBHOST=""
DBPORT=""

PG_HBA="`sudo -u postgres psql -qA -d template_postgis -c "SHOW data_directory;" | grep -m 1 "^/"`/pg_hba.conf"

EOXSLOG="${VIRES_LOGDIR}/eoxserver/${INSTANCE}/eoxserver.log"
ACCESSLOG="${VIRES_LOGDIR}/eoxserver/${INSTANCE}/access.log"
EOXSCONF="${INSTROOT}/${INSTANCE}/${INSTANCE}/conf/eoxserver.conf"
EOXSURL="${VIRES_URL_ROOT}${BASE_URL_PATH}/ows?"
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
sudo -u "$VIRES_USER" eoxserver-instance.py "$INSTANCE" "$INSTROOT/$INSTANCE"

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
        EnableSendfile off
        Options -MultiViews +FollowSymLinks
        Header set Access-Control-Allow-Origin "*"
    </Directory>

    # WSGI service endpoint
    WSGIScriptAlias "${BASE_URL_PATH:-/}" "${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
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
# NOTE: Set the hostname manually if needed.
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
        },
        'request_filter': {
            '()': 'django_requestlogging.logging_filters.RequestFilter'
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
        'eoxserver_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '${EOXSLOG}',
            'formatter': 'default',
            'filters': [],
        },
        'access_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '${ACCESSLOG}',
            'formatter': 'access',
            'filters': ['request_filter'],
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
            'handlers': ['eoxserver_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'access': {
            'handlers': ['access_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        '': {
            'handlers': ['eoxserver_file'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
}
.
g/^\s*'eoxserver.resources.processes',/s/'eoxserver.resources.processes'/#&/
wq
END

# touch the logfile and set the right permissions
_create_log_file() {
    [ ! -f "$1" ] || rm -fv "$1"
    [ -d "`dirname "$1"`" ] || mkdir -p "`dirname "$1"`"
    touch "$1"
    chown "$VIRES_USER:$VIRES_GROUP" "$1"
    chmod 0664 "$1"
}
_create_log_file "$EOXSLOG"
_create_log_file "$ACCESSLOG"

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
$ACCESSLOG {
    copytruncate
    weekly
    minsize 1M
    compress
    rotate 8
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
/^# VIRES LOGGING - BEGIN/,/^# VIRES LOGGING - END/d
/^# WPSASYNC COMPONENTS - BEGIN/,/^# WPSASYNC COMPONENTS - END/d
/^# WPSASYNC LOGGING - BEGIN/,/^# WPSASYNC LOGGING - END/d
/^# ALLAUTH APPS - BEGIN/,/^# ALLAUTH APPS - END/d
/^# ALLAUTH MIDDLEWARE_CLASSES - BEGIN/,/^# ALLAUTH MIDDLEWARE_CLASSES - END/d
/^# ALLAUTH LOGGING - BEGIN/,/^# ALLAUTH LOGGING - END/d
/^# REQUESTLOGGING APPS - BEGIN/,/^# REQUESTLOGGING APPS - END/d
/^# REQUESTLOGGING MIDDLEWARE_CLASSES - BEGIN/,/^# REQUESTLOGGING MIDDLEWARE_CLASSES - END/d
wq
END

{ sudo -u "$VIRES_USER" ex "$URLS" || /bin/true ; } <<END
/^# ALLAUTH URLS - BEGIN/,/^# ALLAUTH URLS - END/d
wq
END

{ sudo -u "$VIRES_USER" ex "$EOXSCONF" || /bin/true ; } <<END
/^# WPSASYNC - BEGIN/,/^# WPSASYNC - END/d
wq
END

# configure the apps ...

if [ "$CONFIGURE_VIRES" != "YES" ]
then
    warn "VIRES specific configuration is disabled."
else
    info "VIRES specific configuration ..."

    # remove unnecessary or conflicting component paths
    { sudo -u "$VIRES_USER" ex "$SETTINGS" || /bin/true ; } <<END
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.services\.ows\.wcs\.\*\*'/#&/
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.services\.native\.\*\*'/#&/
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.services\.gdal\.\*\*'/#&/
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.services\.mapserver\.\*\*'/#&/
wq
END

    # extending the EOxServer settings.py
    sudo -u "$VIRES_USER" ex "$SETTINGS" <<END
/^INSTALLED_APPS\s*=/
/^)/
a
# VIRES APPS - BEGIN - Do not edit or remove this line!
INSTALLED_APPS += (
    'vires',
)

VIRES_AUX_DB_DST = join(PROJECT_DIR, "aux_dst.cdf")
VIRES_AUX_DB_KP = join(PROJECT_DIR, "aux_kp.cdf")
VIRES_AUX_DB_IBIA = join(PROJECT_DIR, "aux_ibia.cdf")
VIRES_ORBIT_COUNTER_DB = {
    'A': join(PROJECT_DIR, "SW_OPER_AUXAORBCNT.cdf"),
    'B': join(PROJECT_DIR, "SW_OPER_AUXBORBCNT.cdf"),
    'C': join(PROJECT_DIR, "SW_OPER_AUXBORBCNT.cdf"),
}

# TODO: Find a better way how to map a collection to the satellite!
#"SW_OPER_FAC_TMS_2F", ???

# satellite to collection mapping
VIRES_SAT2COL = {
    'A': [
        "SW_OPER_MAGA_LR_1B",
        "SW_OPER_EFIA_PL_1B",
        "SW_OPER_IBIATMS_2F",
        "SW_OPER_TECATMS_2F",
        "SW_OPER_FACATMS_2F",
        "SW_OPER_EEFATMS_2F",
    ],
    'B': [
        "SW_OPER_MAGB_LR_1B",
        "SW_OPER_EFIB_PL_1B",
        "SW_OPER_IBIBTMS_2F",
        "SW_OPER_TECBTMS_2F",
        "SW_OPER_FACBTMS_2F",
        "SW_OPER_EEFBTMS_2F",
    ],
    'C': [
        "SW_OPER_MAGC_LR_1B",
        "SW_OPER_EFIC_PL_1B",
        "SW_OPER_IBICTMS_2F",
        "SW_OPER_TECCTMS_2F",
        "SW_OPER_FACCTMS_2F",
        "SW_OPER_EEFCTMS_2F",
    ],
}

# collection to satellite mapping
VIRES_COL2SAT = {}
for satellite, collections in VIRES_SAT2COL.items():
    VIRES_COL2SAT.update(
        (collection, satellite) for collection in collections
    )

# relations between range-type satellite collections
VIRES_TYPE2COL = {
    "SWARM_MAG": {
        "A": "SW_OPER_MAGA_LR_1B",
        "C": "SW_OPER_MAGC_LR_1B",
    },
}

# VIRES APPS - END - Do not edit or remove this line!
.
/^COMPONENTS\s*=/
/^)/a
# VIRES COMPONENTS - BEGIN - Do not edit or remove this line!
COMPONENTS += (
    'eoxserver.services.mapserver.wms.*',
    'vires.processes.*',
    'vires.ows.**',
    'vires.forward_models.*',
    'vires.mapserver.**',
)
# VIRES COMPONENTS - END - Do not edit or remove this line!
.
\$a
# VIRES LOGGING - BEGIN - Do not edit or remove this line!
LOGGING['loggers']['vires'] = {
    'handlers': ['eoxserver_file'],
    'level': 'DEBUG' if DEBUG else 'INFO',
    'propagate': False,
}
# VIRES LOGGING - END - Do not edit or remove this line!
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
    'eoxs_allauth',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.twitter',
    'allauth.socialaccount.providers.linkedin_oauth2',
    'allauth.socialaccount.providers.google',
    #'allauth.socialaccount.providers.github',
    #'allauth.socialaccount.providers.dropbox_oauth2',
    'django_countries',
)

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

# ALLAUTH APPS - END - Do not edit or remove this line!
.
/^MIDDLEWARE_CLASSES\s*=/
/^)/a
# ALLAUTH MIDDLEWARE_CLASSES - BEGIN - Do not edit or remove this line!

# allauth specific middleware classes
MIDDLEWARE_CLASSES += (
    'eoxs_allauth.middleware.InactiveUserLogoutMiddleware',
    'eoxs_allauth.middleware.AccessLoggingMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # SessionAuthenticationMiddleware is only available in django 1.7
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# VirES Specific middleware classes
MIDDLEWARE_CLASSES += (
    'django.middleware.gzip.GZipMiddleware',
)

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of allauth
    'django.contrib.auth.backends.ModelBackend',
    # allauth specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Django allauth
SITE_ID = 1 # ID from django.contrib.sites
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "${BASE_URL_PATH:-/}"
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
#ACCOUNT_EMAIL_VERIFICATION = 'none'
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
ACCOUNT_SIGNUP_FORM_CLASS = 'eoxs_allauth.forms.ESASignupForm'
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = True

TEMPLATE_CONTEXT_PROCESSORS = (
    # Required by allauth template tags
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
)

# EOxServer AllAuth
PROFILE_UPDATE_SUCCESS_URL = "/accounts/profile/"
PROFILE_UPDATE_SUCCESS_MESSAGE = "Profile was updated successfully."
PROFILE_UPDATE_TEMPLATE = "account/userprofile_update_form.html"
WORKSPACE_TEMPLATE="vires/workspace.html"
OWS11_EXCEPTION_XSL = join(STATIC_URL, "other/owserrorstyle.xsl")

# ALLAUTH MIDDLEWARE_CLASSES - END - Do not edit or remove this line!
.
\$a
# ALLAUTH LOGGING - BEGIN - Do not edit or remove this line!
LOGGING['loggers'].update({
    'eoxs_allauth': {
        'handlers': ['access_file'],
        'level': 'DEBUG' if DEBUG else 'INFO',
        'propagate': False,
    },
    'django.request': {
        'handlers': ['access_file'],
        'level': 'DEBUG' if DEBUG else 'INFO',
        'propagate': False,
    },
})
# ALLAUTH LOGGING - END - Do not edit or remove this line!
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
import eoxs_allauth.views
from django.views.generic import TemplateView

urlpatterns += patterns('',
    url(r'^/?$', eoxs_allauth.views.workspace),
    url(r'^ows$', eoxs_allauth.views.wrapped_ows),
    url(r'^accounts/', include('eoxs_allauth.urls')),
    url(
        r'^accounts/faq$',
        TemplateView.as_view(template_name='account/faq.html'),
        name='faq'
    ),
    url(
        r'^accounts/datatc$',
        TemplateView.as_view(template_name='account/datatc.html'),
        name='datatc'
    ),
    url(
        r'^accounts/servicetc$',
         TemplateView.as_view(template_name='account/servicetc.html'),
        name='servicetc'
    ),
)
# ALLAUTH URLS - END - Do not edit or remove this line!
.
wq
END

fi # end of ALLAUTH configuration

# REQUESTLOGGER configuration
sudo -u "$VIRES_USER" ex "$SETTINGS" <<END
/^INSTALLED_APPS\s*=/
/^)/
a
# REQUESTLOGGING APPS - BEGIN - Do not edit or remove this line!
INSTALLED_APPS += (
    'django_requestlogging',
)
# REQUESTLOGGING APPS - END - Do not edit or remove this line!
.
/^MIDDLEWARE_CLASSES\s*=/
/^)/a
# REQUESTLOGGING MIDDLEWARE_CLASSES - BEGIN - Do not edit or remove this line!

# request logger specific middleware classes
MIDDLEWARE_CLASSES += (
    'django_requestlogging.middleware.LogSetupMiddleware',
)
# REQUESTLOGGING MIDDLEWARE_CLASSES - END - Do not edit or remove this line!
.
wq
END
# end of REQUESTLOGGER configuration


# WPS-ASYNC CONFIGURATION
if [ "$CONFIGURE_WPSASYNC" != "YES" ]
then
    warn "WPS async backend specific configuration is disabled."
else
    info "WPS async backend specific configuration ..."

    # locate proper configuration file (see also apache configuration)
    {
        locate_apache_conf 80
        locate_apache_conf 443
    } | while read CONF
    do
        { ex "$CONF" || /bin/true ; } <<END
/EOXS01_BEGIN/,/EOXS01_END/de
/^[ 	]*<\/VirtualHost>/i
    # EOXS01_BEGIN - EOxServer instance - Do not edit or remove this line!

    # WPS static content
    Alias "$VIRES_WPS_URL_PATH" "$VIRES_WPS_PERM_DIR"
    <Directory "$VIRES_WPS_PERM_DIR">
        EnableSendfile off
        Options -MultiViews +FollowSymLinks
        Header set Access-Control-Allow-Origin "*"
    </Directory>

    # EOXS01_END - EOxServer instance - Do not edit or remove this line!
.
wq
END
    done

    # extending the EOxServer settings.py
    sudo -u "$VIRES_USER" ex "$SETTINGS" <<END
/^COMPONENTS\s*=/
/^)/a
# WPSASYNC COMPONENTS - BEGIN - Do not edit or remove this line!
COMPONENTS += (
    'eoxs_wps_async.backend',
    'eoxs_wps_async.processes.**',
)
# WPSASYNC COMPONENTS - END - Do not edit or remove this line!
.
\$a
# WPSASYNC LOGGING - BEGIN - Do not edit or remove this line!
LOGGING['loggers']['eoxs_wps_async'] = {
    'handlers': ['eoxserver_file'],
    'level': 'DEBUG' if DEBUG else 'INFO',
    'propagate': False,
}
# WPSASYNC LOGGING - END - Do not edit or remove this line!
.
wq
END

    [ -n "`grep -m 1 '\[services\.ows\.wps\]' "$EOXSCONF"`" ] || echo '[services.ows.wps]' >> "$EOXSCONF"

    # extending the EOxServer configuration
    sudo -u "$VIRES_USER" ex "$EOXSCONF" <<END
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

    # reset the required WPS directories
    [ ! -d "$VIRES_WPS_TEMP_DIR" ] || rm -fRv "$VIRES_WPS_TEMP_DIR"
    [ ! -d "$VIRES_WPS_PERM_DIR" ] || rm -fRv "$VIRES_WPS_PERM_DIR"
    [ ! -d "$VIRES_WPS_TASK_DIR" ] || rm -fRv "$VIRES_WPS_TASK_DIR"

    for D in "$VIRES_WPS_TEMP_DIR" "$VIRES_WPS_PERM_DIR" "$VIRES_WPS_TASK_DIR" "`dirname "$VIRES_WPS_SOCKET"`"
    do
        mkdir -p "$D"
        chown -v "$VIRES_USER:$VIRES_GROUP" "$D"
        chmod -v 0755 "$D"
    done

    info "WPS async backend ${VIRES_WPS_SERVICE_NAME}.service initialization ..."

    cat > "/etc/systemd/system/${VIRES_WPS_SERVICE_NAME}.service" <<END
[Unit]
Description=Asynchronous EOxServer WPS Daemon
After=network.target
Before=httpd.service

[Service]
Type=simple
User=$VIRES_USER
ExecStartPre=/usr/bin/rm -fv $VIRES_WPS_SOCKET
ExecStart=/usr/bin/python -EsOm eoxs_wps_async.daemon ${INSTANCE}.settings $INSTROOT/$INSTANCE

[Install]
WantedBy=multi-user.target
END

    systemctl daemon-reload
    systemctl enable "${VIRES_WPS_SERVICE_NAME}.service"
    systemctl restart "${VIRES_WPS_SERVICE_NAME}.service"
    systemctl status "${VIRES_WPS_SERVICE_NAME}.service"

fi # end of WPS-ASYNC configuration

#-------------------------------------------------------------------------------
# STEP 7: EOXSERVER INITIALISATION
info "Initializing EOxServer instance '${INSTANCE}' ..."

# collect static files
sudo -u "$VIRES_USER" python "$MNGCMD" collectstatic -l --noinput

# setup new database
#sudo -u "$VIRES_USER" python "$MNGCMD" makemigrations
# NOTE: Django 1.8 'makemigrations' does not seem to properly initialize
#       new migrations and the command has to be called for each app separately.
#       See: http://stackoverflow.com/questions/29689365/auth-user-error-with-django-1-8-and-syncdb-migrate
{
python - << END
import sys
sys.path.append("$INSTROOT/$INSTANCE")
import ${INSTANCE}.settings as settings
for app in settings.INSTALLED_APPS:
    print app.rpartition('.')[-1]
END
} | while read APP
do
    python "$MNGCMD" makemigrations "$APP"
done
sudo -u "$VIRES_USER" python "$MNGCMD" migrate

#-------------------------------------------------------------------------------
# STEP 8: APP-SPECIFIC INITIALISATION

if [ "$CONFIGURE_VIRES" == "YES" ]
then
    # load rangetypes
    sudo -u "$VIRES_USER" python "$MNGCMD" vires_rangetype_load || true

    # register models
    sudo -u "$VIRES_USER" python "$MNGCMD" vires_model_remove --all
    sudo -u "$VIRES_USER" python "$MNGCMD" vires_model_add "SIFM" "IGRF12" "CHAOS-5-Combined"
fi

#-------------------------------------------------------------------------------
# STEP 9: FINAL WEB SERVER RESTART
systemctl restart httpd.service
systemctl status httpd.service
