#-----------------------------------------------------------------------
#
#  VirES - CentOS 7 VirES base OAuth sever image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE

FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

ENV SERVER_NPROC=2
ENV SERVER_NTHREAD=2
ENV SERVER_PORT=8010

ENV INSTANCE_NAME="oauth"
ENV LOG_DIR="/var/log/vires"
ENV INSTANCE_DIR="$VIRES_ROOT/$INSTANCE_NAME"
ENV STATIC_DIR="$VIRES_ROOT/${INSTANCE_NAME}_static"
ENV CONFIGURATION_TEMPLATES_DIR="$VIRES_ROOT/configuration_templates"

ENV INSTANCE_LOG="$LOG_DIR/$INSTANCE_NAME/server.log"
ENV ACCESS_LOG="$LOG_DIR/$INSTANCE_NAME/access.log"
ENV GUNICORN_ACCESS_LOG="$LOG_DIR/$INSTANCE_NAME/gunicorn_access.log"
ENV GUNICORN_ERROR_LOG="$LOG_DIR/$INSTANCE_NAME/gunicorn_error.log"

ENV PATH=$INSTANCE_DIR:$PATH

# copy configuration templates
COPY templates "$CONFIGURATION_TEMPLATES_DIR"

# mount points for variaous instance directories
RUN mkdir -p "$LOG_DIR"
RUN mkdir -p "$INSTANCE_DIR"
RUN mkdir -p "$STATIC_DIR"

# mount point for developemnt sources
RUN mkdir -p "/usr/local/vires"

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]

EXPOSE $SERVER_PORT

WORKDIR "$VIRES_HOME"
