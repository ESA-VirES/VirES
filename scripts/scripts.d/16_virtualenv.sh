#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Install Python virtualenv package
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing Python virtualend package ..."

# NOTE: The vritualenv is installed by the system default pip
#       which is likely outdated and some of the CLI options
#       may not be supported.
pip install --upgrade virtualenv
