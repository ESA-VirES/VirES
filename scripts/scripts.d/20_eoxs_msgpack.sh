#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: numpy installation.
# Author(s): Daniel Santillan <daniel.santillan@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing msgpack ..."

activate_venv "$EOXS_VENV_ROOT"

pip install $PIP_OPTIONS 'msgpack-python'
