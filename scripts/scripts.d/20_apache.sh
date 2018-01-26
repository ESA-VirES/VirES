#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Apache web server installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_apache.sh

info "Installing Apache HTTP server ... "

# configuration switches
ENABLE_FIREWALL=${ENABLE_FIREWALL:-YES}
CONFIGURE_HTTP=${CONFIGURE_HTTP:-YES}
CONFIGURE_HTTPS=${CONFIGURE_HTTPS:-YES}

# STEP 1:  INSTALL RPM PACKAGES
yum --assumeyes install httpd mod_wsgi mod_ssl crypto-utils

# STEP 2: FIREWALL SETUP (OPTIONAL)
# We enable access to port 80 and 443 from anywhere
# and make the firewal chages permanent.
if [ "$ENABLE_FIREWALL" = "YES" ]
then
    if [ "$CONFIGURE_HTTP" = "YES" ]
    then
        firewall-cmd --add-service=http
        firewall-cmd --permanent --add-service=http
    fi
    if [ "$CONFIGURE_HTTPS" = "YES" ]
    then
        firewall-cmd --add-service=https
        firewall-cmd --permanent --add-service=https
    fi
fi

# STEP 3: ENABLE SERVICE
systemctl enable httpd.service
#systemctl start httpd.service
#systemctl status httpd.service
