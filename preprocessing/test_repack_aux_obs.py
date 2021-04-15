#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Test that the re-packed AUX_OBS file equals to the original file.
#
# Author: Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
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
from os.path import basename
from numpy import lexsort, squeeze
from common import cdf_open, setup_logging, CommandError
from compare_cdf import compare_variables, compare_attributes


LOGGER = getLogger(__name__)

OBS_CODE_VARIABLE = "IAGA_code"
OBS_CODES_ATTRIBUTE = "IAGA_CODES"
OBS_RANGES_ATTRIBUTE = "INDEX_RANGES"
TIMESTAMP_VARIABLE = "Timestamp"


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <source-CDF> <re-packed-CDF>" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Test a re-packed ground observatory product against its source.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    try:
        source = argv[1]
        tested = argv[2]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return source, tested


def main(filename_source, filename_tested):
    """ main subroutine """
    LOGGER.info("Comparing %s to %s ...", filename_tested, filename_source)
    result = test_converted_aux_obs(filename_source, filename_tested)
    if result:
        LOGGER.error("%s has issues!", filename_tested)
    else:
        LOGGER.info("%s is correct.", filename_tested)


def test_converted_aux_obs(filename_source, filename_tested):
    """ Compare converted VOBS file to its source and report differences. """
    error_count = 0
    with cdf_open(filename_source) as cdf_src:
        index = get_sorting_index(cdf_src)
        with cdf_open(filename_tested) as cdf_tested:
            error_count += compare_attributes(
                cdf_src.attrs, cdf_tested.attrs,
            )
            error_count += compare_variables(
                cdf_src, cdf_tested, squeeze_src=True, index_src=index,
            )
            error_count += verify_index_ranges(
                cdf_tested, OBS_CODE_VARIABLE, OBS_CODES_ATTRIBUTE,
                OBS_RANGES_ATTRIBUTE,
            )
    return error_count > 0


def verify_index_ranges(cdf, site_code_variable, site_code_attribute, index_range_attribute):
    """ Verify site index ranges. """
    sites = list(cdf.attrs[site_code_attribute])
    ranges = [tuple(item) for item in list(cdf.attrs[index_range_attribute])]

    ref_ranges = {}
    for idx, code in enumerate(cdf[site_code_variable][...]):
        start, _ = ref_ranges.get(code) or (idx, None)
        ref_ranges[code] = (start, idx + 1)

    if sites != list(ref_ranges):
        LOGGER.error("Invalid %s codes!", site_code_attribute)
        return  1

    if ranges != list(ref_ranges.values()):
        LOGGER.error("Incorrect %s ranges!", index_range_attribute)
        return  1

    return 0


def get_sorting_index(cdf):
    """ Get AUX_OBS sorting index. """
    return lexsort((
        cdf.raw_var(TIMESTAMP_VARIABLE)[...],
        squeeze(cdf[OBS_CODE_VARIABLE][...]),
    ))


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
