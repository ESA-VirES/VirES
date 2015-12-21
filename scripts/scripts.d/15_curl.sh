#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: CURL installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing CURL ..."

yum --assumeyes install curl
