#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: mod_wsgi installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing Gunicorn ..."

activate_venv "$OAUTH_VENV_ROOT"

pip install $PIP_OPTIONS setproctitle
pip install $PIP_OPTIONS gunicorn
