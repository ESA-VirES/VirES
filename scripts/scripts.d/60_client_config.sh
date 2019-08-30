#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES client installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_apache.sh
. `dirname $0`/../lib_eoxserver.sh

CONFIGURE_ALLAUTH="${CONFIGURE_ALLAUTH:-YES}"

info "Configuring VirES client ..."

set_instance_variables
required_variables VIRES_CLIENT_HOME STATIC_DIR

VIRES_CLIENT_URL="/`basename "$VIRES_CLIENT_HOME"`"
#VIRES_SERVER_URL="${VIRES_SERVER_URL:-}"

if [ "$CONFIGURE_ALLAUTH" == "YES" ]
then
    INSTALL_DIR="${STATIC_DIR}/workspace"
else
    INSTALL_DIR="${VIRES_CLIENT_HOME}"
fi

[ -d "$VIRES_CLIENT_HOME" ] || {
    warn "The client does not seem to be installed."
    warn "The client configuration is skipped."
    exit 0
}

#-------------------------------------------------------------------------------
# Client configuration.

CONFIG_JSON="${INSTALL_DIR}/scripts/config.json"
[ -f "$CONFIG_JSON" ] || error "Client configuration file $CONFIG_JSON not found!"

# replace OWS URLs
OLD_URL="http://localhost:9000/vires00/"
[ -z "$OLD_URL" ] || sed -i -e "s#\"${OLD_URL}#\"${VIRES_SERVER_URL}#g" "$CONFIG_JSON"
#OLD_URL="`jq -r '.mapConfig.products[].download.url | select(.)' "$CONFIG_JSON" | sort | uniq | grep '/ows$' | head -n 1`"
#[ -z "$OLD_URL" ] || sed -i -e "s#\"${OLD_URL}#\"${VIRES_SERVER_URL}/ows#g" "$CONFIG_JSON"

#-------------------------------------------------------------------------------
# Integration with the Apache web server

info "Configuring Apache web server"

if [ "$CONFIGURE_ALLAUTH" == "YES" ]
then
    warn "ALLAUTH enabled. Removing self-standing client configuration."
fi

# locate proper configuration file (see also apache configuration)
{
    locate_apache_conf 80
    locate_apache_conf 443
} | while read CONF
do

    { ex "$CONF" || /bin/true ; } <<END
/EOXC00_BEGIN/,/EOXC00_END/de
wq
END

    [ "$CONFIGURE_ALLAUTH" == "YES" ] || ex "$CONF" <<END
/^[ 	]*<\/VirtualHost>/i
    # EOXC00_BEGIN - VirES Client - Do not edit or remove this line!

    RedirectMatch permanent ^/$ /eoxc/

    # VirES Client
    Alias $VIRES_CLIENT_URL "$VIRES_CLIENT_HOME"
    <Directory "$VIRES_CLIENT_HOME">
        Options -MultiViews +FollowSymLinks
    </Directory>

    # EOXC00_END - VirES Client - Do not edit or remove this line!
.
wq
END
done
