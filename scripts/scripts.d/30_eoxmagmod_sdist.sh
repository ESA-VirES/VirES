#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library - sdist installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh
#. `dirname $0`/../lib_util.sh

SOURCE_URL="https://github.com/ESA-VirES/MagneticModel/releases/download/eoxmagmod-0.4.1/eoxmagmod-0.4.1.tar.gz"

info "Installing EOxMagMod from source disribution package ..."

activate_virtualenv

# STEP 1: INSTALL DEPENDENCIES

yum --assumeyes install wmm2015-lib wmm2015-devel qdipole qdipole-devel

# STEP 2: INSTALL FROM SOURCES

PACKAGE="$SOURCE_URL"
#PACKAGE="`lookup_package "$CONTRIB_DIR/eoxmagmod-*.tar.gz"`"
#[ -n "$PACKAGE" ] || error "Source distribution package not found!"

pip install "$PACKAGE"
