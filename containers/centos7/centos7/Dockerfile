#-----------------------------------------------------------------------
#
#  CentOS 7 up-to-date base image
#
# Copyright (C) 2022 EOX IT Services GmbH
#-----------------------------------------------------------------------

FROM docker.io/centos:7
LABEL maintainer="EOX <martin.paces@eox.at>"

USER root

# update all installed packages
# ... see https://bugzilla.redhat.com/show_bug.cgi?id=1388570
RUN yum --assumeyes upgrade \
    && rm -f /etc/udev/hwdb.bin \
    && rm -rf /usr/lib/udev/hwdb.d/* \
    && yum clean all
