#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: VirES installation script - Python venv management
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
    VENV_ROOT="${1:-"$VENV_ROOT"}"
    ACTIVATE="$VENV_ROOT/bin/activate"
    is_venv_enabled_with_info || return 0
    if [ ! -f "$ACTIVATE" ]
    then
        info "python venv initialization ..."
        is_venv_root_set || return 1
        does_venv_root_exist || return 1
        python3 -m 'venv' "$VENV_ROOT"
    fi
    . "$ACTIVATE"
    info "python venv activated"
}

create_venv_root_if_missing() {
    [ -d "$VENV_ROOT" ] || {
        mkdir -m 0755 -p "$VENV_ROOT" && \
        info "venv directory $VENV_ROOT created"
    }
}

does_venv_root_exist() {
    if [ ! -d "$VENV_ROOT" ]
    then
        error "$VENV_ROOT directory does not exist!"
        return 1
    fi
}

is_venv_root_set() {
    if [ -z "$VENV_ROOT" ]
    then
        error "Missing the mandatory VENV_ROOT environment variable!"
        return 1
    fi
}

is_venv_enabled_with_info() {
    if is_venv_enabled
    then
        #info "venv is enabled"
        info "python venv directory: $VENV_ROOT"
        return 0
    else
        info "pyhton venv is disabled"
        return 1
    fi
}

is_venv_enabled() {
    [ "$ENABLE_VIRTUALENV" = "YES" ]
}
