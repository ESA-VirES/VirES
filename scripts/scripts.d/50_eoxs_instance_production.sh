#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer instance configuration
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_apache.sh
. `dirname $0`/../lib_virtualenv.sh
. `dirname $0`/../lib_eoxserver.sh

info "Configuring EOxServer instance ... "

activate_virtualenv

# Configuration switches - all default to YES
CONFIGURE_VIRES=${CONFIGURE_VIRES:-YES}
CONFIGURE_ALLAUTH=${CONFIGURE_ALLAUTH:-YES}
CONFIGURE_WPSASYNC=${CONFIGURE_WPSASYNC:-YES}

required_variables VIRES_HOSTNAME VIRES_HOSTNAME_INTERNAL VIRES_IP_ADDRESS
required_variables VIRES_SERVER_HOME
required_variables VIRES_USER VIRES_GROUP VIRES_INSTALL_USER VIRES_INSTALL_GROUP
required_variables VIRES_LOGDIR VIRES_TMPDIR VIRES_CACHE_DIR
required_variables VIRES_WPS_SERVICE_NAME VIRES_WPS_URL_PATH
required_variables VIRES_WPS_TEMP_DIR VIRES_WPS_PERM_DIR VIRES_WPS_TASK_DIR
required_variables VIRES_WPS_SOCKET VIRES_WPS_NPROC VIRES_WPS_MAX_JOBS
required_variables VIRES_UPLOAD_DIR

set_instance_variables

required_variables HOSTNAME
required_variables INSTANCE INSTROOT
required_variables FIXTURES_DIR STATIC_DIR
required_variables SETTINGS WSGI_FILE URLS WSGI MNGCMD EOXSCONF
required_variables STATIC_URL_PATH OWS_URL
required_variables EOXSLOG ACCESSLOG
required_variables EOXSMAXSIZE EOXSMAXPAGE
required_variables OAUTH_SERVER_HOST
required_variables DBENGINE EOXS_DBNAME
required_variables SMTP_HOSTNAME SMTP_DEFAULT_SENDER

SMTP_USE_TLS=${SMTP_USE_TLS:-YES}
SMTP_PORT=${SMTP_PORT:-25}

#-------------------------------------------------------------------------------
# STEP 1: CREATE INSTANCE (if not already present)

info "Creating EOxServer instance '${INSTANCE}' in '$INSTROOT/$INSTANCE' ..."

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

#-------------------------------------------------------------------------------
# STEP 2: SETUP DJANGO DB BACKEND

ex "$SETTINGS" <<END
1,\$s/\('ENGINE'[	 ]*:[	 ]*\).*\(,\)/\1'$DBENGINE',/
1,\$s/\('NAME'[	 ]*:[	 ]*\).*\(,\)/\1'$EOXS_DBNAME',/
1,\$s/\('USER'[	 ]*:[	 ]*\).*\(,\)/\1'$DBUSER',/
1,\$s/\('PASSWORD'[	 ]*:[	 ]*\).*\(,\)/\1'$DBPASSWD',/
1,\$s/\('HOST'[	 ]*:[	 ]*\).*\(,\)/\1'$DBHOST',/
1,\$s/\('PORT'[	 ]*:[	 ]*\).*\(,\)/\1'$DBPORT',/
1,\$s:\(STATIC_URL[	 ]*=[	 ]*\).*:\1'$STATIC_URL_PATH/':
wq
END

#-------------------------------------------------------------------------------
# STEP 4: APACHE WEB SERVER INTEGRATION

info "Mapping EOxServer instance '${INSTANCE}' to URL path '${INSTANCE}' ..."

# locate proper configuration file (see also apache configuration)
_PORT=443 # HTTPS only
[ -z `locate_apache_conf $_PORT $HOSTNAME` ] && error "Failed to locate Apache virtual host $HOSTNAME:$_PORT configuration!"
{
    locate_apache_conf $_PORT $HOSTNAME
    locate_apache_conf $_PORT $VIRES_HOSTNAME_INTERNAL
} | while read CONF
do
    { ex "$CONF" || /bin/true ; } <<END
