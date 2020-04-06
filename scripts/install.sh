#!/bin/sh
set -o pipefail
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: VirES installation script
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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

INSTALL_LOG="./install.log"
SYSTEM_NAME="VirES"

#NOTE: The optional 'user.conf' is used the custom user's configuration options
#      overiding the defaults in 'lib_common.sh'.

#source common parts
[ -f "`dirname $0`/user.conf" ] && . `dirname $0`/user.conf
. `dirname $0`/lib_common.sh
. `dirname $0`/lib_logging.sh

{
    info "#"
    info "#  --= $SYSTEM_NAME installer =-- "
    info "#"
    info "#   version: $VIRES_INSTALLER_VERSION"
    info "# "

    #export location of the contrib directory
    export CONTRIB_DIR="$(cd "$(dirname "$0")/../contrib"; pwd )"

    #-------------------------------------------------------------------------------
    # check whether the user and group exists
    # if not create them

    _mkdir()
    { # <owner>[:<group>] <permissions> <dirname> <label>
        if [ ! -d "$3" ]
        then
            info "Creating $4: $3"
            mkdir -p "$3"
            chown -v "$1" "$3"
            chmod -v "$2" "$3"
        fi
    }

    id -g "$VIRES_GROUP" >/dev/null 2>&1 || \
    {
        info "Creating system group: $VIRES_GROUP"
        groupadd -r "$VIRES_GROUP"
    }

    id -u "$VIRES_USER" >/dev/null 2>&1 || \
    {
        info "Creating system user: $VIRES_USER"
        useradd -r -M -g "$VIRES_GROUP" -d "$VIRES_USER_HOME" -s /sbin/nologin -c "VirES system user" "$VIRES_USER"
        usermod -L "$VIRES_USER"
    }

    # just in case the required directories do not exists create them
    # and set the right permissions

    _mkdir "$VIRES_INSTALL_USER:$VIRES_INSTALL_GROUP" 0755 "$VIRES_ROOT" "$SYSTEM_NAME root directory"
    _mkdir "$VIRES_USER:$VIRES_GROUP" 0775 "$VIRES_USER_HOME" "'$VIRES_USER' user home directory"
    _mkdir "$VIRES_USER:$VIRES_GROUP" 0775 "$VIRES_LOGDIR" "$SYSTEM_NAME logging directory"
    _mkdir "$VIRES_USER:$VIRES_GROUP" 0775 "$VIRES_DATADIR" "$SYSTEM_NAME long-term data storage directory"
    _mkdir "$VIRES_USER:$VIRES_GROUP" 0775 "$VIRES_TMPDIR" "$SYSTEM_NAME temporary storage directory"
    _mkdir "$VIRES_USER:$VIRES_GROUP" 0775 "$VIRES_CACHE_DIR" "$SYSTEM_NAME data cache directory"
    _mkdir "$VIRES_USER:$VIRES_GROUP" 0775 "$VIRES_UPLOAD_DIR" "$SYSTEM_NAME data upload directory"

    #-------------------------------------------------------------------------------
    # execute specific installation scripts

    SCRIPTS=""
    PROFILE="install.d"

    # parse command line arguments
    while [ "$#" -gt 0 ]
    do
        case "$1" in
            -j | --jhub )
                info "Development JupyterHub profile selected."
                PROFILE="jhub.d"
                ;;
            -d | --devel )
                info "Development installation profile selected."
                PROFILE="devel.d"
                ;;
            -p | --production )
                info "Production installation profile selected."
                PROFILE="production.d"
                ;;
            *)
                SCRIPTS="$SCRIPTS $1"
            ;;
        esac
        shift
    done

    # in case of no script select all in the chosen profile
    if [ -z "$SCRIPTS" ]
    then
        SCRIPTS="`dirname $0`/$PROFILE/"*.sh
    fi

    for SCRIPT in $SCRIPTS
    do
        info "Executing installation script: $SCRIPT"
        sh -e $SCRIPT
        [ 0 -ne "$?" ] && error "Installation script ended with an error: $SCRIPT"
    done

    info "Installation has been completed."

} 2>&1 | tee -a "$INSTALL_LOG"
