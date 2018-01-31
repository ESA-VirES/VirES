#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Apache web server configuration on the development machine.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_apache.sh

info "Configuring Apache HTTP server ... "

# the site configuration files
CONF_HTTP="${CONF_HTTP:-/etc/httpd/conf.d/vires.conf}"
CONF_HTTPS="${CONF_HTTPS:-/etc/httpd/conf.d/vires_ssl.conf}"

# optinal configuration file templates
CONF_HTTP_TEMPLATE="${CONF_HTTP_TEMPLATE}"
CONF_HTTPS_TEMPLATE="${CONF_HTTPS_TEMPLATE}"

# configuration switches
CONFIGURE_HTTP=${CONFIGURE_HTTP:-YES}
CONFIGURE_HTTPS=${CONFIGURE_HTTPS:-YES}

# optional virtual host name
HOSTNAME="${VIRES_HOSTNAME}"

#======================================================================
# STEP 1: SETUP THE SITES
#NOTE 1: Current setup does not support multiple virtual hosts.

if [ "$CONFIGURE_HTTP" = "YES" ]
then
    PORT=80
    info "${HOSTNAME:-_default_}:$PORT configuration ..."
    # setup default unsecured site
    CONF=`locate_apache_conf $PORT $HOSTNAME`
    if [ -z "$CONF" ]
    then
        CONF="$CONF_HTTP"
        info "Configuration file not found. New one will be saved to: $CONF"
        if [ -n "$CONF_HTTP_TEMPLATE" ]
        then
            info "Using configuration template: $CONF_HTTP_TEMPLATE"
            envsubst < "$CONF_HTTP_TEMPLATE" > "$CONF"
            #cp -fv "$CONF_HTTP_TEMPLATE" "$CONF"
        else
            cat >"$CONF" <<END
# default site generated by the automatic VirES instance configuration script
<VirtualHost ${HOSTNAME:-_default_}:$PORT>

    <Location "/">
        Require all granted
    </Location>

</VirtualHost>
END
        fi
    else
        info "Configuration file found in: $CONF"
    fi
else
        info "HTTP configuration skipped."
fi

if [ "$CONFIGURE_HTTPS" = "YES" ]
then
    PORT=443
    info "${HOSTNAME:-_default_}:$PORT configuration ..."

    # disable the default settings from the ssl.conf
    CONF=`locate_apache_conf $PORT`
    if [ "$CONF" == "/etc/httpd/conf.d/ssl.conf" ]
    then
        info "Disabling the default SSL configuration in: $CONF"
        disable_virtual_host "$CONF"
        CONF=
    fi

    # setup default unsecured site
    CONF=`locate_apache_conf $PORT $HOSTNAME`
    if [ -z "$CONF" ]
    then
        CONF="$CONF_HTTPS"
        info "Configuration file not found. New one will be saved to: $CONF"
        if [ -n "$CONF_HTTPS_TEMPLATE" ]
        then

            info "Using configuration template: $CONF_HTTPS_TEMPLATE"
            envsubst < "$CONF_HTTPS_TEMPLATE" > "$CONF"
            #cp -fv "$CONF_HTTPS_TEMPLATE" "$CONF"

        else

            if [ -n "$SSL_CACERTIFICATE_FILE" ]
            then
                SSL_CACERTIFICATE_FILE_LINE="SSLCACertificateFile $SSL_CACERTIFICATE_FILE"
            else
                SSL_CACERTIFICATE_FILE_LINE="#SSLCACertificateFile <cacertificate_file>"
            fi
            if [ -n "$SSL_CERTIFICATE_CHAINFILE" ]
            then
                SSL_CERTIFICATE_CHAINFILE_LINE="SSLCertificateChainFile $SSL_CERTIFICATE_CHAINFILE"
            else
                SSL_CERTIFICATE_CHAINFILE_LINE="#SSLCertificateChainFile <certificate_chain_file>"
            fi

            cat >"$CONF" <<END
# default site generated by the automatic VirES instance configuration script
<VirtualHost ${HOSTNAME:-_default_}:$PORT>

    # common SSL settings
    ErrorLog logs/ssl_error_log
    TransferLog logs/ssl_access_log
    LogLevel warn
    SSLEngine on
    SSLProtocol all -SSLv2 -SSLv3
    SSLCipherSuite ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES256-SHA:ECDHE-ECDSA-DES-CBC3-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:!DSS
    SSLHonorCipherOrder on
    SSLCertificateFile $SSL_CERTIFICATE_FILE
    SSLCertificateKeyFile $SSL_CERTIFICATE_KEYFILE
    $SSL_CACERTIFICATE_FILE_LINE
    $SSL_CERTIFICATE_CHAINFILE_LINE

    <Location "/">
        Require all granted
    </Location>

</VirtualHost>
END
        fi
    else
        info "Configuration file found in: $CONF"
    fi
else
        info "HTTPS configuration skipped."
fi
