#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: head-less maptlotlib installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing scipy ..."

activate_virtualenv

pip install $PIP_OPTIONS 'matplotlib'

# configure the default backend for the install (need by pip installs) and execution user

for USER in $VIRES_USER $VIRES_INSTALL_USER
do
    USERS_HOME="`getent passwd "$USER" | cut -f 6 -d ':'`"
    [ -z "$USERS_HOME" ] && continue
    CONF_PATH="${USERS_HOME}/.config/matplotlib/matplotlibrc"
    sudo -u "$USER" mkdir -p "`dirname "$CONF_PATH"`"
    sudo -u "$USER" touch "$CONF_PATH"
    echo "backend:Agg" > "$CONF_PATH"
done
