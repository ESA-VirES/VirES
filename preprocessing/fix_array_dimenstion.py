#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# This script fixes the incorrect dimension of the EIFx_LP product U_orbit
# variable.
#
# Author: Martin Paces <martin.paces@eox.at>
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

from __future__ import print_function
import sys
import ctypes
from datetime import datetime, timedelta
from os import rename, remove
from os.path import basename, exists
import spacepy
from spacepy import pycdf

MAX_TIME_SELECTION = timedelta(days=25*365.25) # max. time selection of ~25 years

GZIP_COMPRESSION = pycdf.const.GZIP_COMPRESSION
GZIP_COMPRESSION_LEVEL1 = ctypes.c_long(1)
GZIP_COMPRESSION_LEVEL9 = ctypes.c_long(9)
CDF_CREATOR = "EOX:fix_array_dimenstion.py [%s-%s, libcdf-%s]" % (
    spacepy.__name__, spacepy.__version__,
    "%s.%s.%s-%s" % tuple(
        v if isinstance(v, int) else v.decode('ascii')
        for v in pycdf.lib.version
    )
)

class CommandError(Exception):
    """ Command error exception. """
    pass


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <input> [<output>]" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  This script fixes the wrong Nx1 dimension of scalar variables",
        "  observed in some Swarm products. The scripts detect whether the",
        "  input file needs to be fixed otherwise nothing is performed.",
        "  It is safe when the input and output are the same files.",
        "  If the output file is not provided the script rewrites the input ",
        "  file.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    argv = argv + [None]
    try:
        input_ = argv[1]
        output = argv[2]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return input_, output or input_


def main(filename_input, filename_output):
    """ main subroutine """
    filename_tmp = filename_output + ".tmp.cdf"

    if exists(filename_tmp):
        remove(filename_tmp)

    try:
        squeeze_dimensions(filename_input, filename_tmp)
        if exists(filename_tmp):
            print("%s -> %s" % (filename_input, filename_output))
            rename(filename_tmp, filename_output)
        else:
            print("%s skipped" % filename_input)
    finally:
        if exists(filename_tmp):
            remove(filename_tmp)

def squeeze_dimensions(filename_input, filename_output):
    """ Squeeze dimension of Nx1 scalar arrays."""
    with cdf_open(filename_input) as cdf_src:
        variables = find_nx1_variables(cdf_src)
        if variables:
            with cdf_open(filename_output, "w") as cdf_dst:
                copy_squeezed(cdf_dst, cdf_src, variables)


def find_nx1_variables(cdf):
    """ Find variables with the squeezable Nx1 dimension. """
    variables = []
    for variable in cdf:
        shape = cdf[variable].shape
        if shape and shape[1:] == (1,):
            variables.append(variable)
    return variables


def copy_squeezed(cdf_dst, cdf_src, squeezed_variables):
    """ Copy squeezed content from the source to the destination CDF file. """
    squeezed_variables = set(squeezed_variables)
    _copy_attributes(cdf_dst, cdf_src)
    _update_creator(cdf_dst)
    for variable in cdf_src:
        if variable in squeezed_variables:
            _copy_squeezed_nx1(cdf_dst, cdf_src, variable)
        else:
            _copy_variable(cdf_dst, cdf_src, variable)


def _update_creator(cdf):
    cdf.attrs.update({
        "CREATOR": CDF_CREATOR,
        "CREATED": (
            datetime.utcnow().replace(microsecond=0)
        ).isoformat() + "Z",
    })


def _copy_variable(cdf_dst, cdf_src, variable):
    _set_variable(cdf_dst, cdf_src, variable, cdf_src.raw_var(variable)[...])


def _copy_squeezed_nx1(cdf_dst, cdf_src, variable):
    _set_variable(cdf_dst, cdf_src, variable, cdf_src.raw_var(variable)[:, 0])


def _set_variable(cdf_dst, cdf_src, variable, data):
    raw_var = cdf_src.raw_var(variable)
    cdf_dst.new(
        variable, data, raw_var.type(), dims=data.shape[1:],
        compress=GZIP_COMPRESSION, compress_param=GZIP_COMPRESSION_LEVEL1,
    )
    cdf_dst[variable].attrs.update(raw_var.attrs)


def _copy_attributes(cdf_dst, cdf_src):
    cdf_dst.attrs.update(cdf_src.attrs)


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


if __name__ == "__main__":
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        usage(sys.argv[0])
