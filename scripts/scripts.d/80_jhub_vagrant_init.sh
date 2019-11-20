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

info "Configuring Vagrant OAuth instance ... "

# TODO: DRY - common JHub configuration
JHUB_CALLBACK_URL="http://localhost:8300/jhub/hub/oauth_callback"
JHUB_CLIENT_ID="vZuNuWKsT4FDl6XcHlUQJdD5idXcsTdCdgIr9fGh"
JHUB_CLIENT_SECRET="vm5ucD1dsHIXOfOwAWCGFR9zfKO8P4sJDsvJ45SzxY2je4dDfJdKpFJGtFA9ZlBI7RgNY2gbQqK9toM9Q7YA9Kv3HDSOLXkqcQ9me9Ww4rSRAdnhWGMP4iCpJ05UfNDN"

activate_venv
set_instance_variables
required_variables MNGCMD

# initial user (vagrant/vagrant)
python "$MNGCMD" auth_import_users << END
[
  {
    "username": "vagrant",
    "password": "pbkdf2_sha256\$150000\$Hpjuirbl8DfK\$8w2VtP5bw09Mtlgvf0Tsiu852cRhkTjaHpEmXw6ErXw=",
    "is_active": true,
    "date_joined": "2016-05-01T00:00:00.000000+00:00",
    "last_login": "2016-05-01T00:00:00.000000+00:00",
    "email": "vagrant@eox.at",
    "groups": [
      "admin",
      "default",
      "swarm_vre"
    ],
    "user_profile": {
      "country": "AT"
    },
    "email_addresses": [
      {
        "email": "vagrant@eox.at",
        "verified": false,
        "primary": true
      }
    ]
  }
]
END

# JHub OAuth client initialization
python "$MNGCMD" loaddata --format=json - << END
[
  {
    "model": "oauth2_provider.application",
    "pk": 1,
    "fields": {
      "client_id": "$JHUB_CLIENT_ID",
      "user": 1,
      "redirect_uris": "$JHUB_CALLBACK_URL",
      "client_type": "confidential",
      "authorization_grant_type": "authorization-code",
      "client_secret": "$JHUB_CLIENT_SECRET",
      "name": "VRE - JupyterHub - Vagrant",
      "skip_authorization": false,
      "created": "2016-05-01T00:00:00.000Z",
      "updated": "2016-05-01T00:00:00.000Z"
    }
  }
]
END
