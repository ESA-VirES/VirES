#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: EOxServer utility scripts
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
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
    required_variables VIRES_SERVER_HOME VIRES_LOGDIR
 
    HOSTNAME="$VIRES_HOSTNAME"
    INSTANCE="`basename "$VIRES_SERVER_HOME"`"
    INSTROOT="`dirname "$VIRES_SERVER_HOME"`"

    SETTINGS="${INSTROOT}/${INSTANCE}/${INSTANCE}/settings.py"
    WSGI_FILE="${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
    URLS="${INSTROOT}/${INSTANCE}/${INSTANCE}/urls.py"
    FIXTURES_DIR="${INSTROOT}/${INSTANCE}/${INSTANCE}/data/fixtures"
    STATIC_DIR="${INSTROOT}/${INSTANCE}/${INSTANCE}/static"
    WSGI="${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
    MNGCMD="${INSTROOT}/${INSTANCE}/manage.py"

    #BASE_URL_PATH="/${INSTANCE}" # DO NOT USE THE TRAILING SLASH!!!
    BASE_URL_PATH=""
    STATIC_URL_PATH="/${INSTANCE}_static" # DO NOT USE THE TRAILING SLASH!!!

    EOXSLOG="${VIRES_LOGDIR}/eoxserver/${INSTANCE}/eoxserver.log"
    ACCESSLOG="${VIRES_LOGDIR}/eoxserver/${INSTANCE}/access.log"
    EOXSCONF="${INSTROOT}/${INSTANCE}/${INSTANCE}/conf/eoxserver.conf"
    OWS_URL="${VIRES_URL_ROOT}${BASE_URL_PATH}/ows"
    EOXSMAXSIZE="20480"
    EOXSMAXPAGE="200"

    # process group label
    EOXS_WSGI_PROCESS_GROUP=${EOXS_WSGI_PROCESS_GROUP:-eoxs_ows}
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
