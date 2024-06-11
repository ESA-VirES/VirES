#-----------------------------------------------------------------------
#
#  VirES - CentOS 7 VirES base Swarm server image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE

FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

# EOX RPM repository
RUN rpm -Uvh http://yum.packages.eox.at/el/eox-release-7-0.noarch.rpm
COPY eox-package-maintainers.gpg /etc/pki/rpm-gpg/eox-package-maintainers.gpg
RUN rpm --import /etc/pki/rpm-gpg/eox-package-maintainers.gpg

# system packages
RUN yum install -y git
RUN yum install -y gcc-gfortran
RUN yum install -y devtoolset-11
RUN yum install -y mapserver-devel gdal-devel proj-devel libxml2-devel swig3
RUN yum install -y cdf
RUN yum install -y qdipole qdipole-devel
RUN yum clean all

# local build packakes
ENV BUILD_DIR="$VIRES_ROOT/build"
RUN mkdir -p "$BUILD_DIR"
COPY GDAL-1.11.4.tar.gz "$BUILD_DIR/gdal.tar.gz"
COPY mapscript-7.4.31.tar.gz "$BUILD_DIR/mapscript.tar.gz"
COPY amps-requirements.txt "$BUILD_DIR/amps-requirements.txt"

# GDAL Python bindings installation requires numpy
RUN pip3 install $PIP_OPTIONS 'numpy>=1.19.0,<1.20a0'
# Current version of GDAL requires setuptools<58 (2to3 removed in 58.0.0)
RUN pip3 install $PIP_OPTIONS "setuptools<58"
RUN pip3 install $PIP_OPTIONS "$BUILD_DIR/gdal.tar.gz"
RUN pip3 install $PIP_OPTIONS "$BUILD_DIR/mapscript.tar.gz"
RUN pip3 install $PIP_OPTIONS msgpack-python
RUN pip3 install $PIP_OPTIONS 'scipy>=1.5.0,<1.6a0'
RUN pip3 install $PIP_OPTIONS 'ply<4'
RUN pip3 install $PIP_OPTIONS SpacePy

# EOxServer dependencies
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
RUN pip3 install $PIP_OPTIONS -r "$BUILD_DIR/amps-requirements.txt"
#RUN pip3 install $PIP_OPTIONS 'git+https://github.com/klaundal/pyAMPS.git@1.6#pyamps'
RUN pip3 install $PIP_OPTIONS 'git+https://github.com/pacesm/pyAMPS.git@1.6_fixed#pyamps'
RUN pip3 cache purge

# clear build packages
RUN rm -fR "$BUILD_DIR"
ENV BUILD_DIR=

# matplotlib configuration
RUN mkdir -p "$VIRES_HOME/.config/matplotlib/" \
  && sh -c "echo 'backend:Agg' > '$VIRES_HOME/.config/matplotlib/matplotlibrc'" \
  && chown vires:vires -R "$VIRES_HOME"

# web-client installation script
COPY install_client.sh $VENV_ROOT/bin/install_client
