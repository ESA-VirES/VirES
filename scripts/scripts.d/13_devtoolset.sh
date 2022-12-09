#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Install newer development tools.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH

. `dirname $0`/../lib_util.sh
. `dirname $0`/../lib_logging.sh

info "Installing newer development tools ..."

required_variables DEVTOOLSET_VERSION

yum install -y centos-release-scl-rh
yum install -y "devtoolset-${DEVTOOLSET_VERSION}"
