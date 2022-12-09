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

# flag indicating whether the installation script shall enable the firewall
export ENABLE_FIREWALL=${ENABLE_FIREWALL:-NO}

# public hostname (or IP number) under which the ODA-OS shall be accessible
# NOTE: Critical parameter! Be sure you set it to the proper value.
export VIRES_HOSTNAME=${VIRES_HOSTNAME}

# URL root to be used by the WPS references
# NOTE: Critical parameter! Be sure you set it to the proper value.
export VIRES_URL_ROOT=${VIRES_URL_ROOT}

# root directory of the VirES
export VIRES_ROOT=${VIRES_ROOT:-/var/www/vires}

# directory where the log files shall be placed
export VIRES_LOGDIR=${VIRES_LOGDIR:-/var/log/vires}

# directory of the short-term data storage
export VIRES_TMPDIR=${VIRES_TMPDIR:-/tmp/vires}

# location of the data cache directory
export VIRES_CACHE_DIR=${VIRES_CACHE_DIR:-$VIRES_ROOT/cache}

# location of the data upload directory
export VIRES_UPLOAD_DIR=${VIRES_UPLOAD_DIR:-$VIRES_ROOT/upload}

# directory where the PosgreSQL DB stores the files
#export VIRES_PGDATA_DIR=${VIRES_PGDATA_DIR:-/var/lib/pgsql/data}

# directory of the long-term data storage
export VIRES_DATADIR=${VIRES_DATADIR:-/mnt/data}

# names of the user and group
export VIRES_GROUP=${VIRES_GROUP:-vires}
export VIRES_USER=${VIRES_USER:-vires}

# location of the VirES user home directory
export VIRES_USER_HOME=${VIRES_USER_HOME:-$VIRES_ROOT/home}

# names of the user and group used to install SW and configuration
export VIRES_INSTALL_GROUP=${VIRES_INSTALL_GROUP:-root}
export VIRES_INSTALL_USER=${VIRES_INSTALL_USER:-root}

# location of the VirES Server home directory
export VIRES_SERVER_HOME=${VIRES_SERVER_HOME:-$VIRES_ROOT/swarm}
# location of the VirES Server URL
export VIRES_SERVER_HOST=${VIRES_SERVER_HOST:-127.0.0.1:8011}
# VirES server - service name
export VIRES_SERVICE_NAME=${VIRES_SERVICE_NAME:-swarm}

# location of the OAuth2 Server home directory
export OAUTH_SERVER_HOME=${OAUTH_SERVER_HOME:-$VIRES_ROOT/oauth}
# location of the OAuth2 Server URL
export OAUTH_SERVER_HOST=${OAUTH_SERVER_HOST:-127.0.0.1:8010}
# OAuth2 server - service name
export OAUTH_SERVICE_NAME=${OAUTH_SERVICE_NAME:-oauth}

# number of processes to be used by the VirES-Server instances
export VIRES_SERVER_NPROC=${VIRES_SERVER_NPROC:-4}
# number of threads per process to be used by the VirES-Server instances
export VIRES_SERVER_NTHREAD=${VIRES_SERVER_NTHREAD:-1}

# location of the VirES Client home directory
export VIRES_CLIENT_HOME=${VIRES_CLIENT_HOME:-$VIRES_ROOT/client}

