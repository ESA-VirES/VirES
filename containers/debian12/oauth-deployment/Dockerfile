
#-----------------------------------------------------------------------
#
#  VirES - Debian 12 VirES development OAuth sever image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE

# -----------------------------------------------------------------------------

FROM $SOURCE_IMAGE AS build
LABEL maintainer="EOX <martin.paces@eox.at>"

ARG OAUTH_GIT_REFERENCE

# prepare local build environment
#ENV BUILD_DIR="$VIRES_ROOT/build"
#RUN mkdir -p "$BUILD_DIR"

RUN apt-get -y update \
 && apt-get -y install git \
 && apt-get -y clean

# install deplyment packages from git repository
RUN pip install "vires-oauth @ git+https://github.com/ESA-VirES/VirES-Server.git@${OAUTH_GIT_REFERENCE:-staging}#subdirectory=vires_oauth"
RUN pip3 cache purge && rm -fR "/root/.cache"

# FIXME: find a better way to strip the cached compiled Python code
RUN sh -c 'find "$VENV_ROOT" -type d -name __pycache__ -exec rm -fR {} \; 2>/dev/null || true'

# -----------------------------------------------------------------------------

FROM $SOURCE_IMAGE

# Copy new files and directories from the build stage image
RUN --mount=type=bind,from=build,source="$VENV_ROOT",target="$VIRES_ROOT/build" bash -x -c '\
    comm -1 -3 <(cd "$VENV_ROOT" ; find . | sort) <(cd "$VIRES_ROOT/build" ; find . | sort) | \
    (cd "$VIRES_ROOT/build" ; tar -cT -) | (cd "$VENV_ROOT" ; tar xv)'

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]

EXPOSE $SERVER_PORT

WORKDIR "$VIRES_HOME"
