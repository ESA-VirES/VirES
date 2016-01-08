#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: ViRES server - local RPM package
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing ViRES-Server from a local RPM package ..."

[ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"

# locate latest RPM package
FNAME="`ls "$CONTRIB_DIR"/eoxmagmod-*.rpm | sort | tail -n 1`"

[ -n "$FNAME" -a -f "$FNAME" ] || { error "Failed to locate the RPM package." ; exit 1 ; }

# install the package and its dependencies
yum --assumeyes install "$FNAME"
