#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose:  Python OpenID, OAuth and PIL packages installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing Python OpenID, OAuth and PIL packages..."

yum --assumeyes install python-imaging  python-openid  python-requests-oauthlib