/EOXS00_BEGIN/,/EOXS00_END/de
/^[ 	]*<\/VirtualHost>/i
    # EOXS00_BEGIN - EOxServer instance - Do not edit or remove this line!

    # EOxServer instance configured by the automatic installation script

    # static content
    Alias "$STATIC_URL_PATH" "$STATIC_DIR"
    <Directory "$STATIC_DIR">
        Options -MultiViews +FollowSymLinks
        Header set Access-Control-Allow-Origin "*"
    </Directory>

    # favicon redirect
    Alias "/favicon.ico" "$INSTSTAT_DIR/other/favicon/favicon.ico"

    # WSGI service endpoint
    WSGIScriptAlias "${BASE_URL_PATH:-/}" "${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
    <Directory "${INSTROOT}/${INSTANCE}/${INSTANCE}">
        <Files "wsgi.py">
            WSGIPassAuthorization On
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

# enable virtualenv in wsgi.py if necessary
if is_virtualenv_enabled
then
    info "Enabling virtualenv ..."
    { ex "$WSGI_FILE" || /bin/true ; } <<END
/^# Start load virtualenv$/,/^# End load virtualenv$/d
/^import sys/a
# Start load virtualenv
import site
# Add the site-packages of the chosen virtualenv to work with
site.addsitedir("${VIRTUALENV_ROOT}/local/lib/python2.7/site-packages")
# End load virtualenv
.
/^# Start activate virtualenv$/,/^# End activate virtualenv$/d
/^os.environ/a
# Start activate virtualenv
activate_env=os.path.expanduser("${VIRTUALENV_ROOT}/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))
# End activate virtualenv
.
wq
END
fi

#-------------------------------------------------------------------------------
# STEP 5: EOXSERVER CONFIGURATION

# remove any previous configuration blocks
{ ex "$EOXSCONF" || /bin/true ; } <<END
/^# WMS_SUPPORTED_CRS - BEGIN/,/^# WMS_SUPPORTED_CRS - END/d
/^# WCS_SUPPORTED_CRS - BEGIN/,/^# WCS_SUPPORTED_CRS - END/d
wq
END

# set the new configuration
ex "$EOXSCONF" <<END
/^[	 ]*http_service_url[	 ]*=/s;\(^[	 ]*http_service_url[	 ]*=\).*;\1${OWS_URL};
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
ex "$EOXSCONF" <<END
g/^[ 	#]*maxsize[ 	]/d
/\[services\.ows\.wcs\]/a
maxsize = $EOXSMAXSIZE
.
/^[	 ]*source_to_native_format_map[	 ]*=/s#\(^[	 ]*source_to_native_format_map[	 ]*=\).*#\1application/x-esa-envisat,application/x-esa-envisat#
/^[	 ]*paging_count_default[	 ]*=/s/\(^[	 ]*paging_count_default[	 ]*=\).*/\1${EOXSMAXPAGE}/

wq
END

# set secret key
[ -z "$SECRET_KEY" ] || ex "$SETTINGS" <<END
/^SECRET_KEY\\s*=/d
i
SECRET_KEY = '$SECRET_KEY'
.
wq
END

# set admins
_ADMINS="`echo $ADMINS | tr ';' '\n' | sed -s "s/^\s*\('[^']*'\)\s*,\s*\('[^']*'\)\s*$/    (\1, \2),/"`"
ex "$SETTINGS" << END
/^ADMINS\\s*=/,/^)/d
i
ADMINS = (
$_ADMINS
)
.
wq
END

# set the allowed hosts
# NOTE: Set the hostname manually if needed.
#TODO add vires.services and env.host to ALLOWED_HOSTS
ex "$SETTINGS" <<END
1,\$s/\(^ALLOWED_HOSTS\s*=\s*\).*/\1['${VIRES_HOSTNAME_INTERNAL}','${VIRES_IP_ADDRESS}','${HOSTNAME}','127.0.0.1','::1']/
wq
END

# set-up logging
ex "$SETTINGS" <<END
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
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
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
        'django': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
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
END

# create fixtures directory
mkdir -p "$FIXTURES_DIR"

#-------------------------------------------------------------------------------
# STEP 6: APPLICATION SPECIFIC SETTINGS

info "Application specific configuration ..."

# remove any previous configuration blocks
{ ex "$SETTINGS" || /bin/true ; } <<END
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
/^# EMAIL_BACKEND - BEGIN/,/^# EMAIL_BACKEND - END/d
wq
END

{ ex "$URLS" || /bin/true ; } <<END
/^# ALLAUTH URLS - BEGIN/,/^# ALLAUTH URLS - END/d
/^# NOAUTH URLS - BEGIN/,/^# NOAUTH URLS - END/d
/^# VIRES URLS - BEGIN/,/^# VIRES URLS - END/d
wq
END

{ ex "$EOXSCONF" || /bin/true ; } <<END
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
    { ex "$SETTINGS" || /bin/true ; } <<END
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.services\.ows\.wcs\.\*\*'/#&/
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.services\.ows\.wms\.\*\*'/#&/
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.services\.native\.\*\*'/#&/
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.services\.gdal\.\*\*'/#&/
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.services\.mapserver\.\*\*'/#&/
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.services\.opensearch\.\*\*'/#&/
g/^COMPONENTS\s*=\s*(/,/^)/s/'eoxserver\.resources\.coverages/#&/
g/^COMPONENTS\s*=\s*(/,/^)/s/##\+/#/
wq
END

    # extending the EOxServer settings.py
    ex "$SETTINGS" <<END
/^INSTALLED_APPS\s*=/
/^)/
a
# VIRES APPS - BEGIN - Do not edit or remove this line!
INSTALLED_APPS += (
    'vires',
)

