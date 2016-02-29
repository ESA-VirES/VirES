#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: PostgreSQL and PostGIS installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "The database is hosted on a different machine."
info "Thus only installing some packages."

#======================================================================

yum --assumeyes install python-psycopg2
