#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

#info "Installing EOxMagMod in the development mode."
info "Installing EOxMagMod from sources ..."

# Path to the EOxMagMod development directory tree:
EOXMM_DEV_PATH="${EOXMM_DEV_PATH:-/usr/local/eoxmagmod}"

# STEP 1: INSTALL DEPENDENCIES
yum --assumeyes install gcc-gfortran python-devel numpy wmm2010-lib wmm2010-devel qdipole

# STEP 2: INSTALL EOXMM
# Install EOxMagMod in the development mode.
pushd .
cd $EOXMM_DEV_PATH
# make sure we build the package from scratch
[ -d './build' ] && rm -fvR './build'
# install python package
python ./setup.py install
popd