VIRES_UPLOAD_DIR = "$VIRES_UPLOAD_DIR"
VIRES_AUX_DB_DST = "$VIRES_CACHE_DIR/aux_dst.cdf"
VIRES_AUX_DB_KP = "$VIRES_CACHE_DIR/aux_kp.cdf"
VIRES_AUX_DB_IBIA = "$VIRES_CACHE_DIR/aux_ibia.cdf"
VIRES_AUX_IMF_2__COLLECTION = "SW_OPER_AUX_IMF_2_"
VIRES_CACHED_PRODUCTS = {
    "AUX_F10_2_": "$VIRES_CACHE_DIR/SW_OPER_AUX_F10_2_.cdf",
    "MCO_SHA_2C": "$VIRES_CACHE_DIR/SW_OPER_MCO_SHA_2C.shc",
    "MCO_SHA_2D": "$VIRES_CACHE_DIR/SW_OPER_MCO_SHA_2D.shc",
    "MCO_SHA_2F": "$VIRES_CACHE_DIR/SW_OPER_MCO_SHA_2F.shc",
    "MCO_CHAOS6": "$VIRES_CACHE_DIR/SW_OPER_MCO_CHAOS6.shc",
    "MLI_SHA_2C": "$VIRES_CACHE_DIR/SW_OPER_MLI_SHA_2C.shc",
    "MLI_SHA_2D": "$VIRES_CACHE_DIR/SW_OPER_MLI_SHA_2D.shc",
    "MMA_SHA_2C": "$VIRES_CACHE_DIR/SW_OPER_MMA_SHA_2C.cdf",
    "MMA_SHA_2F": "$VIRES_CACHE_DIR/SW_OPER_MMA_SHA_2F.cdf",
    "MIO_SHA_2C": "$VIRES_CACHE_DIR/SW_OPER_MIO_SHA_2C.txt",
    "MIO_SHA_2D": "$VIRES_CACHE_DIR/SW_OPER_MIO_SHA_2D.txt",
    "MMA_CHAOS6": "$VIRES_CACHE_DIR/SW_OPER_MMA_CHAOS6.cdf",
    "AUXAORBCNT": "$VIRES_CACHE_DIR/SW_OPER_AUXAORBCNT.cdf",
    "AUXBORBCNT": "$VIRES_CACHE_DIR/SW_OPER_AUXBORBCNT.cdf",
    "AUXCORBCNT": "$VIRES_CACHE_DIR/SW_OPER_AUXCORBCNT.cdf",
    "AUXAODBGEO": "$VIRES_CACHE_DIR/SW_VIRE_AUXAODBGEO.cdf",
    "AUXBODBGEO": "$VIRES_CACHE_DIR/SW_VIRE_AUXBODBGEO.cdf",
    "AUXCODBGEO": "$VIRES_CACHE_DIR/SW_VIRE_AUXCODBGEO.cdf",
    "AUXAODBMAG": "$VIRES_CACHE_DIR/SW_VIRE_AUXAODBMAG.cdf",
    "AUXBODBMAG": "$VIRES_CACHE_DIR/SW_VIRE_AUXBODBMAG.cdf",
    "AUXCODBMAG": "$VIRES_CACHE_DIR/SW_VIRE_AUXCODBMAG.cdf",
}
VIRES_ORBIT_COUNTER_FILE = {
    "A": VIRES_CACHED_PRODUCTS["AUXAORBCNT"],
    "B": VIRES_CACHED_PRODUCTS["AUXBORBCNT"],
    "C": VIRES_CACHED_PRODUCTS["AUXCORBCNT"],
}
VIRES_ORBIT_DIRECTION_GEO_FILE = {
    "A": VIRES_CACHED_PRODUCTS["AUXAODBGEO"],
    "B": VIRES_CACHED_PRODUCTS["AUXBODBGEO"],
    "C": VIRES_CACHED_PRODUCTS["AUXCODBGEO"],
}
VIRES_ORBIT_DIRECTION_MAG_FILE = {
    "A": VIRES_CACHED_PRODUCTS["AUXAODBMAG"],
    "B": VIRES_CACHED_PRODUCTS["AUXBODBMAG"],
    "C": VIRES_CACHED_PRODUCTS["AUXCODBMAG"],
}
VIRES_SPACECRAFTS = list(VIRES_ORBIT_COUNTER_FILE)

