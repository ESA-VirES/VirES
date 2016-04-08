#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES server - production mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing VirES-Server packages."

# Path to the VirES-Server development directory tree:
VIRES_DEV_PATH="${VIRES_DEV_PATH:-/usr/local/vires}"

# STEP 1: INSTALL DEPENDENCIES
yum --assumeyes install python-matplotlib python-setuptools

# STEP 2: INSTALL VIRES
# setup.py install keeps messy leftovers!
# Uninstall previously installed package.
PACKAGE=VirES-Server
[ -z "`pip freeze | grep "$PACKAGE" `" ] || pip uninstall -y "$PACKAGE"
# Install VirES EOxServer extension
pushd .
cd "$VIRES_DEV_PATH/vires"
[ ! -d build/ ] || rm -fvR build/
[ ! -d dist/ ] || rm -fvR dist/
python ./setup.py install
popd

# STEP 3: INSTALL EOxServer django-allauth integration
# setup.py install keeps messy leftovers!
# Uninstall previously installed package.
PACKAGE=EOxServer-allauth
[ -z "`pip freeze | grep "$PACKAGE" `" ] || pip uninstall -y "$PACKAGE"
pushd .
[ ! -d build/ ] || rm -fvR build/
[ ! -d dist/ ] || rm -fvR dist/
cd "$VIRES_DEV_PATH/eoxs_allauth"
python ./setup.py install
popd
