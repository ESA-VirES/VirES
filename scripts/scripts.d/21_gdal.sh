#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: GDAL installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh
. `dirname $0`/../lib_util.sh

info "Installing GDAL library ... "

yum --assumeyes install gdal gdal-libs gdal-python proj-epsg gdal-devel

if is_virtualenv_enabled
then
    # NOTE: gdal-python virenv installation requires numpy installed!!!
    activate_virtualenv
    [ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"
    PACKAGE="`lookup_package "$CONTRIB_DIR/GDAL-*.tar.gz"`"
    [ -n "$PACKAGE" ] || error "Source distribution package not found!"
    pip install $PIP_OPTIONS "$PACKAGE"
fi
