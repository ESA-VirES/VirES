#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: VirES installation script - Python 3 venv management
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

activate_venv() {
    ACTIVATE="$P3_VENV_ROOT/bin/activate"
    is_venv_enabled_with_info || return 0
    if [ ! -f "$ACTIVATE" ]
    then
        info "python3 venv initialization ..."
        is_venv_root_set || return 1
        does_venv_root_exist || return 1
        python3 -m 'venv' "$P3_VENV_ROOT"
    fi
    . "$ACTIVATE"
    info "python3 venv activated"
}

does_venv_root_exist() {
    if [ ! -d "$P3_VENV_ROOT" ]
    then
        error "$P3_VENV_ROOT directory does not exist!"
        return 1
    fi
}

is_venv_root_set() {
    if [ -z "$P3_VENV_ROOT" ]
    then
        error "Missing the mandatory P3_VENV_ROOT environment variable!"
        return 1
    fi
}

is_venv_enabled_with_info() {
    if is_venv_enabled
    then
        #info "venv is enabled"
        info "python3 venv directory: $P3_VENV_ROOT"
        return 0
    else
        info "pyhton3 venv is disabled"
        return 1
    fi
}

is_venv_enabled() {
    [ "$ENABLE_VIRTUALENV" = "YES" ]
}
