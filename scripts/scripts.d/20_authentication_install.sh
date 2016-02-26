#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Authentication installation and configuration.
# Author(s): Daniel Santillan <daniel.santillan@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing  packages related to Authentication..."

yum --assumeyes install python-pip python-openid python-requests-oauthlib 
sudo pip install --upgrade --no-deps django-allauth==0.24.1 