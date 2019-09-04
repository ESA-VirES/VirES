#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Install Python development files.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing Python 3 ..."

yum --assumeyes install install python3 python3-devel python3-pip
