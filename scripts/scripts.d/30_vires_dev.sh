#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES server - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing VirES-Server packages in the development mode."

# Path to the VirES-Server development directory tree:
VIRES_DEV_PATH="${VIRES_DEV_PATH:-/usr/local/vires}"

# STEP 1: INSTALL DEPENDENCIES
yum --assumeyes install python-matplotlib python-setuptools

# STEP 2: INSTALL VIRES
# Install VirES EOxServer extension
pushd .
cd "$VIRES_DEV_PATH/vires"
python ./setup.py develop
popd

# STEP 3: INSTALL EOxServer django-allauth integration
pushd .
cd "$VIRES_DEV_PATH/eoxs_allauth"
python ./setup.py develop
popd
