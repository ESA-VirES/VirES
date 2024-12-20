#-----------------------------------------------------------------------
#
#  VirES - CentOS 7 VirES common base Django sever image
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

# extra repositories
RUN yum install -y centos-release-scl-rh
RUN yum install -y epel-release
RUN rpm -Uvh https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Disable PGDG repositories not needed by the installation
run sed -i \
    -e 's/^\s*enabled\s*=.*$/enabled=0/' \
    -e '/\[pgdg-common\]/,/^gpgkey/s/^s*enabled\s*=.*$/enabled=1/' \
    -e '/\[pgdg12\]/,/^gpgkey/s/^s*enabled\s*=.*$/enabled=1/' \
    /etc/yum.repos.d/pgdg-redhat-all.repo

# system packages
RUN yum install -y postgresql12-libs postgresql12 postgresql12-devel
RUN yum install -y python3 python3-devel python3-pip
RUN yum install -y gcc gcc-c++
RUN yum clean all
ENV PATH="$PATH:/usr/pgsql-12/bin/"

# system setup
RUN mkdir -p "$VIRES_ROOT"
RUN groupadd -r "$VIRES_GROUP"
RUN useradd -r -M -g "$VIRES_GROUP" -d "$VIRES_HOME" -s /sbin/nologin -c "VirES system user" "$VIRES_USER"

# venv installation
RUN python3 -m 'venv' "$VENV_ROOT"
ENV PATH=$VENV_ROOT/bin/:$PATH

RUN pip3 install $PIP_OPTIONS pip
RUN pip3 install $PIP_OPTIONS Jinja2
# psycopg2<2.9 see https://github.com/ESA-VirES/VirES/issues/83
RUN pip3 install --force-reinstall --no-binary :all: 'psycopg2 < 2.9'
RUN pip3 install $PIP_OPTIONS setproctitle
RUN pip3 install $PIP_OPTIONS gunicorn
RUN pip3 install $PIP_OPTIONS jsonschema
RUN pip3 install $PIP_OPTIONS pyyaml
RUN pip3 install $PIP_OPTIONS 'Django>=2.2.2,<3.0'
RUN pip3 install $PIP_OPTIONS django-requestlogging
RUN pip3 install $PIP_OPTIONS django-allauth
RUN pip3 install $PIP_OPTIONS 'django-countries<7.5'

RUN pip3 cache purge

# install script rendering Jinja2 templates
COPY render_template.py $VENV_ROOT/bin/render_template
