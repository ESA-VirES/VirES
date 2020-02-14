#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: final server restart
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh


list_services() {

    echo "httpd.service"

    if [ -n "`systemctl -a | grep 'jupyterhub\.service'`" ]
    then
        echo "jupyterhub.service"
    fi

    if [ -n "${OAUTH_SERVICE_NAME}" ]
    then
        echo "${OAUTH_SERVICE_NAME}.service"
    fi

    if [ -n "${VIRES_SERVICE_NAME}" ]
    then
        echo "${VIRES_SERVICE_NAME}.service"
    fi

    #if [ "${CONFIGURE_WPSASYNC:-YES}" = "YES" ]
    #then
    #    [ -z "$VIRES_WPS_SERVICE_NAME" ] && error "Missing the required VIRES_WPS_SERVICE_NAME variable!"
    #    echo "${VIRES_WPS_SERVICE_NAME}.service"
    #fi
}

list_services
for SERVICE in `list_services`
do
    info "stopping $SERVICE ..."
    systemctl stop $SERVICE
done

info "reloading daemons' configuration ..."
systemctl daemon-reload

for SERVICE in `list_services | tac`
do
    info "starting $SERVICE ..."
    systemctl start $SERVICE
done

for SERVICE in `list_services`
do
    systemctl status $SERVICE
done
