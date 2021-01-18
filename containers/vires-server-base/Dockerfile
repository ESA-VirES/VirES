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
    rpm -Uvh http://yum.packages.eox.at/el/eox-release-7-0.noarch.rpm &&\
    yum clean all

# install RPM packages 
RUN yum --assumeyes install install \
    unzip wget jq git \
    curl libcurl-devel \
    gcc-gfortran gcc-c++ \
    python3 python3-devel python3-pip \
    postgresql96-devel \
    gdal gdal-libs proj-epsg gdal-devel \
    mapserver mapserver-devel proj-devel libxml2-devel swig3 &&\
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
USER $USER
