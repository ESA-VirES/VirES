#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES client installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Adding VirES client to static files..."

[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"
[ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"
[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"
[ -z "$VIRES_GROUP" ] && error "Missing the required VIRES_GROUP variable!"

TMPDIR='/tmp/eoxc'
INSTROOT="`dirname "$VIRES_SERVER_HOME"`"
INSTANCE="`basename "$VIRES_SERVER_HOME"`"
WORKSPACE="${INSTROOT}/${INSTANCE}/${INSTANCE}/static/workspace/"


# locate lates TGZ package
FNAME="`ls "$CONTRIB_DIR"/{WebClient-Framework,VirES-Client}*.tar.gz 2>/dev/null | sort | tail -n 1`"

[ -n "$FNAME" -a -f "$FNAME" ] || { error "Failed to locate the installation package." ; exit 1 ; }

# installing the ODA-Client

# clean-up the previous installation if needed
[ -d "$WORKSPACE" ] && rm -fR "$WORKSPACE"
[ -d "$TMPDIR" ] && rm -fR "$TMPDIR"

# init
mkdir -p "$TMPDIR"

# unpack
info "Installation package located in: $FNAME"
tar -xzf "$FNAME" --directory="$TMPDIR"

# move to destination
ROOT="`find "$TMPDIR" -mindepth 1 -maxdepth 1 -type d \( -name 'VirES-Client*' -o -name 'WebClient-Framework*' \) | head -n 1`"
mv -f "$ROOT" "$WORKSPACE"


info "VirES Client added to: $WORKSPACE"
