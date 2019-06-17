#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Installation of extra RPM repositories.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh  

info "Installing extra RPM repositories ..."

# EPEL: http://fedoraproject.org/wiki/EPEL
yum --assumeyes install install epel-release

# ELGIS: http://elgis.argeo.org/
#rpm -q --quiet elgis-release || rpm -Uvh http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm

# EOX - EOX RPM repository 
rpm -q --quiet eox-release || rpm -Uvh http://yum.packages.eox.at/el/eox-release-7-0.noarch.rpm

# PosgresSQL 9.6 CentOS-7 x86_64
rpm -q --quiet pgdg-redhat-repo || rpm -Uvh https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm

ex /etc/yum.repos.d/pgdg-redhat-all.repo -V <<END
1,\$s/^\\s*enabled\\s*=.*\$/enabled=0/
/\[pgdg96\]/
+1,/^gpgkey/s/^\\s*enabled\\s*=.*\$/enabled=1/
wq
END

#info "Enabling EOX testing repository for explicitly listed packages ..."
#
#ex /etc/yum.repos.d/eox-testing.repo <<END
#1,\$s/^[ 	]*enabled[ 	]*=.*\$/enabled = 1/
#1,\$g/^[ 	]*includepkgs[ 	]*=.*\$/d
#1,\$g/^[ 	]*exclude[ 	]*=.*\$/d
#/\[eox-testing\]
#/^[ 	]*gpgkey[ 	]*=.*\$
#a
#includepkgs=
#exclude=
#.
#/\[eox-testing-source\]
#/^[ 	]*gpgkey[ 	]*=.*\$
#a
#includepkgs=
#exclude=
#.
#/\[eox-testing-noarch\]
#/^[ 	]*gpgkey[ 	]*=.*\$
#a
#includepkgs=
#exclude=
#.
#wq 
#END

# reset yum cache
yum clean all
