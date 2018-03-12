#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: psycopg2 - Python-PostgreSQL Database Adapter installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing psycopg2 (Python-PostgreSQL Database Adapter) ... """

activate_virtualenv

pip install $PIP_OPTIONS psycopg2
