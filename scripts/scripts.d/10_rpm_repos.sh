#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Installation of extra RPM repositories.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh  

info "Installing common RPM repositories ..."

# EPEL: http://fedoraproject.org/wiki/EPEL
rpm -q --quiet epel-release || rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm

# ELGIS: http://elgis.argeo.org/
rpm -q --quiet elgis-release || rpm -Uvh http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm

# EOX - EOX RPM repository 
rpm -q --quiet eox-release || rpm -Uvh http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm

#info "Enabling EOX testing repository for explicitly listed packages only..."
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
