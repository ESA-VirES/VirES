#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: mapserver installation - optional local RPM package
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing mapserver RPM package ..."

[ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"

# try to locate the lates RPM packages
MAPSERVER_RPM="`ls "$CONTRIB_DIR"/mapserver-[0-9]*.x86_64.rpm 2>/dev/null | sort | tail -n 1`"
MAPSERVER_PY_RPM="`ls "$CONTRIB_DIR"/mapserver-python-[0-9]*.x86_64.rpm 2>/dev/null | sort | tail -n 1`"
MAPSERVER_RPM_VERSION="`basename "$MAPSERVER_RPM" | sed -e 's/^mapserver-//'`"
MAPSERVER_PY_RPM_VERSION="`basename "$MAPSERVER_PY_RPM" | sed -e 's/^mapserver-python-//'`"

# install from yum repository first
#(yum update below doesn't throw an error on nothing to do)
yum --assumeyes install mapserver mapserver-python

# if there are the required RPMs and all have the same version
# preferably install the local packages
if [ -n "$MAPSERVER_RPM" -a -n "$MAPSERVER_PY_RPM" -a "$MAPSERVER_RPM_VERSION" = "$MAPSERVER_PY_RPM_VERSION" ]
then
    info "Following local RPM packages located:"
    info "$MAPSERVER_RPM"
    info "$MAPSERVER_PY_RPM"
    yum --assumeyes update "$MAPSERVER_RPM" "$MAPSERVER_PY_RPM"
fi
