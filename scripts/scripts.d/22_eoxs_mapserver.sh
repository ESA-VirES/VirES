#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Mapserver / Mapscript installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh
. `dirname $0`/../lib_util.sh

info "Installing mapserver packages ..."

[ -z "`rpm -qa | grep swig-2`" ] || yum --assumeyes remove swig
yum --assumeyes install mapserver mapserver-devel gdal-devel proj-devel libxml2-devel swig3

activate_venv "$VIRES_VENV_ROOT"

[ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"
PACKAGE="`lookup_package "$CONTRIB_DIR/python-mapscript-*.tar.gz"`"
[ -n "$PACKAGE" ] || error "Source distribution package not found!"
pip install $PIP_OPTIONS "$PACKAGE"
