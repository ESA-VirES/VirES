#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library - optional local RPM package
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing EOxMagMod from a local RPM package ..."

[ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"

# locate latest RPM package
FNAME="`ls "$CONTRIB_DIR"/eoxmagmod-*.rpm | sort | tail -n 1`"

if [ -n "$FNAME" -a -f "$FNAME" ]
then 
    info "Following local RPM package located:"
    info "$FNAME"
    yum --assumeyes install "$FNAME"
else
    # defaulting to yum repository
    yum --assumeyes install eoxmagmod
fi
