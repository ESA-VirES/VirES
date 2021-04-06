#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Test that the re-packed VOBS file equals to the original file.
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
from numpy import asarray, stack, arange
from numpy.testing import assert_equal
from common import cdf_open, setup_logging, CommandError
from compare_cdf import compare_attributes
from test_repack_aux_obs import verify_index_ranges

LOGGER = getLogger(__name__)


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <source-CDF> <re-packed-CDF>" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Test a re-packed virtual observatory product against its source.",
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
    result = test_converted_vobs(filename_source, filename_tested)
    if result:
        LOGGER.error("%s has issues!", filename_tested)
    else:
        LOGGER.info("%s is correct.", filename_tested)


def test_converted_vobs(filename_source, filename_tested):
    """ Compare converted VOBS file to its source and report differences. """
    error_count = 0
    with cdf_open(filename_source) as cdf_src:
        with cdf_open(filename_tested) as cdf_tested:
            error_count += compare_attributes(
                cdf_src.attrs, cdf_tested.attrs,
                excluded=['ORIGINAL_PRODUCT_NAME', 'CREATOR']
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
    return error_count > 0


def verify_site_codes(cdf, site_code_variable, latitude_variable, longitude_variable):
    """ Verify site labels. """

    def _get_site_code(latitude, longitude):
        return ("%s%2.2d%s%3.3d" % (
            "N" if latitude >= 0.0 else "S", abs(int(round(latitude))),
            "E" if longitude >= 0.0 else "W", abs(int(round(longitude))),
        ))

    if site_code_variable not in cdf:
        LOGGER.error("Missing {key} variable!")
        return 1

    site_codes = asarray([
        _get_site_code(lat, lon) for lat, lon
        in zip(cdf[latitude_variable][...], cdf[longitude_variable][...])
    ])

    try:
        assert_equal(site_codes, cdf[site_code_variable][...])
    except AssertionError:
        LOGGER.error("Invalid %s values detected!", site_code_variable)
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
        LOGGER.error("Impossible source to tested element mapping!")

    if not mask_src.all() and not dst_is_subset_of_src:
        error_count += 1
        LOGGER.error("Impossible tested to source element mapping!")

    idx_src = arange(mask_src.size)
    idx_dst = arange(mask_dst.size)
    if (
            (idx_src[mask_src] != idx_src[index_src2dst][index_dst2src[mask_src]]).any() or
            (idx_dst != idx_dst[index_dst2src][index_src2dst]).any()
        ):
        error_count += 1
        LOGGER.error("Ambiguous element mapping!")

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
            LOGGER.error("%s values differ!", var_dst)

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


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