# TODO: Find a better way how to map a collection to the satellite!
#"SW_OPER_FAC_TMS_2F", ???

# satellite to collection mapping
VIRES_SAT2COL = {
    'A': [
        "SW_OPER_MAGA_LR_1B",
        "SW_OPER_EFIA_LP_1B",
        "SW_OPER_EFIA_PL_1B",
        "SW_OPER_IBIATMS_2F",
        "SW_OPER_TECATMS_2F",
        "SW_OPER_FACATMS_2F",
        "SW_OPER_EEFATMS_2F",
        "SW_OPER_IPDAIRR_2F",
    ],
    'B': [
        "SW_OPER_MAGB_LR_1B",
        "SW_OPER_EFIB_LP_1B",
        "SW_OPER_EFIB_PL_1B",
        "SW_OPER_IBIBTMS_2F",
        "SW_OPER_TECBTMS_2F",
        "SW_OPER_FACBTMS_2F",
        "SW_OPER_EEFBTMS_2F",
        "SW_OPER_IPDBIRR_2F",
    ],
    'C': [
        "SW_OPER_MAGC_LR_1B",
        "SW_OPER_EFIC_LP_1B",
        "SW_OPER_EFIC_PL_1B",
        "SW_OPER_IBICTMS_2F",
        "SW_OPER_TECCTMS_2F",
        "SW_OPER_FACCTMS_2F",
        "SW_OPER_EEFCTMS_2F",
        "SW_OPER_IPDCIRR_2F",
    ],
}

# collection to satellite mapping
VIRES_COL2SAT = {}
for satellite, collections in VIRES_SAT2COL.items():
    VIRES_COL2SAT.update(
        (collection, satellite) for collection in collections
    )
# custom data mapping
VIRES_COL2SAT["USER_DATA"] = "U"

# relations between range-type satellite collections
VIRES_TYPE2COL = {
    "SWARM_MAG": {
        "A": "SW_OPER_MAGA_LR_1B",
        "C": "SW_OPER_MAGC_LR_1B",
    },
}

# extra sampled collections
VIRES_EXTRA_SAMPLED_COLLECTIONS = {
    "SW_OPER_EEFATMS_2F",
    "SW_OPER_EEFBTMS_2F",
    "SW_OPER_EEFCTMS_2F",
}

# collections requiring samples grouping
VIRES_GROUPED_SAMPLES_COLLECTIONS = {
    "SW_OPER_TECATMS_2F",
    "SW_OPER_TECBTMS_2F",
    "SW_OPER_TECCTMS_2F",
}

