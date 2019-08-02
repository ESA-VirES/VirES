#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Installation of extra RPM repositories.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh  

info "Installing PostgresSQL RPM repository ..."

# PosgresSQL 9.6 CentOS-7 x86_64
rpm -q --quiet pgdg-redhat-repo || rpm -Uvh https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm

ex /etc/yum.repos.d/pgdg-redhat-all.repo -V <<END
1,\$s/^\\s*enabled\\s*=.*\$/enabled=0/
/\[pgdg96\]/
+1,/^gpgkey/s/^\\s*enabled\\s*=.*\$/enabled=1/
wq
END

# reset yum cache
yum clean all
