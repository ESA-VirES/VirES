#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: VirES installation script - common Apache server configuration
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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

# locate Apache configuration files
# configured for the given port number 

_locate_conf()
{
    _CONFS="/etc/httpd/conf/httpd.conf /etc/httpd/conf.d/*.conf"
    for _F_ in $_CONFS
    do
        if [ 0 -lt `grep -c "$1" "$_F_"` ]
        then
            echo "$_F_"
            return 0
        fi
    done
    return 1 
}

locate_apache_conf()
{
    _locate_conf '^[ 	]*<VirtualHost[ 	]*_default_:'${1:-80}'>' || \
    _locate_conf '^[ 	]*<VirtualHost[ 	]*\*:'${1:-80}'>' || true
}

locate_wsgi_socket_prefix_conf()
{
    _locate_conf '^[ 	]*WSGISocketPrefix' || true
}

locate_wsgi_daemon()
{
    _locate_conf '^[ 	]*WSGIDaemonProcess[ 	]*'$1 || true
}

disable_virtual_host()
{
    ex "$1" <<END
/^[ 	]*<VirtualHost/,/<\/VirtualHost>/s/^/#/
wq
END
}
