#-----------------------------------------------------------------------
#
#  VirES for Swarm - base server image
#
# Copyright (C) 2021 EOX IT Services GmbH
#-----------------------------------------------------------------------

FROM docker.io/library/centos:centos7
LABEL maintainer="EOX <martin.paces@eox.at>"

USER root

# enable rquired RPM repos
RUN yum --assumeyes install install epel-release &&\
    rpm -Uvh https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm &&\
    yum clean all

# install RPM packages
RUN yum --assumeyes install \
    unzip wget jq git \
    curl libcurl-devel \
    gcc \
    python3 python3-devel python3-pip \
    postgresql96-devel &&\
    yum clean all

ENV PATH="/usr/pgsql-9.6/bin:$PATH"

# initialize the users and directories
ENV HOMEDIR="/srv" \
    USER="vires" \
    GROUP="vires" \
    UID="1000" \
    GID="1000"

RUN groupadd --system --gid $GID vires &&\
    useradd --system --no-create-home --gid $GID --home-dir $HOMEDIR \
      --shell /sbin/nologin --comment "VirES system user" $USER &&\
    mkdir -p $HOMEDIR &&\
    chown -R $USER:$GROUP $HOMEDIR

WORKDIR $HOMEDIR

# setup virtual environment
ENV VENV="/srv/venv_oauth"
ENV PATH="$VENV/bin:$PATH"

RUN /usr/bin/python3 -m venv "$VENV" &&\
    pip install --upgrade "pip" &&\
    pip install --no-binary :all: "psycopg2" &&\
    pip install "setproctitle" &&\
    pip install "gunicorn" &&\
    pip install "Django>=2.2.2,<3.0" &&\
    pip install "django-requestlogging" &&\
    pip install "django-allauth==0.42.0" &&\
    pip install "django-countries" &&\
    pip install "django-oauth-toolkit" &&\
    rm -fR /root/.cache/ ./assets/

# VirES SW installation
ENV VERSION_VIRES_SERVER="master"

RUN pip install "git+https://github.com/ESA-VirES/VirES-Server@$VERSION_VIRES_SERVER#egg=vires-oauth&subdirectory=vires_oauth" &&\
    rm -fR /root/.cache/

# uninstall RPM development packages
RUN yum --assumeyes erase \
    gcc \
    libcurl-devel \
    python3-devel \
    postgresql96-devel &&\
    yum clean all

USER $USER