# VIRES APPS - END - Do not edit or remove this line!
.
/^COMPONENTS\s*=/
/^)/a
# VIRES COMPONENTS - BEGIN - Do not edit or remove this line!
COMPONENTS += (
    'vires.processes.*',
    'vires.ows.wms.*',
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

    if [ "$CONFIGURE_ALLAUTH" == "YES" ]
    then

        # extending the EOxServer urls.py
        ex "$URLS" <<END
$ a
# VIRES URLS - BEGIN - Do not edit or remove this line!
from logging import INFO, WARNING
from django.views.decorators.csrf import csrf_exempt
from eoxs_allauth.decorators import log_access, authenticated_only, token_authentication
import vires.views

def allauth_wrapper(view):
    view = csrf_exempt(view)
    view = authenticated_only(view)
    view = log_access(INFO, WARNING)(view)
    return view

def allauth_wrapper_with_token(view):
    view = csrf_exempt(view)
    view = authenticated_only(view)
    view = token_authentication(view)
    view = log_access(INFO, WARNING)(view)
    return view

urlpatterns += patterns('',
    url(r'^custom_data/(?P<identifier>[0-9a-f-]{36,36})?$', allauth_wrapper_with_token(vires.views.custom_data)),
    url(r'^custom_model/(?P<identifier>[0-9a-f-]{36,36})?$', allauth_wrapper(vires.views.custom_model)),
    url(r'^client_state/(?P<identifier>[0-9a-f-]{36,36})?$', allauth_wrapper(vires.views.client_state)),
)
# VIRES URLS - END - Do not edit or remove this line!
.
wq
END

    else

        # extending the EOxServer urls.py
        ex "$URLS" <<END
$ a
# VIRES URLS - BEGIN - Do not edit or remove this line!
import vires.views
urlpatterns += patterns('',
    url(r'^custom_data/(?P<identifier>[0-9a-f-]{36,36})?$', vires.views.custom_data),
    url(r'^custom_model/(?P<identifier>[0-9a-f-]{36,36})?$', vires.views.custom_model),
    url(r'^client_state/(?P<identifier>[0-9a-f-]{36,36})?$', vires.views.client_state),
)
# VIRES URLS - END - Do not edit or remove this line!
.
wq
END

    fi

fi # end of VIRES configuration


if [ "$CONFIGURE_ALLAUTH" != "YES" ]
then
    warn "ALLAUTH specific configuration is disabled."
else
    info "ALLAUTH specific configuration ..."

    # extending the EOxServer settings.py
    ex "$SETTINGS" <<END
/^INSTALLED_APPS\s*=/
/^)/
a
# ALLAUTH APPS - BEGIN - Do not edit or remove this line!
INSTALLED_APPS += (
    'eoxs_allauth',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'eoxs_allauth.vires_oauth', # VirES-OAuth2 "social account provider"
    'django_countries',
)

