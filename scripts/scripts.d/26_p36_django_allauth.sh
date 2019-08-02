#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: django-allauth installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python3_venv.sh

info "Installing django-allauth ..."

activate_venv

pip install $PIP_OPTIONS 'django-allauth>=0.39.1<0.40a0'
pip install $PIP_OPTIONS 'django-countries>=5.3.3<5.4a0'
