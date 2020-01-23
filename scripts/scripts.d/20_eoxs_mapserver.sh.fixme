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

info "Installing mapserver RPM packages ..."

yum --assumeyes install mapserver mapserver-python

if is_virtualenv_enabled
then
    # a hack adding system-site mapscript package to virtualenv
    link_file "/usr/lib64/python2.7/site-packages/_mapscript.so" "$VIRTUALENV_ROOT/lib64/python2.7/site-packages/_mapscript.so"
    link_file "/usr/lib64/python2.7/site-packages/mapscript.py" "$VIRTUALENV_ROOT/lib64/python2.7/site-packages/mapscript.py"
fi
