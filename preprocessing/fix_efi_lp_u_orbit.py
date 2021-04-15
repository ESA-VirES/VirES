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

import sys
from logging import getLogger
from datetime import datetime, timedelta
from os import rename, remove
from os.path import basename, exists
from common import (
    setup_logging, cdf_open, CommandError,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
)


LOGGER = getLogger()

MAX_TIME_SELECTION = timedelta(days=25*365.25) # max. time selection of ~25 years

CDF_CREATOR = "EOX:fix_efi_lp_u_orbit.py [%s-%s, libcdf-%s]" % (
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION
)


class ConversionSkipped(Exception):
    """ Exception raised when the processing is skipped."""


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <input> [<output>]" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  This script fixes the wrong Nx1 dimension of the U_orbit variable",
        "  of the Swarm EFIx_LP products. The scripts detect whether the",
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
    return input_, output


def main(filename_input, filename_output=None):
    """ main subroutine """
    if filename_output is None:
        filename_output = filename_input

    filename_tmp = filename_output + ".tmp.cdf"

    if exists(filename_tmp):
        remove(filename_tmp)

    try:
        fix_efi_lp(filename_input, filename_tmp)
        LOGGER.info("%s -> %s", filename_input, filename_output)
        rename(filename_tmp, filename_output)
    except ConversionSkipped as exc:
        LOGGER.warning("%s skipped - %s", filename_input, exc)
    finally:
        if exists(filename_tmp):
            remove(filename_tmp)


def fix_efi_lp(filename_input, filename_output):
    """ Write a fixed EFIx_LP product. """
    with cdf_open(filename_input) as cdf_src:
        if "U_orbit" in cdf_src and cdf_src["U_orbit"].shape[1:] == (1,):
            with cdf_open(filename_output, "w") as cdf_dst:
                copy_fixed_efi_lp(cdf_dst, cdf_src)


def copy_fixed_efi_lp(cdf_dst, cdf_src):
    """ Copy fixed content from one EFIx_LP CDF to a new one. """
    _copy_attributes(cdf_dst, cdf_src)
    _update_creator(cdf_dst)
    for variable in cdf_src:
        if variable == "U_orbit":
            _copy_u_orbit(cdf_dst, cdf_src, variable)
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


def _copy_u_orbit(cdf_dst, cdf_src, variable):
    _set_variable(cdf_dst, cdf_src, variable, cdf_src.raw_var(variable)[:, 0])


def _set_variable(cdf_dst, cdf_src, variable, data):
    raw_var = cdf_src.raw_var(variable)
    cdf_dst.new(
        variable, data, raw_var.type(), dims=data.shape[1:],
        compress=GZIP_COMPRESSION, compress_param=GZIP_COMPRESSION_LEVEL4,
    )
    cdf_dst[variable].attrs.update(raw_var.attrs)


def _copy_attributes(cdf_dst, cdf_src):
    cdf_dst.attrs.update(cdf_src.attrs)


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
