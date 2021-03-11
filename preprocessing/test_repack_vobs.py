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
            error_count += compare_variables(
                cdf_src, cdf_tested,
                'Timestamp', ['Latitude', 'Longitude', 'Radius'],
                {
                    'Timestamp': 'Timestamp',
                    'Latitude': 'Latitude',
                    'Longitude': 'Longitude',
                    'Radius': 'Radius',
                    'B_CF': 'B_CF',
                    'B_OB': 'B_OB',
                    'sigma_CF': 'sigma_CF',
                    'sigma_OB': 'sigma_OB',
                },
            )
            error_count += compare_variables(
                cdf_src, cdf_tested,
                'Timestamp_SV', ['Latitude_SV', 'Longitude_SV', 'Radius_SV'],
                {
                    'Timestamp_SV': 'Timestamp_SV',
                    'Latitude_SV': 'Latitude',
                    'Longitude_SV': 'Longitude',
                    'Radius_SV': 'Radius',
                    'B_SV': 'B_SV',
                    'sigma_SV': 'sigma_SV',
                },
                dst_is_subset_of_src=True,
            )
            error_count += verify_site_codes(
                cdf_tested, 'SiteCode', 'Latitude', 'Longitude'
            )
            error_count += verify_site_codes(
                cdf_tested, 'SiteCode_SV', 'Latitude_SV', 'Longitude_SV'
            )
            error_count += verify_index_ranges(
                cdf_tested, 'SiteCode', 'SITE_CODES', 'INDEX_RANGES'
            )
            error_count += verify_index_ranges(
                cdf_tested, 'SiteCode_SV', 'SITE_CODES', 'INDEX_RANGES_SV'
            )
    if error_count:
        error(f"{filename_tested} has issues!")
    else:
        info(f"{filename_tested} is correct.")
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
        error(f"Invalid {site_code_attribute} codes!")
        return  1

    if ranges != list(ref_ranges.values()):
        error(f"Incorrect {index_range_attribute} ranges!")
        return  1

    return 0


def verify_site_codes(cdf, site_code_variable, latitude_variable, longitude_variable):
    """ Verify site labels. """

    def _get_site_code(latitude, longitude):
        return ("%s%2.2d%s%3.3d" % (
            "N" if latitude >= 0.0 else "S", abs(int(round(latitude))),
            "E" if longitude >= 0.0 else "W", abs(int(round(longitude))),
        ))

    if site_code_variable not in cdf:
        error("Missing {key} variable!")
        return 1

    site_codes = asarray([
        _get_site_code(lat, lon) for lat, lon
        in zip(cdf[latitude_variable][...], cdf[longitude_variable][...])
    ])

    try:
        assert_equal(site_codes, cdf[site_code_variable][...])
    except AssertionError:
        error(f"Invalid {site_code_variable} values detected!")
        return 1

    return 0


def compare_variables(cdf_src, cdf_dst, time_variable, location_variables,
                      tested_variables, dst_is_subset_of_src=False):
    """ Compare variables. """
    error_count = 0
    _vars = [time_variable] + location_variables
    index_src2dst, index_dst2src = _find_mapping(
        cdf_src, cdf_dst, [tested_variables[v] for v in _vars], _vars,
    )

    mask_src = index_dst2src != -1
    mask_dst = index_src2dst != -1

    if not mask_dst.all():
        error_count += 1
        error("Impossible source to tested element mapping!")

    if not mask_src.all() and not dst_is_subset_of_src:
        error_count += 1
        error("Impossible tested to source element mapping!")

    idx_src = arange(mask_src.size)
    idx_dst = arange(mask_dst.size)
    if (
            (idx_src[mask_src] != idx_src[index_src2dst][index_dst2src[mask_src]]).any() or
            (idx_dst != idx_dst[index_dst2src][index_src2dst]).any()
        ):
        error_count += 1
        error("Ambiguous element mapping!")

    # compare mapping
    for var_dst, var_src in tested_variables.items():
        data_ref = cdf_src.raw_var(var_src)[...]
        data_tested = cdf_dst.raw_var(var_dst)[...]
        if var_dst.startswith('B_'):
            data_tested = _convert_nec_to_rtp(data_tested)
        elif var_dst.startswith('sigma_'):
            data_tested = _convert_nec_to_rtp_positive(data_tested)
        try:
            assert_equal(data_ref[index_src2dst], data_tested)
            assert_equal(
                data_ref[:mask_src.size][mask_src],
                data_tested[index_dst2src[mask_src]]
            )
        except AssertionError:
            error_count += 1
            error(f"{var_dst} values differ!")

    return error_count


def _convert_nec_to_rtp(data):
    return stack((-data[:, 2], -data[:, 0], data[:, 1]), axis=1)


def _convert_nec_to_rtp_positive(data):
    return stack((data[:, 2], data[:, 0], data[:, 1]), axis=1)


def _find_mapping(cdf_src, cdf_dst, vars_src, vars_dst):

    def _to_int(item):
        time, lat, lon, rad = item
        return int(round(time)), int(round(lat)), int(round(lon)), int(round(rad))

    def _read_items(cdf, variables):
        time, lat, lon, rad = variables
        return [_to_int(item) for item in zip(
            cdf.raw_var(time)[...],
            cdf[lat][...],
            cdf[lon][...],
            cdf[rad][...],
        )]

    src_items = _read_items(cdf_src, vars_src)
    src_mapping = {item: idx for idx, item in enumerate(src_items)}

    dst_items = _read_items(cdf_dst, vars_dst)
    dst_mapping = {item: idx for idx, item in enumerate(dst_items)}

    index_dst2src = asarray([dst_mapping.get(item, -1) for item in src_items])
    index_src2dst = asarray([src_mapping.get(item, -1) for item in dst_items])

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
