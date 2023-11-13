#-----------------------------------------------------------------------
#
#  VirES - Debian 12 VirES base Swarm server image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE

# -----------------------------------------------------------------------------

FROM $SOURCE_IMAGE as base
LABEL maintainer="EOX <martin.paces@eox.at>"

ENV GCC_MARCH="skylake"
ENV GCC_MTUNE="$GCC_MARCH"

ENV SERVER_NPROC=4
#ENV SERVER_NTHREAD=1 # fixed to 1, not configurable
ENV SERVER_PORT=8011

ENV VIRES_ASYNC_WPS_MAX_JOBS=64
ENV VIRES_ASYNC_WPS_NPROC=2

ENV INSTANCE_NAME="swarm"
ENV LOG_DIR="/var/log/vires"
ENV INSTANCE_DIR="$VIRES_ROOT/$INSTANCE_NAME"
ENV STATIC_DIR="$VIRES_ROOT/${INSTANCE_NAME}_static"

ENV VIRES_DATA_DIR="$VIRES_ROOT/data"
ENV VIRES_UPLOAD_DIR="$VIRES_ROOT/upload"
ENV VIRES_WPS_DIR="$VIRES_ROOT/wps"
ENV VIRES_PRODUCT_CACHE_DIR="$VIRES_ROOT/cache/products"
ENV VIRES_MODEL_CACHE_DIR="$VIRES_ROOT/cache/models"
ENV VIRES_SOCKET_DIR="$VIRES_ROOT/sockets"
ENV VIRES_ASYNC_WPS_SOCKET_FILE="$VIRES_SOCKET_DIR/async_wps.socket"

ENV INSTANCE_LOG="$LOG_DIR/$INSTANCE_NAME/server.log"
ENV ACCESS_LOG="$LOG_DIR/$INSTANCE_NAME/access.log"
ENV GUNICORN_ACCESS_LOG="$LOG_DIR/$INSTANCE_NAME/gunicorn_access.log"
ENV GUNICORN_ERROR_LOG="$LOG_DIR/$INSTANCE_NAME/gunicorn_error.log"

ENV PATH=$INSTANCE_DIR:$PATH

ENV LD_LIBRARY_PATH="$VENV_ROOT/lib"
ENV CDF_LIB="$VENV_ROOT/lib"

# mount points for variaous instance directories
RUN mkdir -p "$LOG_DIR"
RUN mkdir -p "$INSTANCE_DIR"
RUN mkdir -p "$STATIC_DIR"
RUN mkdir -p "$VIRES_DATA_DIR"
RUN mkdir -p "$VIRES_UPLOAD_DIR"
RUN mkdir -p "$VIRES_WPS_DIR"
RUN mkdir -p "$VIRES_PRODUCT_CACHE_DIR"
RUN mkdir -p "$VIRES_MODEL_CACHE_DIR"
RUN mkdir -p "$VIRES_SOCKET_DIR"

# install GDAL and Mapserver/Mapscript
RUN apt-get -y update \
 && apt-get -y install gdal-bin libgdal32 \
 && apt-get -y install python3-mapscript libmapserver2 \
 && apt-get -y clean

# mapserver - clone global installation to venv
RUN sh -c 'PYTHON_VERSION=$(python --version | sed -e '"'s/Python \([23]\.[0-9]\+\).*/\1/'"') \
  && TARGET_PATH="$VENV_ROOT/lib/python$PYTHON_VERSION/site-packages" \
  && SOURCE_PATH="/usr/lib/python3/dist-packages" \
  && cp -vlR "$SOURCE_PATH"/mapscript* "$TARGET_PATH"'

# matplotlib configuration
RUN mkdir -p "$VIRES_HOME/.config/matplotlib/" \
  && sh -c "echo 'backend:Agg' > '$VIRES_HOME/.config/matplotlib/matplotlibrc'"

# web-client installation script
COPY install_client.sh $VENV_ROOT/bin/install_client

# data registration script
COPY register_products.sh  /usr/local/bin/register_products

# -----------------------------------------------------------------------------

FROM base as build
LABEL maintainer="EOX <martin.paces@eox.at>"

RUN apt-get -y update \
 && apt-get -y install git \
 && apt-get -y install libgdal-dev \
 && apt-get -y install python3-dev \
 && apt-get -y install make g++ gfortran \
 && apt-get -y clean

# prepare local build environment
ENV BUILD_DIR="$VIRES_ROOT/build"
RUN mkdir -p "$BUILD_DIR"

# Get libCDF and QDipole sources
RUN sh -c 'cd "$BUILD_DIR" \
  && TAG=cdf-3.9.0.a \
  && curl -sSL "https://github.com/ESA-VirES/MagneticModel/archive/refs/tags/$TAG.tar.gz" | tar xvz \
  && mv -v MagneticModel-$TAG MagneticModel'

# Build and install QDipole
RUN sh -c 'cd "$BUILD_DIR/MagneticModel/qdipole" \
  && CFLAGS="-O3 -march=${GCC_MARCH} -mtune=${GCC_MTUNE} -ftree-vectorize" \
  && ./configure --prefix="$VENV_ROOT" CFLAGS="$CFLAGS" \
  && make all install clean'

# Build and install QDipole
RUN sh -c 'cd "$BUILD_DIR/MagneticModel/libcdf" \
  && make all install clean INSTALLDIR="$VENV_ROOT"'

RUN pip3 install $PIP_OPTIONS numpy
RUN pip3 install $PIP_OPTIONS scipy
RUN pip3 install $PIP_OPTIONS msgpack-python
RUN pip3 install $PIP_OPTIONS 'ply<4'
# See https://github.com/spacepy/spacepy/issues/717
# To be reviewed once SpacePy v0.5 is released.
RUN pip3 install $PIP_OPTIONS --no-build-isolation 'SpacePy<0.5'

# EOxServer dependencies
RUN pip3 install $PIP_OPTIONS "GDAL==$(gdal-config --version)"
RUN pip3 install $PIP_OPTIONS python-dateutil
RUN pip3 install $PIP_OPTIONS 'django-model-utils<5.0.0'
RUN pip3 install $PIP_OPTIONS 'django-utils-six==2.0'
RUN pip3 install $PIP_OPTIONS django-prometheus
RUN pip3 install $PIP_OPTIONS tzdata
RUN pip3 install $PIP_OPTIONS zipstream
RUN pip3 install $PIP_OPTIONS lxml
RUN pip3 install $PIP_OPTIONS 'pycql==0.0.8'
RUN pip3 install $PIP_OPTIONS 'pyows>=0.2.6'
RUN pip3 install $PIP_OPTIONS 'python-keystoneclient<6.0.0'
RUN pip3 install $PIP_OPTIONS 'python-swiftclient<5.0.0'
RUN pip3 install $PIP_OPTIONS jsonfield

# AMPS model
RUN pip3 install $PIP_OPTIONS 'pyamps==1.5.2'

# -----------------------------------------------------------------------------

FROM base AS final
LABEL maintainer="EOX <martin.paces@eox.at>"

# Copy new files and directories from the build stage image
RUN --mount=type=bind,from=build,source="$VENV_ROOT",target="$VIRES_ROOT/build" bash -x -c '\
    comm -1 -3 <(cd "$VENV_ROOT" ; find . | sort) <(cd "$VIRES_ROOT/build" ; find . | sort) | \
    (cd "$VIRES_ROOT/build" ; tar -cT -) | (cd "$VENV_ROOT" ; tar xv)'
