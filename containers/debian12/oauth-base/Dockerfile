#-----------------------------------------------------------------------
#
#  VirES - Debian 12 VirES base OAuth server image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE

FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

RUN pip3 install $PIP_OPTIONS 'django-oauth-toolkit>=2.0'
RUN pip3 cache purge
