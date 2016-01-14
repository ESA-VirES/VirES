#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: VirES
# Purpose: VirES installation script - logging utilities
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

EXENAME=`basename -- "$0"`

# setup color output
if [ "$COLORS" != "OFF" ]
then
    RED="\\033[31m"
    GRE="\\033[32m"
    YEL="\\033[33m"
    BLU="\\033[34m"
    RES="\\033[m"
fi

tstamp()
{
    date --rfc-3339=seconds
}

error()
{
    echo -e "`tstamp` ${RED}ERROR: $EXENAME: $* ${RES}"
    exit 1
}

info()
{
    echo -e "`tstamp` ${YEL}INFO: $EXENAME: $* ${RES}"
}

warn()
{
    echo -e "`tstamp` ${RED}WARNING: $EXENAME: $* ${RES}"
}
