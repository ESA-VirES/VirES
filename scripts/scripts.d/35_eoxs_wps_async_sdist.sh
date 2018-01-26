#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer WPS asynchronous back-end installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

SOURCE_URL="https://github.com/DAMATS/WPS-Backend/archive/0.3.0.tar.gz"

info "Installing EOxServer asynchronous WPS backend."

activate_virtualenv

pip install "$SOURCE_URL"
