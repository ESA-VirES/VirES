#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: django-allauth installation
# Author(s): Daniel Santillan <daniel.santillan@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing django-allauth ..."

activate_virtualenv

pip install $PIP_OPTIONS python-openid
pip install $PIP_OPTIONS requests-oauthlib
pip install $PIP_OPTIONS "django-allauth==0.32.0"
pip install $PIP_OPTIONS "django-countries==3.4.1"
