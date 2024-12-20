#-----------------------------------------------------------------------
#
#  VirES - CentOS 7 PosgreSQL 12 image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE
FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

USER root

# PostgreSQL repositories
RUN yum install -y centos-release-scl-rh
RUN yum install -y epel-release
RUN rpm -Uvh https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Disable PGDG repositories not needed by the installation
run sed -i \
    -e 's/^\s*enabled\s*=.*$/enabled=0/' \
    -e '/\[pgdg-common\]/,/^gpgkey/s/^s*enabled\s*=.*$/enabled=1/' \
    -e '/\[pgdg12\]/,/^gpgkey/s/^s*enabled\s*=.*$/enabled=1/' \
    /etc/yum.repos.d/pgdg-redhat-all.repo

# PosgresSQL installation
RUN yum --assumeyes install postgresql12 postgresql12-server postgis31_12
RUN yum clean all

ENV PATH="$PATH:/usr/pgsql-12/bin/"

# setting volume at standard data path
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
