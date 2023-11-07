#-----------------------------------------------------------------------
#
#  VirES - Debian 12 PosgreSQL 12 image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE
FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

USER root

## PostgreSQL repositories
RUN sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list' \
    && sh -c 'curl -S https://www.postgresql.org/media/keys/ACCC4CF8.asc > /etc/apt/trusted.gpg.d/pgdg.asc ' \
    && apt-get -y update \
    && apt-get -y install postgresql-12 postgresql-12-postgis-3 \
    && apt-get -y clean

ENV PATH="/usr/lib/postgresql/12/bin:$PATH"


# setting volume at standard data path
RUN rm -fR du /var/lib/postgresql/12/main
ENV PGDATA="/var/lib/postgresql/data"
RUN mkdir -p "$PGDATA" && chown -R postgres:postgres "$PGDATA" && chmod 0700 "$PGDATA"
VOLUME "$PGDATA"


# logging volume
ENV LOG_DIR="/var/log/postgresql"
RUN mkdir -p "$LOG_DIR" && chown -R postgres:postgres "$LOG_DIR" && chmod 0700 "$LOG_DIR"
VOLUME "$LOG_DIR"

# helper scripts
COPY create_db.sh /usr/local/bin/create_db
COPY drop_db.sh /usr/local/bin/drop_db
COPY drop_db_user.sh /usr/local/bin/drop_db_user
COPY get_random_db_creadentials.sh /usr/local/bin/get_random_db_creadentials
COPY list_dbs.sh /usr/local/bin/list_dbs
COPY list_db_users.sh /usr/local/bin/list_db_users

# entry point scripts
COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]

# See https://www.postgresql.org/docs/12/server-shutdown.html for more details
# about available PostgreSQL server shutdown signals.
#
# See also https://www.postgresql.org/docs/12/server-start.html for 
# justification of using SIGINT termination.

STOPSIGNAL SIGINT
#
# Consider using "--stop-timeout" (or equivalent) for controlling how long
#  to wait between sending the defined STOPSIGNAL and sending SIGKILL
#  (which is likely to cause data corruption).
#
# The usual 10 seconds default may not be long enough.
# See https://www.postgresql.org/docs/12/server-start.html notes

EXPOSE 5432

USER postgres
