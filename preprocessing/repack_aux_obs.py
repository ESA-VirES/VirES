#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Re-pack ground observatory data to a new CDF file.
#
# Author: Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2020 EOX IT Services GmbH
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

import sys
import ctypes
from datetime import datetime #, timedelta
from os import remove, rename
from os.path import basename, exists, splitext
from numpy import unique, concatenate
import spacepy
from spacepy import pycdf


GZIP_COMPRESSION = pycdf.const.GZIP_COMPRESSION
GZIP_COMPRESSION_LEVEL4 = ctypes.c_long(4)
GZIP_COMPRESSION_LEVEL = GZIP_COMPRESSION_LEVEL4

CDF_CREATOR = "EOX:repack_aux_obs.py [%s-%s, libcdf-%s]" % (
    spacepy.__name__, spacepy.__version__,
    "%s.%s.%s-%s" % tuple(
        v if isinstance(v, int) else v.decode('ascii')
        for v in pycdf.lib.version
    )
)


QUALITY_VARIABLE = "Quality"
OBS_CODE_VARIABLE = "IAGA_code"
OBS_CODES_ATTRIBUTE = "IAGA_CODES"
OBS_RANGES_ATTRIBUTE = "INDEX_RANGES"
TIMESTAMP_VARIABLE = "Timestamp"


CDF_FLOAT_TYPE = pycdf.const.CDF_FLOAT.value
CDF_DOUBLE_TYPE = pycdf.const.CDF_DOUBLE.value
CDF_REAL8_TYPE = pycdf.const.CDF_REAL8.value # CDF_DOUBLE != CDF_REAL8
CDF_REAL4_TYPE = pycdf.const.CDF_REAL4.value # CDF_FLOAT != CDF_REAL4

TYPE_MAP = {
    CDF_REAL8_TYPE: CDF_DOUBLE_TYPE,
    CDF_REAL4_TYPE: CDF_FLOAT_TYPE,
}


class CommandError(Exception):
    """ Command error exception. """


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <input> [<output>]" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Re-pack observatory data CDF and save them into a new CDF file.",
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
        repack_aux_obs(filename_input, filename_tmp)
        if exists(filename_tmp):
            print("%s -> %s" % (filename_input, filename_output))
            rename(filename_tmp, filename_output)
        else:
            print("%s skipped" % filename_input)
    finally:
        if exists(filename_tmp):
            remove(filename_tmp)


def repack_aux_obs(filename_input, filename_output):
    """ Squeeze dimension of Nx1 scalar arrays."""
    extra_attributes = {
        "ORIGINAL_PRODUCT_NAME": splitext(basename(filename_input))[0],
    }
    with cdf_open(filename_input) as cdf_src:
        variables = find_nx1_variables(cdf_src)
        index, ranges = get_obs_index_and_ranges(cdf_src)
        extra_attributes[OBS_CODES_ATTRIBUTE] = list(ranges)
        extra_attributes[OBS_RANGES_ATTRIBUTE] = list(ranges.values())
        if variables:
            with cdf_open(filename_output, "w") as cdf_dst:
                copy_squeezed(
                    cdf_dst, cdf_src, variables, index, extra_attributes
                )


def get_obs_index_and_ranges(cdf):
    """ Get index sorting the arrays by observatory and time. """
    times = cdf.raw_var(TIMESTAMP_VARIABLE)[...]
    codes = cdf[OBS_CODE_VARIABLE][...][:, 0]
    ranges = {}
    indices = []
    offset = 0
    for code in get_obs_codes(codes):
        index = get_obs_index(codes, code)
        index = sort_by(times, index)
        indices.append(index)
        ranges[code] = (offset, offset + len(index))
        offset += len(index)

    return concatenate(indices), ranges


def get_obs_index(codes, code):
    """ Get index extracting records for the given observatory. """
    return (codes == code).nonzero()[0]


def sort_by(values, index):
    """ Sort index by the given values. """
    return index[values[index].argsort()]


def get_obs_codes(codes):
    """ Read available observatory codes from the source file. """
    return [str(code) for code in unique(codes)]


def find_nx1_variables(cdf):
    """ Find variables with the squeezable Nx1 dimension. """
    variables = []
    for variable in cdf:
        shape = cdf[variable].shape
        if shape and shape[1:] == (1,):
            variables.append(variable)
    return variables


def copy_squeezed(cdf_dst, cdf_src, squeezed_variables, index, attrs=None):
    """ Copy squeezed content from the source to the destination CDF file. """
    squeezed_variables = set(squeezed_variables)
    _copy_attributes(cdf_dst, cdf_src)
    _update_attributes(cdf_dst, attrs)
    _update_creator(cdf_dst)
    for variable in cdf_src:
        if variable in squeezed_variables:
            _copy_squeezed_nx1(cdf_dst, cdf_src, variable, index)
        else:
            _copy_variable(cdf_dst, cdf_src, variable, index)


def _update_attributes(cdf, attrs):
    cdf.attrs.update(attrs or {})


def _update_creator(cdf):
    _update_attributes(cdf, {
        "CREATOR": CDF_CREATOR,
        "CREATED": (
            datetime.utcnow().replace(microsecond=0)
        ).isoformat() + "Z",
    })


def _copy_variable(cdf_dst, cdf_src, variable, index):
    _set_variable(
        cdf_dst, cdf_src, variable, cdf_src.raw_var(variable)[...][index]
    )


def _copy_squeezed_nx1(cdf_dst, cdf_src, variable, index):
    _set_variable(
        cdf_dst, cdf_src, variable, cdf_src.raw_var(variable)[:, 0][index]
    )


def _set_variable(cdf_dst, cdf_src, variable, data):
    raw_var = cdf_src.raw_var(variable)
    cdf_dst.new(
        variable, data, TYPE_MAP.get(raw_var.type(), raw_var.type()), dims=data.shape[1:],
        compress=GZIP_COMPRESSION, compress_param=GZIP_COMPRESSION_LEVEL,
    )
    cdf_dst[variable].attrs.update(raw_var.attrs)


def _copy_attributes(cdf_dst, cdf_src):
    _update_attributes(cdf_dst, cdf_src.attrs)


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
