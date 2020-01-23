#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library - sdist installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

SOURCE="https://github.com/ESA-VirES/MagneticModel/releases/download/eoxmagmod-0.9.7/eoxmagmod-0.9.7.tar.gz"

info "Installing EOxMagMod from a source distribution package ..."

activate_venv "$EOXS_VENV_ROOT"

# requires spacepy + cdf to be installed
yum --assumeyes install qdipole qdipole-devel

pip install $PIP_OPTIONS "$SOURCE"
