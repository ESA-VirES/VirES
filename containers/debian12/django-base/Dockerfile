#-----------------------------------------------------------------------
#
#  VirES - Debian 12 VirES common base Django sever image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE
ARG VIRES_ROOT="/srv/vires"

# -----------------------------------------------------------------------------

FROM $SOURCE_IMAGE AS base
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
 && apt-get -y install libpq-dev \
 && apt-get -y install python3 \
 && apt-get -y clean

# && apt-get -y install postgresql-client-12 \

# system setup
RUN mkdir -p "$VIRES_ROOT"

ENV PATH="/usr/lib/postgresql/12/bin:$PATH"
ENV PATH="$VENV_ROOT/bin:$PATH"

# -----------------------------------------------------------------------------

FROM base AS build

RUN apt-get -y update \
 && apt-get -y install libpq-dev \
 && apt-get -y install python3-dev python3-pip python3-venv \
 && apt-get -y clean

# venv installation
RUN python3 -m 'venv' "$VENV_ROOT"

RUN pip3 install $PIP_OPTIONS pip
RUN pip3 install $PIP_OPTIONS wheel
RUN pip3 install $PIP_OPTIONS Jinja2
RUN pip3 install --force-reinstall --no-binary :all: psycopg2
RUN pip3 install $PIP_OPTIONS setproctitle
#RUN pip3 install $PIP_OPTIONS gunicorn
RUN pip3 install $PIP_OPTIONS 'gunicorn<22' # 22.0.0 regression see https://github.com/benoitc/gunicorn/pull/3192
RUN pip3 install $PIP_OPTIONS jsonschema
RUN pip3 install $PIP_OPTIONS pyyaml
RUN pip3 install $PIP_OPTIONS 'Django>=3.2,<4.0'
RUN pip3 install $PIP_OPTIONS django-requestlogging
RUN pip3 install $PIP_OPTIONS django-allauth
RUN pip3 install $PIP_OPTIONS django-countries

RUN pip3 cache purge && rm -fR "/root/.cache"

# FIXME: find a better way to strip the cached compiled Python code
RUN sh -c 'find "$VENV_ROOT" -type d -name __pycache__ -exec rm -fR {} \; 2>/dev/null || true'

# install script rendering Jinja2 templates
COPY render_template.py $VENV_ROOT/bin/render_template

# -----------------------------------------------------------------------------

FROM base AS final

COPY --from=build "$VIRES_ROOT" "$VIRES_ROOT"
