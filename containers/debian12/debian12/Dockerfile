#-----------------------------------------------------------------------
#
#  Debian 12 latest base image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

FROM docker.io/debian:12
LABEL maintainer="EOX <martin.paces@eox.at>"

USER root

# update all installed packages
# install common utilities
# clean the APT cache
RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get -y install ed vim-tiny less curl \
    && apt-get -y clean
