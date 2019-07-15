#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: EOxServer utility scripts
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

PG_VERSION=9.6
PGIS_VERSION=2.3
PG_DATA_DIR_DEFAULT="/var/lib/pgsql/$PG_VERSION/data"
PG_SERVICE_NAME="postgresql-$PG_VERSION.service"
PG_BIN="/usr/pgsql-$PG_VERSION/bin"
PGIS_TEMPLATES="/usr/pgsql-$PG_VERSION/share/contrib/postgis-$PGIS_VERSION"

export PATH=$PG_BIN:$PATH

alias postgresql-setup="$PG_BIN/postgresql96-setup"
