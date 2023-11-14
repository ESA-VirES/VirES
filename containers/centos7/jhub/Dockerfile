#-----------------------------------------------------------------------
#
# JupyterHub development image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE
FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

ENV SERVER_PORT=8012
ENV SWARM_SERVER_PORT=8011
ENV OAUTH_SERVER_PORT=8010

ENV USERS_DIR="$VIRES_ROOT/users"
ENV DATA_DIR="$VIRES_ROOT/data"
ENV LOG_DIR="/var/log/vires"

# copy configuration templates
ENV CONFIGURATION_TEMPLATES_DIR="$VIRES_ROOT/configuration_templates"
COPY templates "$CONFIGURATION_TEMPLATES_DIR"

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]

EXPOSE $SERVER_PORT

WORKDIR "$VIRES_ROOT"
