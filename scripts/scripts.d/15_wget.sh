#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: WGET installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing WGET ..."

yum --assumeyes install wget
