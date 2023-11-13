#-----------------------------------------------------------------------
#
#  VirES - Debian 12 VirES base OAuth sever image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE

FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

RUN apt-get -y update \
 && apt-get -y install gcc python3-dev \
 && apt-get -y clean

# copy configuration templates
ENV CONFIGURATION_TEMPLATES_DIR="$VIRES_ROOT/configuration_templates"
COPY templates "$CONFIGURATION_TEMPLATES_DIR"

# create the VirES user and group
RUN groupadd -r "$VIRES_GROUP"
RUN useradd -r -M -g "$VIRES_GROUP" -d "$VIRES_HOME" -s /sbin/nologin -c "VirES system user" "$VIRES_USER"

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]

EXPOSE $SERVER_PORT

WORKDIR "$VIRES_HOME"
