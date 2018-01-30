#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX server installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing EOxServer in the development mode ..."

activate_virtualenv

# Path to the EOxServer development directory tree:
EOXS_DEV_PATH="${EOXS_DEV_PATH:-/usr/local/eoxserver}"

# STEP 1: INSTALL DEPENDENCIES
yum --assumeyes install proj-epsg
pip install lxml
pip install python-dateutil
pip install psycopg2

# STEP 2: INSTALL EOXSERVER
cd $EOXS_DEV_PATH
python ./setup.py develop
