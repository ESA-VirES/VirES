#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Compare content of two CDF files.
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
from numpy.testing import assert_equal
from common import setup_logging, CommandError, CDF_TYPE_LABEL, cdf_open

LOGGER = getLogger(__name__)


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s [--squeeze] <source-CDF> <re-packed-CDF>" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Compare content of two CDF files.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    squeeze_src_variables = True
    ignore_options = False

    args = []
    for arg in argv:
        if arg == '--':
            ignore_options = True
        elif arg == '--squeeze' and not ignore_options:
            squeeze_src_variables = True
        else:
            args.append(arg)

    try:
        source = args[1]
        tested = args[2]
    except IndexError:
        raise CommandError("Not enough input arguments!")

    return source, tested, squeeze_src_variables


def main(filename_source, filename_tested, squeeze_src_variables=False):
    """ main subroutine """
    LOGGER.info("Comparing %s to %s ...", filename_tested, filename_source)
    result = compare_cdf(filename_source, filename_tested, squeeze_src_variables)
    if result:
        LOGGER.error("%s has issues!", filename_tested)
    else:
        LOGGER.info("%s is correct.", filename_tested)


def compare_cdf(filename_source, filename_tested,
                squeeze_src_variables=False, exclude_attrs=None):
    """ Compare two CDF files.
    The tested file is expected to contain the same data and attributes
    as the source file. Extra attributes and variables in the tested file
    which are not present in the source file are ignored.
    """
    error_count = 0
    with cdf_open(filename_source) as cdf_src:
        with cdf_open(filename_tested) as cdf_tested:
            error_count += compare_attributes(
                cdf_src.attrs, cdf_tested.attrs, excluded=exclude_attrs,
            )
            error_count += compare_variables(
                cdf_src, cdf_tested, squeeze_src=squeeze_src_variables,
            )
    return error_count > 0


def compare_variables(cdf_src, cdf_dst, squeeze_src=False, index_src=None):
    """ Compare variables of two CDF file. """
    error_count = 0
    for variable in cdf_src:
        if variable not in cdf_dst:
            error_count += 1
            LOGGER.error("Missing %s CDF variable!", variable)
            continue
        error_count += compare_variable(
            variable, cdf_src.raw_var(variable), cdf_dst.raw_var(variable),
            squeeze_src=squeeze_src,
            index_src=index_src,
        )
    return error_count


def compare_variable(name, var_src, var_dst, squeeze_src=False, index_src=None):
    """ Compare type, shape, values and attributes of two variables. """

    def _shape_to_str(shape):
        return "[%s]" % ",".join(str(v) for v in shape)

    error_count = compare_attributes(
        var_src.attrs, var_dst.attrs, "%s variable" % name
    )

    if var_src.type() != var_dst.type():
        LOGGER.error(
            "%s data type mismatch! %s != %s", name,
            CDF_TYPE_LABEL[var_src.type()], CDF_TYPE_LABEL[var_dst.type()],
        )
        return error_count + 1

    data_src, data_dst = var_src[...], var_dst[...]

    if squeeze_src:
        if data_src.shape[1:] == (1,):
            data_src = data_src[:, 0]

    if index_src is not None:
        data_src = data_src[index_src]

    if data_src.shape != data_dst.shape:
        LOGGER.error(
            "%s data shape mismatch! %s != %s", name,
            _shape_to_str(data_src.shape), _shape_to_str(data_dst.shape),
        )
        return error_count + 1

    try:
        assert_equal(data_src[...], data_dst[...])
    except AssertionError:
        error_count += 1
        LOGGER.error("%s values differ!", name)

    return error_count


def compare_attributes(src_attrs, dst_attrs, label="global", excluded=None):
    """ Compare attributes. """
    error_count = 0
    excluded = set(excluded or [])
    for key in src_attrs:
        if key in excluded:
            continue
        if key not in dst_attrs:
            error_count += 1
            LOGGER.error("Missing %s attribute %s!", label, key)
            continue
        items0 = src_attrs[key]
        items1 = dst_attrs[key]
        if len(items0) != len(items1):
            error_count += 1
            LOGGER.error(
                "Mismatch of the count of the %s %s attribute"
                " elements %s != %s", key, label, len(items0), len(items1)
            )

        for idx, (item0, item1) in enumerate(zip(iter(items0), iter(items1))):
            try:
                assert_equal(item0, item1)
            except AssertionError:
                error_count += 1
                LOGGER.error(
                    "Mismatch of the %s attribute %s[%s]!"
                    " %r != %r", label, key, idx, item0, item1
                )
    return error_count


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
