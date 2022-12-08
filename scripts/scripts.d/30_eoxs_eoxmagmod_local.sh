#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library - local installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_util.sh
. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

required_variables DEVTOOLSET_VERSION GCC_MARCH GCC_MTUNE

SOURCE="${EOXMAGMOD_SOURCE_PATH:-/usr/local/eoxmagmod}"

info "Installing EOxMagMod from a local source directory ..."

activate_venv "$VIRES_VENV_ROOT"

# requires spacepy + cdf to be installed
yum --assumeyes install qdipole qdipole-devel

# get rid of the previous build
[ -d "$SOURCE/build" ] && rm -fvR "$SOURCE/build"
[ -d "$SOURCE/dist" ] && rm -fvR "$SOURCE/dist"

# enable newer development tools
. /opt/rh/devtoolset-${DEVTOOLSET_VERSION}/enable

# custom compiler options
export CFLAGS="-march=${GCC_MARCH} -mtune=${GCC_MTUNE} -ftree-vectorize"

pip install $PIP_OPTIONS "$SOURCE"