SOCIALACCOUNT_PROVIDERS = {
    'vires': {
        'SERVER_URL': '/oauth/',
        'DIRECT_SERVER_URL': 'http://$OAUTH_SERVER_HOST',
        'SCOPE': ['read_id', 'read_permissions'],
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
VIRES_VRE_JHUB_PERMISSION = "swarm_vre"
VIRES_VRE_JHUB_URL = ${VIRES_VRE_JHUB_URL:+"'"}${VIRES_VRE_JHUB_URL:-None}${VIRES_VRE_JHUB_URL:+"'"}
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/vires/login/"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

TEMPLATE_CONTEXT_PROCESSORS = (
    # Required by allauth template tags
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'eoxs_allauth.vires_oauth.context_processors.vires_oauth',
    'eoxs_allauth.context_processors.vre_jhub', # required by VRE/JupyterHub integration
)

# EOxServer AllAuth
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
    { ex "$URLS" || /bin/true ; } <<END
/^urlpatterns = patterns(/,/^)/s/^\\s/# /
wq
END

    # extending the EOxServer urls.py
    ex "$URLS" <<END
$ a
# ALLAUTH URLS - BEGIN - Do not edit or remove this line!
import eoxs_allauth.views
import eoxs_allauth.urls
from vires.client_state import parse_client_state
from django.views.generic import TemplateView

urlpatterns += patterns('',
    url(r'^/?$', eoxs_allauth.views.workspace(parse_client_state)),
    url(r'^ows$', eoxs_allauth.views.wrapped_ows),
    url(r'^accounts/', include('eoxs_allauth.urls')),
    *eoxs_allauth.urls.document_urlpatterns
)
# ALLAUTH URLS - END - Do not edit or remove this line!
.
wq
END

fi # end of ALLAUTH configuration

# e-mail backend settings
if [ "$SMTP_USE_TLS" == YES -o "$SMTP_USE_TLS" == "True" ]
then
    _SMTP_USE_TLS="True"
else
    _SMTP_USE_TLS="False"
fi

ex "$SETTINGS" <<END
\$a
# EMAIL_BACKEND - BEGIN - Do not edit or remove this line!
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = $_SMTP_USE_TLS
EMAIL_HOST = '$SMTP_HOSTNAME'
EMAIL_PORT = $SMTP_PORT
DEFAULT_FROM_EMAIL = '$SMTP_DEFAULT_SENDER'
SERVER_EMAIL = '$SERVER_EMAIL'
# EMAIL_BACKEND - END - Do not edit or remove this line!
.
wq
END

# REQUESTLOGGER configuration
ex "$SETTINGS" <<END
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
    #Disable if too many 404 are reported
    'django.middleware.common.BrokenLinkEmailsMiddleware',
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
    _PORT=443 # HTTPS only
    [ -z `locate_apache_conf $_PORT $HOSTNAME` ] && error "Failed to locate Apache virtual host $HOSTNAME:$_PORT configuration!"
    {
        locate_apache_conf $_PORT $HOSTNAME
        locate_apache_conf $_PORT $VIRES_HOSTNAME_INTERNAL
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
    ex "$SETTINGS" <<END
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

    for D in "$VIRES_WPS_TEMP_DIR" "$VIRES_WPS_PERM_DIR" "$VIRES_WPS_TASK_DIR" "`dirname "$VIRES_WPS_SOCKET"`"
    do
        mkdir -p "$D"
        chown -v "$VIRES_USER:$VIRES_GROUP" "$D"
        chmod -v 0755 "$D"
    done

    info "WPS async backend ${VIRES_WPS_SERVICE_NAME}.service initialization ..."

    if is_virtualenv_enabled
    then
        PREFIX="$VIRTUALENV_ROOT"
    else
        PREFIX="/usr"
    fi

    cat > "/etc/systemd/system/${VIRES_WPS_SERVICE_NAME}.service" <<END
[Unit]
Description=Asynchronous EOxServer WPS Daemon
After=network.target
Before=httpd.service

[Service]
Type=simple
User=$VIRES_USER
ExecStartPre=/usr/bin/rm -fv $VIRES_WPS_SOCKET
ExecStart=${PREFIX}/bin/python -EsOm eoxs_wps_async.daemon ${INSTANCE}.settings $INSTROOT/$INSTANCE

[Install]
WantedBy=multi-user.target
END

    systemctl daemon-reload
    systemctl enable "${VIRES_WPS_SERVICE_NAME}.service"

fi # end of WPS-ASYNC configuration

#-------------------------------------------------------------------------------
# STEP 7: EOXSERVER INITIALISATION
info "Initializing EOxServer instance '${INSTANCE}' ..."

# collect static files
python "$MNGCMD" collectstatic -l --noinput

# setup new database
# NOTE: When a new DB is created Django migrate does not seem to respect
#       the apps' models dependencies and does not create the models
#       in the right order.
##  setup this procedure to ensure that migrations run in the right order
#python "$MNGCMD" migrate sites
#python "$MNGCMD" migrate contenttypes
#python "$MNGCMD" migrate admin
#python "$MNGCMD" migrate auth
python "$MNGCMD" migrate --noinput

# load the social providers
if [ -n "$EOXS_SOCIAL_PROVIDERS" ]
then
    python "$MNGCMD" auth_load_social_providers --file "$EOXS_SOCIAL_PROVIDERS"
fi

#-------------------------------------------------------------------------------
# STEP 8: APP-SPECIFIC INITIALISATION
info "APP specific initialisatins (ragetypes, models, etc.) ..."

if [ "$CONFIGURE_VIRES" == "YES" ]
then
    # load rangetypes
    python "$MNGCMD" vires_rangetype_load || true
fi

#-------------------------------------------------------------------------------
# STEP 9: CHANGE OWNERSHIP OF THE CONFIGURATION FILES

info "Changing ownership of $INSTROOT/$INSTANCE to $VIRES_INSTALL_USER"
chown -R "$VIRES_INSTALL_USER:$VIRES_INSTALL_GROUP" "$INSTROOT/$INSTANCE"
