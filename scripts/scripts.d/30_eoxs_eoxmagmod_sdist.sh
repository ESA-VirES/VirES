#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library - sdist installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_util.sh
. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

required_variables DEVTOOLSET_VERSION GCC_MARCH GCC_MTUNE

SOURCE="https://github.com/ESA-VirES/MagneticModel/releases/download/eoxmagmod-0.11.0/eoxmagmod-0.11.0.tar.gz"

info "Installing EOxMagMod from a source distribution package ..."

activate_venv "$VIRES_VENV_ROOT"

# requires spacepy + cdf to be installed
yum --assumeyes install qdipole qdipole-devel

# enable newer development tools
. /opt/rh/devtoolset-${DEVTOOLSET_VERSION}/enable

# custom compiler options
export CFLAGS="-march=${GCC_MARCH} -mtune=${GCC_MTUNE} -ftree-vectorize"

pip install $PIP_OPTIONS "$SOURCE"
