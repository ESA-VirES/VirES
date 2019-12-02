#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Vagrant OAuth instance initialization
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python3_venv.sh
. `dirname $0`/../lib_oauth.sh

info "Initializing JHub OAuth app ... "
JHUB_SERVICE_NAME="jupyterhub"
JHUB_SERVICE_FILE="/etc/systemd/system/${JHUB_SERVICE_NAME}.service"
JHUB_CALLBACK_URL="http://localhost:8300/jhub/hub/oauth_callback"
JHUB_CLIENT_ID="vZuNuWKsT4FDl6XcHlUQJdD5idXcsTdCdgIr9fGh"
JHUB_CLIENT_SECRET="`base64 /dev/urandom | tr -d '+/\n' | head -c '128'`"

. `dirname $0`/../lib_python3_venv.sh
. `dirname $0`/../lib_oauth.sh
activate_venv
set_instance_variables
required_variables MNGCMD

# JHub OAuth client initialization
python "$MNGCMD" auth_import_apps << END
[
  {
    "name": "VRE - JupyterHub - Vagrant",
    "client_id": "$JHUB_CLIENT_ID",
    "client_secret": "$JHUB_CLIENT_SECRET",
    "redirect_uris": [
        "$JHUB_CALLBACK_URL"
    ],
    "client_type": "confidential",
    "authorization_grant_type": "authorization-code",
    "skip_authorization": false
  }
]
END

# JHub OAuth service configuration
[ -f "$JHUB_SERVICE_FILE" ] && ex "$JHUB_SERVICE_FILE" <<END
/--ViresOAuthenticator.client_id=/d
/--ViresOAuthenticator.client_secret=/d
i
    --ViresOAuthenticator.client_id="$JHUB_CLIENT_ID" \\\\
    --ViresOAuthenticator.client_secret="$JHUB_CLIENT_SECRET" \\\\
.
wq
END
