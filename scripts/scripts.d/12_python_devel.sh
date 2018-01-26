#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Install Python development files.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing Python development files ..."

yum --assumeyes install install python-devel gcc-gfortran gcc-c++
