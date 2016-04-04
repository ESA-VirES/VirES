#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: django-allauth installation
# Author(s): Daniel Santillan <daniel.santillan@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing django-allauth ..."

yum --assumeyes install python-openid python-requests-oauthlib
pip install --upgrade --no-deps django-allauth==0.24.1
pip install --upgrade django-countries
