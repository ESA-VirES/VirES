#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: GDAL installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh
. `dirname $0`/../lib_util.sh

info "Installing GDAL library ... "

yum --assumeyes install gdal gdal-libs proj-epsg gdal-devel

activate_venv "$VIRES_VENV_ROOT"

# Current version of GDAL requires setuptools<58 (2to3 removed in 58.0.0)
pip install $PIP_OPTIONS setuptools<58

# NOTE: gdal-python virenv installation requires numpy to be installed!
[ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"
PACKAGE="`lookup_package "$CONTRIB_DIR/GDAL-*.tar.gz"`"
[ -n "$PACKAGE" ] || error "Source distribution package not found!"
pip install $PIP_OPTIONS "$PACKAGE"
