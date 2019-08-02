#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Jupyter Hub service instance
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_apache.sh
. `dirname $0`/../lib_python3_venv.sh

info "Configuring Jupyter Hub ..."

#required_variables VIRES_USER

export P3_VENV_ROOT="$VIRES_ROOT/python3_jhub"
activate_venv

JHUB_CLIENT_ID="vZuNuWKsT4FDl6XcHlUQJdD5idXcsTdCdgIr9fGh"
JHUB_CLIENT_SECRET="vm5ucD1dsHIXOfOwAWCGFR9zfKO8P4sJDsvJ45SzxY2je4dDfJdKpFJGtFA9ZlBI7RgNY2gbQqK9toM9Q7YA9Kv3HDSOLXkqcQ9me9Ww4rSRAdnhWGMP4iCpJ05UfNDN"

JHUB_SERVICE_NAME="jupyterhub"
JHUB_BASE_URL_PATH=""
JHUB_SERVER_HOST=127.0.0.1:8080
JHUB_BASE_URL_PATH="/jhub"
JHUB_WORK_DIR="$VIRES_ROOT/jhub/"
mkdir -m 0755 -p "$JHUB_WORK_DIR"

#-------------------------------------------------------------------------------
# Apache web server integration

# locate proper configuration file (see also apache configuration)
{
    locate_apache_conf 80
    locate_apache_conf 443
} | while read CONF
do
    { ex "$CONF" || /bin/true ; } <<END
/JHUB_BEGIN/,/JHUB_END/de
/^[ 	]*<\/VirtualHost>/i
    # JHUB_BEGIN - OAuth server instance - Do not edit or remove this line!
    # OAuth server instance configured by the automatic installation script

    <Location "$JHUB_BASE_URL_PATH">
        ProxyPreserveHost on
        ProxyPass "http://$JHUB_SERVER_HOST$JHUB_BASE_URL_PATH"
        #ProxyPassReverse "http://$JHUB_SERVER_HOST$JHUB_BASE_URL_PATH"
        #RequestHeader set SCRIPT_NAME "$JHUB_BASE_URL_PATH"
    </Location>

    # JHUB_END - OAuth server instance - Do not edit or remove this line!
.
wq
END
done


#-------------------------------------------------------------------------------
# JHub system integration

#Environment="OAUTH_CALLBACK_URL=http://localhost:8300/jhub/hub/oauth_callback"
#Environment="VIRES_USER_PERMISSION=swarm_vre"
#Environment="VIRES_ADMIN_PERMISSION=admin"
#Environment="VIRES_CLIENT_ID=$JHUB_CLIENT_ID"
#Environment="VIRES_CLIENT_SECRET=$JHUB_CLIENT_SECRET"
#Environment="VIRES_OAUTH_SERVER_URL=/oauth/"
#Environment="VIRES_OAUTH_DIRECT_SERVER_URL=http://$OAUTH_SERVER_HOST"
echo "/etc/systemd/system/${JHUB_SERVICE_NAME}.service"
cat > "/etc/systemd/system/${JHUB_SERVICE_NAME}.service" <<END
[Unit]
Description=JupyterHub server
After=network.target
Before=httpd.service

[Service]
PIDFile=/run/${JHUB_SERVICE_NAME}.pid
WorkingDirectory=${JHUB_WORK_DIR}
Environment="PATH=${P3_VENV_ROOT}/bin:/usr/bin/"
ExecStart=${P3_VENV_ROOT}/bin/jupyterhub \\
    --JupyterHub.authenticator_class='vires_jhub.authenticator.LocalViresOAuthenticator' \\
    --JupyterHub.pid_file="/run/${JHUB_SERVICE_NAME}.pid" \\
    --JupyterHub.bind_url="http://$JHUB_SERVER_HOST" \\
    --JupyterHub.base_url="$JHUB_BASE_URL_PATH" \\
    --ViresOAuthenticator.server_url="/oauth/" \\
    --ViresOAuthenticator.direct_server_url="http://$OAUTH_SERVER_HOST" \\
    --ViresOAuthenticator.client_id="$JHUB_CLIENT_ID" \\
    --ViresOAuthenticator.client_secret="$JHUB_CLIENT_SECRET" \\
    --ViresOAuthenticator.admin_permission="admin" \\
    --ViresOAuthenticator.user_permission="swarm_vre"

[Install]
WantedBy=multi-user.target
END

systemctl daemon-reload
systemctl enable "${JHUB_SERVICE_NAME}.service"
