#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer WPS asynchronous back-end installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing EOxServer asynchronous WPS backend."

SOURCE_URL="https://github.com/DAMATS/WPS-Backend/archive/0.1.1.tar.gz"

# set temporary directory removed after the installation
TMP_DIR="`mktemp -d`"
cleanup () {
    if [ -n "$TMP_DIR " -a -d "$TMP_DIR" ]
    then
        info "Removing temporary directory $TMP_DIR"
        rm -fR "$TMP_DIR"
    fi
}
trap cleanup EXIT

# download and unpack the package and step to the installation directory
info "Downloading and unpacking source $SOURCE_URL"
cd "$TMP_DIR"
curl -sSL "$SOURCE_URL" | tar -xzf -
cd "`find -name setup.py -exec dirname {} \; | head -n 1`"

# install the software
PACKAGE=eoxs-wps-async
[ -z "`pip freeze 2>/dev/null | grep "$PACKAGE" `" ] || pip uninstall -y "$PACKAGE"
python ./setup.py install
