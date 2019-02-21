#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Dump orbit direction boundary points as tab separated file.
#
# Author: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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

from __future__ import print_function
import sys
from os.path import basename, exists
from numpy import asarray
from spacepy import pycdf

try:
    # Python 2
    from itertools import izip as zip
except ImportError:
    pass

FLAG_START = 1
FLAG_END = -1
FLAG_MIDDLE = 0
FLAG_ASCENDING = 1
FLAG_DESCENDING = -1
FLAG_UNDEFINED = 0


BT2STR = {
    FLAG_START: "BLOCK_START",
    FLAG_END: "BLOCK_END",
    FLAG_MIDDLE: "",
}

OD2STR = {
    FLAG_ASCENDING: "ASCENDING",
    FLAG_DESCENDING: "DESCENDING",
    FLAG_UNDEFINED: "UNDEFINED",
}

class CommandError(Exception):
    """ Command error exception. """
    pass



def main(filename):
    """ main subroutine. """
    with cdf_open(filename) as cdf:
        times = CdfTypeEpoch.decode(cdf.raw_var("Timestamp")[...])
        odirs = cdf["OrbitDirection"][...]
        btypes = cdf["BoundaryType"][...]

    print("Timestamp\tOrbitDirection\tBoundaryType")
    for time, odir, btype in zip(times, odirs, btypes):
        print("%s\t%s\t%s" % (time, OD2STR[odir], BT2STR[btype]))


def parse_inputs(argv):
    """ Parse input arguments. """
    try:
        input_ = argv[1]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return (input_,)


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <odb-file>" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Read Orbit Direction Boundary CDF file and dump it as"
        " text to standard output.",
    ]), file=file)


def cdf_open(filename, mode="r"):
    """ Open a new or existing  CDF file.
    Allowed modes are 'r' (read-only) and 'w' (read-write).
    A new CDF file is created if the 'w' mode is chosen and the file does not
    exist.
    The returned object is a context manager which can be used with the `with`
    command.

    NOTE: for the newly created CDF files the pycdf.CDF adds the '.cdf'
    extension to the filename if it does not end by this extension already.
    """
    if mode == "r":
        cdf = pycdf.CDF(filename)
    elif mode == "w":
        if exists(filename):
            cdf = pycdf.CDF(filename)
            cdf.readonly(False)
        else:
            pycdf.lib.set_backward(False) # produce CDF version 3
            cdf = pycdf.CDF(filename, "")
    else:
        raise ValueError("Invalid mode value %r!" % mode)
    return cdf


class CdfTypeEpoch(object):
    """ CDF Epoch Time type conversions. """
    CDF_EPOCH_1970 = 62167219200000.0

    @classmethod
    def decode(cls, cdf_raw_time):
        """ Convert CDF raw time to datetime64[ms]. """
        return asarray(
            cdf_raw_time - cls.CDF_EPOCH_1970
        ).astype('datetime64[ms]')

    @classmethod
    def encode(cls, time):
        """ Convert datetime64[ms] to CDF raw time. """
        time = asarray(time, 'datetime64[ms]').astype('int64')
        return time + cls.CDF_EPOCH_1970


if __name__ == "__main__":
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        usage(sys.argv[0])
