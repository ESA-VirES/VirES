#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library - sdist installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

SOURCE_URL="https://github.com/ESA-VirES/MagneticModel/releases/download/eoxmagmod-0.8.1/eoxmagmod-0.8.1.tar.gz"

info "Installing EOxMagMod from source disribution package ..."

activate_virtualenv

yum --assumeyes install qdipole qdipole-devel

pip install $PIP_OPTIONS "$SOURCE_URL"
