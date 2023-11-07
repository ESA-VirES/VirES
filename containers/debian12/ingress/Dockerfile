#-----------------------------------------------------------------------
#
#  VirES - Debian 12 Apache web-server image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE
FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

USER root

RUN apt-get -y update \
    && apt-get -y install apache2 \
    && apt-get -y clean

RUN rm -fv /etc/apache2/sites-enabled/000-default.conf
RUN a2enmod proxy \
 && a2enmod proxy_http \
 && a2enmod headers

EXPOSE 80

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]
