#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES for Swarm server installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing VirES for Swarm server packages in the development mode."

activate_virtualenv

# STEP 1: INSTALL DEPENDENCIES
pip install matplotlib

# STEP 2: INSTALL VIRES
VIRES_DEV_PATH="${VIRES_DEV_PATH:-/usr/local/vires}"

# Install VirES EOxServer extension
pushd .
cd "$VIRES_DEV_PATH/vires"
python ./setup.py develop
popd

# Install EOxServer django-allauth integration
pushd .
cd "$VIRES_DEV_PATH/eoxs_allauth"
python ./setup.py develop
popd
