#!/bin/sh
#
# Purpose: pyAPMS installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing pyAMPS in the development mode."

activate_virtualenv

PYAMPS_SOURCE_PATH="${PYAMPS_SOURCE_PATH:-/usr/local/pyAMPS}"

if [ -d "${PYAMPS_SOURCE_PATH}" ]
then
    pip install dask
    pip install toolz
    pip install future
    pip install apexpy
    pip install pandas
    pip install -e "$PYAMPS_SOURCE_PATH"
else
    warn "pyAMPS source path $PYAMPS_SOURCE_PATH not found."
    warn "The pAMPS installation is skipped."
fi
