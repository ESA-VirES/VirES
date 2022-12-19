#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: VirES installation script - Python package installation
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
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

create_and_enter_tmp_dir() {
    # the path is exported via TMP_DIR
    TMP_DIR=`mktemp -d -t 'vires.XXXXXXXXXXXX'`
    info "temporary directory $TMP_DIR created"
    trap 'rm -fR "'"$TMP_DIR"'" && info "temporary directory '"$TMP_DIR"' removed"' EXIT
    cd "$TMP_DIR"
}

find_and_enter_setup_dir() {
    _SETUP_FILE="`find -name setup.py -print -quit`"
    [ -n "$_SETUP_FILE" ] || error "setup.py not found!"
    cd "`dirname "$_SETUP_FILE"`"
    info "setup.py located in $PWD"
}

lookup_package() {
    ls $@ 2>/dev/null | sort | tail -n 1
}

uninstall_python_package() {
    [ -z "`pip freeze | grep "$1" `" ] || pip uninstall -y "$1"
}

link_file() {
    info "linking $1 to $2 ..."
    if [ -f "$2" -o -h "$2" ]
    then
        rm -fv "$2"
    fi
    ln -sf "$1" "$2"
}

required_variables()
{
    for __VARIABLE___
    do
        if [ -z "${!__VARIABLE___}" ]
        then
            error "Missing the required ${__VARIABLE___} variable!"
        fi
    done
}
