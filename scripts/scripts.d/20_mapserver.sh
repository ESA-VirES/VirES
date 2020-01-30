#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: mapserver RPM installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh
. `dirname $0`/../lib_util.sh

info "Installing mapserver packages ..."

if is_virtualenv_enabled
then
    activate_virtualenv

    [ -z "`rpm -qa | grep mapserver-python`" ] || yum --assumeyes remove mapserver-python
    yum --assumeyes install mapserver mapserver-devel proj-devel libxml2-devel swig

    # clean up the old installation
    rm -vf "$VIRTUALENV_ROOT/lib64/python2.7/site-packages/mapscript.py"
    rm -vf "$VIRTUALENV_ROOT/lib64/python2.7/site-packages/_mapscript.so"

    [ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"
    PACKAGE="`lookup_package "$CONTRIB_DIR/python-mapscript-*.tar.gz"`"
    [ -n "$PACKAGE" ] || error "Source distribution package not found!"
    pip install $PIP_OPTIONS "$PACKAGE"
else
    yum --assumeyes install mapserver mapserver-python
fi
