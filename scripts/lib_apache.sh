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

_locate_virtal_host_conf()
{
    _dupm_conf() {
        sed -n -e '/^\s*<VirtualHost/,/^\s*<\\VirtualHost/p' "$1"
    }

    _find_port() {
        _dupm_conf "$1" | sed -n -e 's/^\s*<VirtualHost\s\+\([^>]*\)\s*>/\1/p' \
        | sed 's/\s\+/ /g' | tr ' ' '\n' | sed 's/.*:\([0-9]\+\)$/\1/' \
        | sort -n | uniq | egrep "^$2\$"
    }
    _find_host() {
        _dupm_conf "$1" | sed -n -e 's/^\s*\(ServerName\|ServerAlias\)\s\+\([^#]*\)\s*\(#\|$\)/\2/p' \
        | sed 's/\s\+/ /g' | tr ' ' '\n' | sed 's/.*:\([0-9]\+\)$/\1/' \
        | sort -n | uniq | egrep "^`sed 's/\\./\\\\./g' <<< "$2"`\$"
    }

    _PORT=$1
    _HOST=$2
    _CONFS="/etc/httpd/conf/httpd.conf /etc/httpd/conf.d/*.conf"
    for _FILE in $_CONFS
    do
        [ -n "`_find_port "$_FILE" "$_PORT"`" ] || continue
        [ -z "$_HOST" ] || [ -n "`_find_host "$_FILE" "$_HOST"`" ] || continue
        echo $_FILE
    done
    return 1
}

locate_apache_conf()
{
    _PORT=${1:-80}
    _HOST=$2
    _locate_virtal_host_conf $_PORT $_HOST
}

locate_wsgi_socket_prefix_conf()
{
    _locate_conf '^\s*WSGISocketPrefix' || true
}

locate_wsgi_daemon()
{
    _locate_conf '^\s*WSGIDaemonProcess\s*'$1 || true
}

disable_virtual_host()
{
    ex "$1" <<END
/^\s*<VirtualHost/,/<\/VirtualHost>/s/^/#/
wq
END
}
