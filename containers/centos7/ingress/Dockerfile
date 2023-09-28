#-----------------------------------------------------------------------
#
#  VirES - CentOS 7 Apache web-server image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE
FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

USER root

RUN yum --assumeyes install httpd mod_ssl crypto-utils
RUN yum clean all

EXPOSE 80

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]
