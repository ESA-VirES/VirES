#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Django installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing Django ..."

# STEP 1:  INSTALL PACKAGES
yum --assumeyes install python-django

# STEP 2:  PIP INSTALLERS
#pip install Django==1.4
