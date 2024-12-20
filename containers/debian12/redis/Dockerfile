#-----------------------------------------------------------------------
#
#  VirES - Debian 12 Redis image
#
# Copyright (C) 2024 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE
FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

USER root

## PostgreSQL repositories
RUN apt-get -y update \
 && apt-get -y install redis-server \
 && apt-get -y clean


# setting volume data storage volume
ENV DATA_DIR="/var/lib/redis "
RUN mkdir -p "$DATA_DIR" && chown -R redis:redis "$DATA_DIR" && chmod 0700 "$DATA_DIR"
VOLUME "$DATA_DIR"


# logging volume
ENV LOG_DIR="/var/log/redis"
RUN mkdir -p "$LOG_DIR" && chown -R redis:redis "$LOG_DIR" && chmod 0700 "$LOG_DIR"
VOLUME "$LOG_DIR"


# entry point scripts
COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]

EXPOSE 6379

USER redis
