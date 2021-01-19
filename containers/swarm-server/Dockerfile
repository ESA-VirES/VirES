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
RUN yum --assumeyes install epel-release &&\
    rpm -Uvh https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm &&\
    rpm -Uvh http://yum.packages.eox.at/el/eox-release-7-0.noarch.rpm &&\
    yum clean all

# install RPM packages
RUN yum --assumeyes install \
    unzip wget jq git \
    curl libcurl-devel \
    gcc gcc-gfortran gcc-c++ \
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

# install Swarm specific RPM
RUN yum --assumeyes install cdf qdipole qdipole-devel &&\
    yum clean all

COPY assets/matplotlibrc ./.config/matplotlib/
COPY assets/GDAL-1.11.4.tar.gz ./assets/
COPY assets/python-mapscript-7.4.3.tar.gz ./assets/

# setup virtual environment
ENV VENV="/srv/venv_swarm"
ENV PATH="$VENV/bin:$PATH"

RUN /usr/bin/python3 -m venv "$VENV" &&\
    pip install --upgrade "pip" &&\
    pip install "setuptools" &&\
    pip install ./assets/GDAL-1.11.4.tar.gz &&\
    pip install ./assets/python-mapscript-7.4.3.tar.gz &&\
    pip install --no-binary :all: "psycopg2" &&\
    pip install "setproctitle" &&\
    pip install "gunicorn" &&\
    pip install "Django>=2.2.2,<3.0" &&\
    pip install "django-requestlogging" &&\
    pip install "python-openid" &&\
    pip install "requests-oauthlib" &&\
    pip install "django-allauth" &&\
    pip install "django-countries" &&\
    pip install "msgpack-python" &&\
    pip install "numpy>=1.19.0,<1.20a0" &&\
    pip install "scipy>=1.5.0,<1.6a0" &&\
    pip install "matplotlib" &&\
    pip install "SpacePy" &&\
    pip install "apexpy>=1.0" &&\
    pip install "ply<4" &&\
    pip install "future" &&\
    pip install "pandas" &&\
    pip install "toolz==0.11.1" &&\
    pip install "dask==2.16.0" &&\
    pip install "git+https://github.com/klaundal/pyAMPS.git@0661c5d6faba0f0f0be567118ab4b0307e462d5e#pyamps" &&\
    rm -fR /root/.cache/ ./assets/

# VirES SW installation
ENV VERSION_EOXSERVER="release-1.0.0-rc18" \
    VERSION_EOXMAGMOD="0.9.7" \
    VERSION_VIRES_SERVER="master"

RUN pip install "git+https://github.com/EOxServer/eoxserver@$VERSION_EOXSERVER#egg=EOxServer" &&\
    pip install "https://github.com/DAMATS/WPS-Backend/archive/0.5.2.tar.gz" &&\
    pip install "https://github.com/ESA-VirES/MagneticModel/releases/download/eoxmagmod-$VERSION_EOXMAGMOD/eoxmagmod-$VERSION_EOXMAGMOD.tar.gz" &&\
    pip install "git+https://github.com/ESA-VirES/VirES-Server@$VERSION_VIRES_SERVER#egg=VirES_Server&subdirectory=vires" &&\
    pip install "git+https://github.com/ESA-VirES/VirES-Server@$VERSION_VIRES_SERVER#egg=EOxServer_allauth&subdirectory=eoxs_allauth" &&\
    rm -fR /root/.cache/

RUN yum --assumeyes erase \
    gcc gcc-gfortran gcc-c++ \
    libcurl-devel \
    python3-devel \
    postgresql96-devel \
    gdal-devel \
    mapserver-devel proj-devel libxml2-devel swig3 &&\
    yum clean all

USER $USER
