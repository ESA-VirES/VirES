#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: VirES installation script - common shared defaults
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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

# version
VERSION_FILE="`dirname $0`/../version.txt"
export VIRES_INSTALLER_VERSION="`cat "$VERSION_FILE"`"

# public hostname (or IP number) under which the ODA-OS shall be accessable
# NOTE: Critical parameter! Be sure you set it to the proper value.
export VIRES_HOSTNAME=${VIRES_HOSTNAME:-$HOSTNAME}

# root directory of the VirES - by default set to '/srv/vires'
export VIRES_ROOT=${VIRES_ROOT:-/srv/vires}

# directory where the log files shall be placed - by default set to '/var/log/vires'
export VIRES_LOGDIR=${VIRES_LOGDIR:-/var/log/vires}

# directory of the short-term data storage - by default set to '/tmp/vires'
export VIRES_TMPDIR=${VIRES_TMPDIR:-/tmp/vires}

# directory where the PosgreSQL DB stores the files
export VIRES_PGDATA_DIR=${VIRES_PGDATA_DIR:-/srv/pgdata}

# directory of the long-term data storage - by default set to '/srv/eodata'
export VIRES_DATADIR=${VIRES_DATADIR:-/srv/eodata}

# names of the ODA-OS user and group - by default set to 'vires:vires'
export VIRES_GROUP=${VIRES_GROUP:-vires}
export VIRES_USER=${VIRES_USER:-vires}

# location of the VirES Server home directory
export VIRES_SERVER_HOME=${VIRES_SERVER_HOME:-$VIRES_ROOT/eoxs}
# WSGI daemon - number of processes to be used by the VirES EOxServer instances
export EOXS_WSGI_NPROC=${EOXS_WSGI_NPROC:-4}
# WSGI daemon - process group to be used by the VirES EOxServer instances
export EOXS_WSGI_PROCESS_GROUP=vires_eoxs_ows

# location of the VirES Client home directory
export VIRES_CLIENT_HOME=${VIRES_CLIENT_HOME:-$VIRES_ROOT/eoxc}

# some apache configurations
export SSLCertificateFile=${:-/etc/pki/tls/certs/localhost.crt}
export SSLCertificateKeyFile=${:-/etc/pki/tls/private/localhost.key}
export SSLCACertificateFile=${:-/dev/null}
export SSLCertificateChainFile=${:-/dev/null}
