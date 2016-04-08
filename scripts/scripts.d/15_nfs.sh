#!/bin/bash

#-------------------------------------------------------------------------------
#
# Project:          ViRES-DEMPO
# Purpose:          postgres/postgis - installation/configuration script
# Authors:          Christian Schiller
# Copyright(C):     2016 - EOX IT Services GmbH, Vienna, Austria
# Email:            christian dot schiller at eox dot at
# Date:             2016-01-30
# License:          MIT License (MIT)
#
#-------------------------------------------------------------------------------
# The MIT License (MIT):
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------



source `dirname $0`/../lib_logging.sh
source `dirname $0`/../lib_common.sh

###  TO BE RUN ONLY ON  SWARM-SERV1 !!!

info 'Installing NFS-Utils -> NFS-Server/NFS-Client ...'

# configuration switches
INSTALL_NFSSERVER=${INSTALL_SERVER:-NO}
INSTALL_NFSCLIENT=${INSTALL_CLIENT:-NO}
NFSSERVER_HOSTNAME=${NFSSERVER_HOSTNAME:-NO}
NFSCLIENT_HOSTNAME=${NFSCLIENT_HOSTNAME:-NO}


#source:  http://www.itzgeek.com/how-tos/linux/centos-how-tos/how-to-setup-nfs-server-on-centos-7-rhel-7-fedora-22.html

if [ "$INSTALL_NFSSERVER" = "YES" ] || [ "$INSTALL_NFSCLIENT" = "YES" ]
then
    yum install -y nfs-utils
fi



if [ "$INSTALL_NFSSERVER" = "YES" ]
then
    if [ ! -d $VIRES_DATADIR'/ftp_in' ]; then
        mkdir -p -m 0775  $VIRES_DATADIR'/ftp_in'
        chown $VIRES_USER:$VIRES_GROUP  $VIRES_DATADIR'/ftp_in'
    fi

    if [ ! -d $VIRES_DATADIR'/swarm' ]; then
        mkdir -p -m 0775  $VIRES_DATADIR'/swarm'
        chown $VIRES_USER:$VIRES_GROUP  $VIRES_DATADIR'/swarm'
    fi

    systemctl enable rpcbind
    systemctl start rpcbind

    systemctl enable nfs-server
    systemctl start nfs-server
    systemctl start rpc-statd

    # setup of exports
    grep -e -q "^${VIRES_DATADIR}" /etc/exports
if [ $? != 0 ]; then
cat <<EOF>  /etc/exports
${VIRES_DATADIR}  ${NFSCLIENT_HOSTNAME}(ro,async)
EOF

fi

    # nfs-export the filesystems
    exportfs -ra

fi


if [ "$INSTALL_NFSCLIENT" = "YES" ]
then
    systemctl enable rpcbind
    systemctl start rpcbind

    # local mount of external data-disk
    grep -e -q "${VIRES_DATADIR}" /etc/fstab
if [ $? != 0 ]; then
cat <<EOF>  /etc/fstab
## mount the swarm data storage (nfs-exported by swarm-serv1)
${NFSSERVER_HOSTNAME}:${VIRES_DATADIR}   ${VIRES_DATADIR}       nfs     defaults,nosuid,noexec,nodev  0 0
EOF

fi

    systemctl start rpc-statd

fi
