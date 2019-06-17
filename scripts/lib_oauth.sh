#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: EOxServer utility scripts
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

set_instance_variables() {
    required_variables OAUTH_SERVER_HOME VIRES_LOGDIR
 
    HOSTNAME="$VIRES_HOSTNAME"
    INSTANCE="`basename "$OAUTH_SERVER_HOME"`"
    INSTROOT="`dirname "$OAUTH_SERVER_HOME"`"

    SETTINGS="${INSTROOT}/${INSTANCE}/${INSTANCE}/settings.py"
    WSGI_FILE="${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
    URLS="${INSTROOT}/${INSTANCE}/${INSTANCE}/urls.py"
    FIXTURES_DIR="${INSTROOT}/${INSTANCE}/${INSTANCE}/data/fixtures"
    STATIC_DIR="${INSTROOT}/${INSTANCE}/${INSTANCE}/static"
    WSGI="${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
    MNGCMD="${INSTROOT}/${INSTANCE}/manage.py"

    OAUTH_BASE_URL_PATH="/${INSTANCE}" # DO NOT USE THE TRAILING SLASH!!!
    STATIC_URL_PATH="/${INSTANCE}_static" # DO NOT USE THE TRAILING SLASH!!!

    OAUTHLOG="${VIRES_LOGDIR}/oauth/${INSTANCE}/server.log"
    ACCESSLOG="${VIRES_LOGDIR}/oauth/${INSTANCE}/access.log"

    GUNICORN_ACCESS_LOG="${VIRES_LOGDIR}/oauth/${INSTANCE}/gunicorn_access.log"
    GUNICORN_ERROR_LOG="${VIRES_LOGDIR}/oauth/${INSTANCE}/gunicorn_error.log"

    # process group label
    OAUTH_WSGI_PROCESS_GROUP=${OAUTH_WSGI_PROCESS_GROUP:-oauth}
}

load_db_conf () {
    if [ -f "$1" ]
    then
        . "$1"
    fi
}

save_db_conf () {
    touch "$1"
    chmod 0600 "$1"
    cat > "$1" <<END
DBENGINE="$DBENGINE"
DBNAME="$DBNAME"
DBUSER="$DBUSER"
DBPASSWD="$DBPASSWD"
DBHOST="$DBHOST"
DBPORT="$DBPORT"
END
}

required_variables()
{
    for __VARIABLE___
    do
        if [ -z "${!__VARIABLE___}" ]
        then
            error "Missing the required ${__VARIABLE___} variable!"
        fi
    done 
}
