#-----------------------------------------------------------------------
#
#  VirES - Debian 12 VirES base OAuth sever image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE

FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

ENV SERVER_NPROC=4
#ENV SERVER_NTHREAD=1 # fixed to 1, not configurable
ENV SERVER_PORT=8011

ENV VIRES_ASYNC_WPS_MAX_JOBS=64                                           
ENV VIRES_ASYNC_WPS_NPROC=2

ENV INSTANCE_NAME="swarm"
ENV LOG_DIR="/var/log/vires"
ENV INSTANCE_DIR="$VIRES_ROOT/$INSTANCE_NAME"
ENV STATIC_DIR="$VIRES_ROOT/${INSTANCE_NAME}_static"
ENV CONFIGURATION_TEMPLATES_DIR="$VIRES_ROOT/configuration_templates"

ENV VIRES_DATA_DIR="$VIRES_ROOT/data"
ENV VIRES_UPLOAD_DIR="$VIRES_ROOT/upload"
ENV VIRES_WPS_DIR="$VIRES_ROOT/wps"
ENV VIRES_PRODUCT_CACHE_DIR="$VIRES_ROOT/cache/products"
ENV VIRES_MODEL_CACHE_DIR="$VIRES_ROOT/cache/models"
ENV VIRES_SOCKET_DIR="$VIRES_ROOT/sockets"
ENV VIRES_ASYNC_WPS_SOCKET_FILE="$VIRES_SOCKET_DIR/async_wps.socket"

ENV INSTANCE_LOG="$LOG_DIR/$INSTANCE_NAME/server.log"
ENV ACCESS_LOG="$LOG_DIR/$INSTANCE_NAME/access.log"
ENV GUNICORN_ACCESS_LOG="$LOG_DIR/$INSTANCE_NAME/gunicorn_access.log"
ENV GUNICORN_ERROR_LOG="$LOG_DIR/$INSTANCE_NAME/gunicorn_error.log"

ENV PATH=$INSTANCE_DIR:$PATH

# copy configuration templates
COPY templates "$CONFIGURATION_TEMPLATES_DIR"

# copy data registration script
COPY register_products.sh  /usr/local/bin/register_products

# mount points for variaous instance directories
RUN mkdir -p "$LOG_DIR"
RUN mkdir -p "$INSTANCE_DIR"
RUN mkdir -p "$STATIC_DIR"
RUN mkdir -p "$VIRES_DATA_DIR"
RUN mkdir -p "$VIRES_UPLOAD_DIR"
RUN mkdir -p "$VIRES_WPS_DIR"
RUN mkdir -p "$VIRES_PRODUCT_CACHE_DIR"
RUN mkdir -p "$VIRES_MODEL_CACHE_DIR"
RUN mkdir -p "$VIRES_SOCKET_DIR"

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]

EXPOSE $SERVER_PORT

WORKDIR "$VIRES_HOME"
