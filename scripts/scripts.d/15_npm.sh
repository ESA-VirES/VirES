#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: NPM package mamager installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing NPM package manager ..."

yum --assumeyes install npm
