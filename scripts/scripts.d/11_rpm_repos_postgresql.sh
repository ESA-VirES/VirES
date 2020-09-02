#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Installation of extra RPM repositories.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh  

#PG_REPO_VERSION=$PG_REPO_VERSION
PG_REPO_CONF="/etc/yum.repos.d/pgdg-redhat-all.repo"

info "Installing PostgresSQL RPM repository ..."

rpm -q --quiet pgdg-redhat-repo || rpm -Uvh https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm

ex "$PG_REPO_CONF" <<END
1,\$s/^\\s*enabled\\s*=.*\$/enabled=0/
wq
END

[ -z "$PG_REPO" ] || { ex "$PG_REPO_CONF" && info "$PG_REPO enabled"; }<<END
/\[pgdg-common\]/
+1,/^gpgkey/s/^\\s*enabled\\s*=.*\$/enabled=1/
/\[$PG_REPO\]/
+1,/^gpgkey/s/^\\s*enabled\\s*=.*\$/enabled=1/
wq
END

# reset yum cache
yum clean all
