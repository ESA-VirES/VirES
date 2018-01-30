#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES server - production mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing VirES-Server packages from sources ..."

activate_virtualenv

# Path to the VirES-Server development directory tree:
VIRES_DEV_PATH="${VIRES_DEV_PATH:-/usr/local/vires}"

# STEP 1: INSTALL DEPENDENCIES
#pip install matplotlib

# STEP 2: INSTALL VIRES

# Install VirES EOxServer extension
pushd .
cd "$VIRES_DEV_PATH/vires"
[ ! -d build/ ] || rm -fR build/
[ ! -d dist/ ] || rm -fR dist/
python setup.py bdist_wheel
pip install ./dist/VirES_Server-*.whl
rm -fR build/ dist/
popd

# STEP 3: INSTALL EOxServer django-allauth integration
cd "$VIRES_DEV_PATH/eoxs_allauth"
[ ! -d build/ ] || rm -fR build/
[ ! -d dist/ ] || rm -fR dist/
python setup.py bdist_wheel
pip install ./dist/EOxServer_allauth-*.whl
rm -fR build/ dist/
popd
