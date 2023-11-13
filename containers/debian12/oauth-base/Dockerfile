#-----------------------------------------------------------------------
#
#  VirES - Debian 12 VirES base OAuth server image
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

ENV INSTANCE_LOG="$LOG_DIR/$INSTANCE_NAME/server.log"
ENV ACCESS_LOG="$LOG_DIR/$INSTANCE_NAME/access.log"
ENV GUNICORN_ACCESS_LOG="$LOG_DIR/$INSTANCE_NAME/gunicorn_access.log"
ENV GUNICORN_ERROR_LOG="$LOG_DIR/$INSTANCE_NAME/gunicorn_error.log"

ENV PATH=$INSTANCE_DIR:$PATH

# mount points for variaous instance directories
RUN mkdir -p "$LOG_DIR"
RUN mkdir -p "$INSTANCE_DIR"
RUN mkdir -p "$STATIC_DIR"

# extra pip pacakges
RUN pip3 install $PIP_OPTIONS 'django-oauth-toolkit>=2.0'
RUN pip3 cache purge && rm -fR "/root/.cache"

# FIXME: find a better way to strip the cached compiled Python code
RUN sh -c 'find "$VENV_ROOT" -type d -name __pycache__ -exec rm -fR {} \; 2>/dev/null || true'
