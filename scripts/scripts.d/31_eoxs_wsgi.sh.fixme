#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX server installation - WSGI daemon
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_apache.sh

info "Configuring WSGI daemon to be used by the EOxServer instances."

[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"
[ -z "$VIRES_GROUP" ] && error "Missing the required VIRES_GROUP variable!"

# number of EOxServer daemon processes
EOXS_WSGI_NPROC=${EOXS_WSGI_NPROC:-4}
# process group label
EOXS_WSGI_PROCESS_GROUP=${EOXS_WSGI_PROCESS_GROUP:-eoxs_ows}
# path to import script (http://modwsgi.readthedocs.io/en/develop/configuration-directives/WSGIImportScript.html)
EOXS_WSGI_IMPORT_SCRIPT=${EOXS_WSGI_IMPORT_SCRIPT:-wsgi.py}

WSGI_DAEMON="WSGIDaemonProcess $EOXS_WSGI_PROCESS_GROUP processes=$EOXS_WSGI_NPROC threads=1 user=$VIRES_USER group=$VIRES_GROUP maximum-requests=50000"
WSGI_IMPORTSCRIPT="WSGIImportScript $EOXS_WSGI_IMPORT_SCRIPT process-group=$EOXS_WSGI_PROCESS_GROUP application-group=%{GLOBAL}"
#TODO add: WSGIRestrictEmbedded On

CONF="`locate_wsgi_daemon $EOXS_WSGI_PROCESS_GROUP`"
if [ -z "$CONF" ]
then
    cat >> /etc/httpd/conf.d/wsgi.conf <<END

# WSGI process daemon used by the EOxServer
$WSGI_DAEMON
END
else
    ex "$CONF" <<END
g/^[ 	]*WSGIDaemonProcess[ 	]*$EOXS_WSGI_PROCESS_GROUP/d
g/^[ 	]*WSGIImportScript.*process-group=$EOXS_WSGI_PROCESS_GROUP/d
i
$WSGI_DAEMON
$WSGI_IMPORTSCRIPT
.
wq
END
fi
