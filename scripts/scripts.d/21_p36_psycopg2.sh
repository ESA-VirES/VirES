#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: psycopg2 - Python-PostgreSQL Database Adapter installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python3_venv.sh

info "Installing psycopg2 (Python-PostgreSQL Database Adapter) ... """

yum --assumeyes install ${PG_DEVEL_PACKAGE:-postgresql-devel}

[ -n "PG_PATH" ] && export export PATH="$PG_PATH:$PATH"
activate_venv
pip install --force-reinstall --no-binary :all: psycopg2
