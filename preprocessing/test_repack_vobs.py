#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Test that if the re-packed VOBS file equals to the original file.
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
from os.path import basename, exists
from numpy import asarray, stack, arange
from numpy.testing import assert_equal #, assert_allclose
from spacepy import pycdf


#DEF_PRECISION = {'atol': 0, 'rtol': 0}
#PRECISION = {
#    'Timestamp': {'atol': 1e-3, 'rtol': 0},
#}


class CommandError(Exception):
    """ Command error exception. """


def info(message):
    """ Print info message. """
    print(f"INFO: {message}")


def warning(message):
    """ Print warning message. """
    print(f"WARNING: {message}")


def error(message):
    """ Print error message. """
    print(f"ERROR: {message}")


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <source-CDF> <re-packed-CDF>" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Test the re-pack virtual observatory product against its source.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    argv = argv + [None]
    try:
        source = argv[1]
        tested = argv[2]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return source, tested


def main(filename_source, filename_tested):
    """ main subroutine """
    return test_converted_vobs(filename_source, filename_tested)


def test_converted_vobs(filename_source, filename_tested):
    """ Compare converted VOBS file to its source and report differences. """
    info(f"Comparing {filename_tested} to {filename_source} ...")
    error_count = 0
    with cdf_open(filename_source) as cdf_src:
        with cdf_open(filename_tested) as cdf_tested:
            error_count += compare_global_attributes(
                cdf_src.attrs, cdf_tested.attrs
            )
            error_count += compare_variables(cdf_src, cdf_tested)
            error_count += verify_site_codes(cdf_tested)
    if error_count:
        error(f"{filename_tested} has issues!")
    else:
        info(f"{filename_tested} is correct.")
    return error_count > 0


def verify_site_codes(cdf):
    """ Verify site labels. """

    def _get_site_code(latitude, longitude):
        return ("%s%2.2d%s%3.3d" % (
            "N" if latitude >= 0.0 else "S", abs(int(round(latitude))),
            "E" if longitude >= 0.0 else "W", abs(int(round(longitude))),
        ))

    key = 'SiteCode'

    if key not in cdf:
        error("Missing {key} variable!")
        return 1

    site_codes = asarray([
        _get_site_code(lat, lon) for lat, lon
        in zip(cdf['Latitude'][...], cdf['Longitude'][...])
    ])

    try:
        assert_equal(site_codes, cdf['SiteCode'][...])
    except AssertionError:
        error(f"Invalid {key} values detected!")
        return 1

    return 0


def compare_variables(cdf_src, cdf_dst):
    """ Compare variables. """
    error_count = 0
    index_src2dst, index_dst2src = _find_mapping(cdf_src, cdf_dst)

    if cdf_src.raw_var('Timestamp').shape != index_dst2src.shape:
        error_count += 1
        error("Ambiguous tested to source element mapping!")

    if cdf_dst.raw_var('Timestamp').shape != index_dst2src.shape:
        error_count += 1
        error("Ambiguous source to tested element mapping!")

    idx = arange(len(cdf_src.raw_var('Timestamp')))
    if (
            (idx != idx[index_src2dst][index_dst2src]).any() or
            (idx != idx[index_dst2src][index_src2dst]).any()
        ):
        error_count += 1
        error("Ambiguous element mapping!")

    excluded = ['SiteCode']
    for key in cdf_dst:
        if key in excluded:
            continue
        data_ref = cdf_src.raw_var(key)[...]
        data_tested = cdf_dst.raw_var(key)[...][index_src2dst]
        #data_tested = cdf_dst.raw_var(key)[...]#[index_src2dst]
        if key.startswith('B_') or key.startswith('sigma_'):
            data_tested = _convert_nec_to_rtp(data_tested)
        try:
            assert_equal(data_ref, data_tested)
            #assert_allclose(
            #    data_ref, data_tested, equal_nan=True,
            #    **PRECISION.get(key, DEF_PRECISION)
            #)
        except AssertionError:
            error_count += 1
            error(f"{key} data are not equal!")

    return error_count


def _convert_nec_to_rtp(data):
    return stack((-data[:, 2], -data[:, 0], data[:, 1]), axis=1)


def _find_mapping(cdf_src, cdf_dst):

    def _to_int(item):
        time, lat, lon, rad = item
        return int(round(time)), int(round(lat)), int(round(lon)), int(round(rad))

    src_items = [_to_int(item) for item in zip(
        cdf_src.raw_var('Timestamp')[...],
        cdf_src['Latitude'][...],
        cdf_src['Longitude'][...],
        cdf_src['Radius'][...],
    )]
    src_mapping = {item: idx for idx, item in enumerate(src_items)}

    dst_items = [_to_int(item) for item in zip(
        cdf_dst.raw_var('Timestamp')[...],
        cdf_dst['Latitude'][...],
        cdf_dst['Longitude'][...],
        cdf_dst['Radius'][...],
    )]
    dst_mapping = {item: idx for idx, item in enumerate(dst_items)}

    index_src2dst = asarray([
        dst_mapping[item] for item in src_items if item in dst_mapping
    ])
    index_dst2src = asarray([
        src_mapping[item] for item in dst_items if item in src_mapping
    ])
    return index_src2dst, index_dst2src


def compare_global_attributes(src_attrs, dst_attrs):
    """ Compare global attributes. """
    error_count = 0
    excluded = ['ORIGINAL_PRODUCT_NAME', 'CREATOR']
    for key in src_attrs:
        if key in excluded:
            continue

        if key not in dst_attrs:
            error_count += 1
            error(f"Missing {key} global attribute!")
            continue
        items0 = list(src_attrs[key])
        items1 = list(dst_attrs[key])
        if len(items0) != len(items1):
            error_count += 1
            error(
                f"Mismatch of the count of the {key} global attribute"
                f" elements {len(items0)} != {len(items1)}"
            )

        for idx, (item0, item1) in enumerate(zip(items0, items1)):
            if item0 != item1:
                error_count += 1
                error(
                    f"Mismatch of the global attribute {key}[{idx}]!"
                    f" {item0!r} != {item1!r}"
                )
    return error_count


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
