#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: VirES installation script - Python virtualenv management
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

activate_virtualenv() {
    ACTIVATE="$VIRTUALENV_ROOT/bin/activate"
    is_virtualenv_enabled_with_info || return 0
    if [ ! -f "$ACTIVATE" ]
    then
        info "virtualenv initialization ..."
        is_virtualenv_root_set || return 1
        does_virtualenv_root_exist || return 1
        python -m 'virtualenv' "$VIRTUALENV_ROOT"
    fi
    . "$ACTIVATE"
    info "virtualenv activated"
}

does_virtualenv_root_exist() {
    if [ ! -d "$VIRTUALENV_ROOT" ]
    then
        error "$VIRTUALENV_ROOT directory does not exist!"
        return 1
    fi
}

is_virtualenv_root_set() {
    if [ -z "$VIRTUALENV_ROOT" ]
    then
        error "Missing the mandatory VIRTUALENV_ROOT environment variable!"
        return 1
    fi
}

is_virtualenv_enabled_with_info() {
    if is_virtualenv_enabled
    then
        info "virtualenv is enabled"
        info "virtualenv directory: $VIRTUALENV_ROOT"
        return 0
    else
        info "virtualenv is disabled"
        return 1
    fi
}

is_virtualenv_enabled() {
    [ "$ENABLE_VIRTUALENV" = "YES" ]
}
