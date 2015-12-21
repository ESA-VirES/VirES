#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: PIP Python package mamager installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing PIP Python package manager ..."

yum --assumeyes install python-pip
