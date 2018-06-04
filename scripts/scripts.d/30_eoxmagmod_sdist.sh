#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library - sdist installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

SOURCE_URL="https://github.com/ESA-VirES/MagneticModel/releases/download/eoxmagmod-0.5.0/eoxmagmod-0.5.0.tar.gz"

info "Installing EOxMagMod from source disribution package ..."

activate_virtualenv

yum --assumeyes install wmm2015-lib wmm2015-devel qdipole qdipole-devel

pip install $PIP_OPTIONS "$SOURCE_URL"
