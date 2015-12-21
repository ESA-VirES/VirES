#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: UNZIP installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing UNZIP ..."

yum --assumeyes install unzip
