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
from logging import getLogger
from datetime import datetime
from os import remove, rename
from os.path import basename, exists, splitext
from numpy import unique, concatenate, squeeze
from common import (
    setup_logging, cdf_open, CommandError,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
    CDF_REAL8, CDF_REAL4, CDF_DOUBLE, CDF_FLOAT,
)


LOGGER = getLogger(__name__)

CDF_CREATOR = "EOX:repack_aux_obs.py [%s-%s, libcdf-%s]" % (
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION
)


OBS_CODE_VARIABLE = "IAGA_code"
OBS_CODES_ATTRIBUTE = "IAGA_CODES"
OBS_RANGES_ATTRIBUTE = "INDEX_RANGES"
TIMESTAMP_VARIABLE = "Timestamp"


TYPE_MAP = {
    CDF_REAL8: CDF_DOUBLE,
    CDF_REAL4: CDF_FLOAT,
}


class ConversionSkipped(Exception):
    """ Exception raised when the processing is skipped."""


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
    return input_, output


def main(filename_input, filename_output=None):
    """ main subroutine """
    if filename_output is None:
        filename_output = filename_input

    filename_tmp = filename_output + ".tmp.cdf"

    if exists(filename_tmp):
        remove(filename_tmp)

    try:
        repack_aux_obs(filename_input, filename_tmp)
        LOGGER.info("%s -> %s", filename_input, filename_output)
        rename(filename_tmp, filename_output)
    except ConversionSkipped as exc:
        LOGGER.warning("%s skipped - %s", filename_input, exc)
    finally:
        if exists(filename_tmp):
            remove(filename_tmp)


def repack_aux_obs(filename_input, filename_output):
    """ Repack AUX_OBS product file and squeeze dimension of Nx1 scalar arrays.
    """

    def _does_not_need_repacking():
        dindex = index[1:] - index[:-1]
        is_same_order = (
            dindex.size < 0 or (dindex.max() == 1 and dindex.min() == 1)
        )
        return (
            OBS_RANGES_ATTRIBUTE in cdf_src.attrs and
            OBS_CODES_ATTRIBUTE in cdf_src.attrs and
            is_same_order and not bool(nx1_variables)
        )

    extra_attributes = {
        "ORIGINAL_PRODUCT_NAME": splitext(basename(filename_input))[0],
    }
    with cdf_open(filename_input) as cdf_src:
        nx1_variables = find_nx1_variables(cdf_src)
        index, ranges = get_obs_index_and_ranges(
            cdf_src.raw_var(TIMESTAMP_VARIABLE)[...],
            squeeze(cdf_src[OBS_CODE_VARIABLE][...])
        )
        if _does_not_need_repacking():
            raise ConversionSkipped("repacking is not needed")
        extra_attributes[OBS_CODES_ATTRIBUTE] = list(ranges)
        extra_attributes[OBS_RANGES_ATTRIBUTE] = list(ranges.values())
        with cdf_open(filename_output, "w") as cdf_dst:
            copy_squeezed_and_ordered(
                cdf_dst, cdf_src, nx1_variables, index, extra_attributes
            )


def get_obs_index_and_ranges(times, codes):
    """ Get index sorting the arrays by observatory and time. """
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


def copy_squeezed_and_ordered(cdf_dst, cdf_src, squeezed_variables, index, attrs=None):
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
        compress=GZIP_COMPRESSION, compress_param=GZIP_COMPRESSION_LEVEL4,
    )
    cdf_dst[variable].attrs.update(raw_var.attrs)


def _copy_attributes(cdf_dst, cdf_src):
    _update_attributes(cdf_dst, cdf_src.attrs)


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
