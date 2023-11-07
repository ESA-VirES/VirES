#-----------------------------------------------------------------------
#
#  VirES - Debian 12 VirES common base Django sever image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE
ARG VIRES_ROOT="/srv/vires"

FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

ENV VIRES_ROOT="/srv/vires"
ENV VIRES_USER="vires"
ENV VIRES_GROUP="vires"
ENV VIRES_HOME="$VIRES_ROOT/home"
ENV VENV_ROOT="$VIRES_ROOT/venv"
ENV PIP_OPTIONS="--upgrade --upgrade-strategy=only-if-needed"

# extra repositories and system packages
RUN sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list' \
    && sh -c 'curl -S https://www.postgresql.org/media/keys/ACCC4CF8.asc > /etc/apt/trusted.gpg.d/pgdg.asc ' \
    && apt-get -y update \
    && apt-get -y install postgresql-client-12 libpq-dev \
    && apt-get -y install python3 python3-dev python3-pip python3-venv \
    && apt-get -y clean

ENV PATH="/usr/lib/postgresql/12/bin:$PATH"

# system setup
RUN mkdir -p "$VIRES_ROOT"
RUN groupadd -r "$VIRES_GROUP"
RUN useradd -r -M -g "$VIRES_GROUP" -d "$VIRES_HOME" -s /sbin/nologin -c "VirES system user" "$VIRES_USER"

# venv installation
RUN python3 -m 'venv' "$VENV_ROOT"
ENV PATH="$VENV_ROOT/bin:$PATH"

RUN pip3 install $PIP_OPTIONS pip
RUN pip3 install $PIP_OPTIONS wheel
RUN pip3 install $PIP_OPTIONS Jinja2
RUN pip3 install --force-reinstall --no-binary :all: psycopg2
RUN pip3 install $PIP_OPTIONS setproctitle
RUN pip3 install $PIP_OPTIONS gunicorn
RUN pip3 install $PIP_OPTIONS jsonschema
RUN pip3 install $PIP_OPTIONS pyyaml
RUN pip3 install $PIP_OPTIONS 'Django>=3.2,<4.0'
RUN pip3 install $PIP_OPTIONS django-requestlogging
RUN pip3 install $PIP_OPTIONS django-allauth
RUN pip3 install $PIP_OPTIONS django-countries

RUN pip3 cache purge

# install script rendering Jinja2 templates
COPY render_template.py $VENV_ROOT/bin/render_template
