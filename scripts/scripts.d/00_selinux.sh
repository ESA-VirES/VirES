#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: SELinux configuration
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Configuring SELinux ..."

# change to permissive mode in the current session
[ `getenforce` != "Disabled" ] && setenforce "Permissive"

# disable SELinux permanently
sed -e 's/^[ 	]*SELINUX=/SELINUX=permissive/' -i /etc/selinux/config

# print status
sestatus
