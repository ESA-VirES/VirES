#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: final server restart
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "stoping httpd.service"
systemctl stop httpd.service


if [ "${CONFIGURE_WPSASYNC:-YES}" = "YES" ]
then
    [ -z "$VIRES_WPS_SERVICE_NAME" ] && error "Missing the required VIRES_WPS_SERVICE_NAME variable!"

    info "stopping ${VIRES_WPS_SERVICE_NAME}.service"
    systemctl stop "${VIRES_WPS_SERVICE_NAME}.service"
fi

if [ -n "${OAUTH_SERVICE_NAME}" ]
then
    info "stopping ${OAUTH_SERVICE_NAME}.service"
    systemctl stop "${OAUTH_SERVICE_NAME}.service"
fi

if [ "${CONFIGURE_WPSASYNC:-YES}" = "YES" ]
then
    info "starting ${VIRES_WPS_SERVICE_NAME}.service"
    systemctl start "${VIRES_WPS_SERVICE_NAME}.service"
fi

if [ -n "${OAUTH_SERVICE_NAME}" ]
then
    info "starting ${OAUTH_SERVICE_NAME}.service"
    systemctl start "${OAUTH_SERVICE_NAME}.service"
fi

info "starting httpd.service"
systemctl start httpd.service

systemctl status httpd.service

if [ "${CONFIGURE_WPSASYNC:-YES}" = "YES" ]
then
    systemctl status "${VIRES_WPS_SERVICE_NAME}.service"
fi

if [ -n "${OAUTH_SERVICE_NAME}" ]
then
    systemctl status "${OAUTH_SERVICE_NAME}.service"
fi
