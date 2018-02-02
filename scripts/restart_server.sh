#!/bin/bash

. `dirname $0`/lib_common.sh
. `dirname $0`/lib_logging.sh

set -x
eoxs_wps_async_enabled() {
    [ "${CONFIGURE_WPSASYNC:-YES}" = "YES" -a -n "$VIRES_WPS_SERVICE_NAME" ]
}

sudo systemctl stop httpd.service
eoxs_wps_async_enabled && sudo systemctl stop "${VIRES_WPS_SERVICE_NAME}.service"
eoxs_wps_async_enabled && sudo systemctl start "${VIRES_WPS_SERVICE_NAME}.service"
sudo systemctl start httpd.service
sudo systemctl status httpd.service
eoxs_wps_async_enabled && sleep 5 && sudo systemctl status "${VIRES_WPS_SERVICE_NAME}.service"