# WPS configuration - service name
export VIRES_WPS_SERVICE_NAME=${VIRES_WPS_SERVICE_NAME:-eoxs_wps_async}
# WPS configuration - permanent storage location
export VIRES_WPS_ROOT_DIR=${VIRES_WPS_ROOT_DIR:-$VIRES_ROOT/wps}
# WPS configuration - temporary workspace location
export VIRES_WPS_TEMP_DIR=${VIRES_WPS_TEMP_DIR:-$VIRES_WPS_ROOT_DIR/workspace}
# WPS configuration - permanent storage location
export VIRES_WPS_PERM_DIR=${VIRES_WPS_PERM_DIR:-$VIRES_WPS_ROOT_DIR/public}
# WPS configuration - persistent task storage
export VIRES_WPS_TASK_DIR=${VIRES_WPS_TASK_DIR:-$VIRES_WPS_ROOT_DIR/tasks}
# WPS configuration - permanent storage - public URL path
export VIRES_WPS_URL_PATH=${VIRES_WPS_URL_PATH:-/wps}
# WPS configuration - IPC socket file
export VIRES_WPS_SOCKET=${VIRES_WPS_SOCKET:-$VIRES_WPS_ROOT_DIR/socket/socket}
# WPS configuration - number of parallel workers
export VIRES_WPS_NPROC=${VIRES_WPS_NPROC:-4}
# WPS configuration - maximum number of queued jobs
export VIRES_WPS_MAX_JOBS=${VIRES_WPS_MAX_JOBS:-128}

# optional VRE/JupyterHub base URL
export VIRES_VRE_JHUB_URL

# some apache configurations
export SSL_CERTIFICATE_FILE=${SSL_CERTIFICATE_FILE:-/etc/pki/tls/certs/localhost.crt}
export SSL_CERTIFICATE_KEYFILE=${SSL_CERTIFICATE_KEYFILE:-/etc/pki/tls/private/localhost.key}
export SSL_CACERTIFICATE_FILE=${SSL_CACERTIFICATE_FILE:-}
export SSL_CERTIFICATE_CHAINFILE=${SSL_CERTIFICATE_CHAINFILE:-}

# some database configuration
INSTANCE="`basename "$VIRES_SERVER_HOME"`"
export DBNAME=${DBNAME:-eoxs_${INSTANCE}}
export DBUSER=${DBUSER:-eoxs_admin_${INSTANCE}}
export DBPASSWD=${DBPASSWD:-${INSTANCE}_admin_eoxs_`head -c 24 < /dev/urandom | base64 | tr '/' '_'`}
export DBHOST=${DBHOST:-}
export DBPORT=${DBPORT:-}

# are we using virtualenv
export ENABLE_VIRTUALENV=${ENABLE_VIRTUALENV:-YES}

# VirES-Server virtual environment
export VIRES_VENV_ROOT="${VIRES_VENV_ROOT:-$VIRES_ROOT/venv_p36_vires}"

# OAuth server virtual environment
export OAUTH_VENV_ROOT="${OAUTH_VENV_ROOT:-$VIRES_ROOT/venv_p36_oauth}"

# Jupyter Hub virtual environment
export JHUB_VENV_ROOT="${JHUB_VENV_ROOT:-$VIRES_ROOT/venv_p36_jhub}"

# Switch controlling whether the AllAuth gets configured or not.
export CONFIGURE_ALLAUTH=${CONFIGURE_ALLAUTH:-NO}

# Optional location of the loaded fixtures.
export FIXTURES_DIR_SRC="${FIXTURES_DIR_SRC}"

# Optional location of the loaded templates.
export TEMPLATES_DIR_SRC="${TEMPLATES_DIR_SRC}"

# Apache options
# the site configuration files
export CONF_HTTP
export CONF_HTTPS

# optional configuration file templates
export CONF_HTTP_TEMPLATE
export CONF_HTTPS_TEMPLATE

# configuration switches
export CONFIGURE_HTTP
export CONFIGURE_HTTPS

export PIP_OPTIONS="--upgrade --upgrade-strategy=only-if-needed"

export PG_VERSION="${PG_VERSION:-12}"
export PG_REPO="${PG_REPO:-pgdg$PG_VERSION}"
export PG_PACKAGE="${PG_RPM:-postgresql$PG_VERSION}"
export PGIS_PACKAGE="${PGIS_PACKAGE:-postgis31_$PG_VERSION}"

# local development URL
export LOCAL_URL="${LOCAL_URL}"

# compiler options
export DEVTOOLSET_VERSION=${DEVTOOLSET_VERSION:-11}
export GCC_MARCH=${GCC_MARCH:-skylake}
export GCC_MTUNE=${GCC_MTUNE:-$GCC_MARCH}
