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

# the site configuration files
CONF_DEFAULT="/etc/httpd/conf.d/vires.conf"
CONF_DEFAULT_SSL="/etc/httpd/conf.d/vires_ssl.conf"

#======================================================================

SOCKET_PREFIX="run/wsgi"

# STEP 1:  INSTALL RPMS

yum --assumeyes install httpd mod_wsgi mod_ssl


# STEP 2: FIREWALL SETUP

# we enable access to port 80 and 443 from anywhere
# and make the iptables chages permanent
if [ -z "`iptables -L | grep '^ACCEPT *tcp *-- *anywhere *anywhere *state *NEW *tcp *dpt:http'`" ]
then
    iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j ACCEPT
    service iptables save
fi
if [ -z "`iptables -L | grep '^ACCEPT *tcp *-- *anywhere *anywhere *state *NEW *tcp *dpt:https'`" ]
then
    iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport 443 -j ACCEPT
    service iptables save
fi


# STEP 3: SETUP THE DEFAUT SITE

#NOTE 1: Current setup does not support multiple virtual hosts.


# setup default unsecured site
CONF=`locate_apache_conf 80`
if [ -z "$CONF" ]
then
    CONF="$CONF_DEFAULT"
    echo "Default virtual host not located creting own one in: $CONF"
    cat >"$CONF" <<END
# default site generated by the automatic VirES instance configuration script
<VirtualHost _default_:80>
</VirtualHost>
END
else
    echo "Default virtual host located in: $CONF"
fi

# setup default secured site
CONF=`locate_apache_conf 443`

# disable the default settings from the ssl.conf
if [ "$CONF" == "/etc/httpd/conf.d/ssl.conf" ]
then
    echo "Disabling the default SSL configutation in: $CONF"
    disable_virtual_host "$CONF"
    CONF=
fi

if [ -z "$CONF" ]
then
    CONF="$CONF_DEFAULT_SSL"
    echo "Default secured virtual host not located creting own one in: $CONF"
    cat >"$CONF" <<END
# default site generated by the automatic VirES instance configuration script
<VirtualHost _default_:443>

    # common SSL settings
    ErrorLog logs/ssl_error_log
    TransferLog logs/ssl_access_log
    LogLevel warn
    SSLEngine on
    SSLProtocol all -SSLv2
    SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM:+LOW
    SSLCertificateFile /etc/pki/tls/certs/localhost.crt
    SSLCertificateKeyFile /etc/pki/tls/private/localhost.key

</VirtualHost>
END
else
    echo "Default secured virtual host located in: $CONF"
fi

# check whether WSGI socket is set already - if not do so
CONF="`locate_wsgi_socket_prefix_conf`"
if [ -z "$CONF" ]
then # set socket prefix if not already set
    echo "WSGISocketPrefix is set to: $SOCKET_PREFIX"

    echo "WSGISocketPrefix $SOCKET_PREFIX" >> /etc/httpd/conf.d/wsgi.conf
else
    echo "WSGISocketPrefix set already:"
    grep -nH WSGISocketPrefix "$CONF"
fi

# STEP 4: START THE SERVICE

# enable the HTTP service
chkconfig httpd on

#
service httpd start
