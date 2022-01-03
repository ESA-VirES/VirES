#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Test Swarm MOD orbits converted to CDF against the source  SP3 text format.
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
# pylint: disable=missing-docstring

import re
import sys
from logging import getLogger
from os.path import basename, splitext
from numpy import asarray, datetime64, timedelta64, stack
from numpy.testing import assert_equal, assert_allclose
from eoxmagmod import convert, GEOCENTRIC_CARTESIAN, GEOCENTRIC_SPHERICAL
from common import (
    setup_logging, cdf_open, CommandError,
    CdfTypeEpoch,
)
from sp3_reader import read_sp3, GPS_TO_TAI_OFFSET
from leap_seconds import load_leap_seconds

LOGGER = getLogger(__name__)

RE_PRODUCT_ID = re.compile(
    r'^[A-Z0-9_]+_(\d{8,8}T\d{6,6})_(\d{8,8}T\d{6,6})_[A-Z0-9_]+$'
)

RE_TIMESTAMP = re.compile(
    r'^(?P<year>\d{4,4})(?P<month>\d{2,2})(?P<day>\d{2,2})T'
    r'(?P<hour>\d{2,2})(?P<minute>\d{2,2})(?P<second>\d{2,2})'
)


class TestError(Exception):
    """ Test error exception. """


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <input SP3> <output CDF>" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Convert Swarm MOD orbit products to CDF format.",
        "  The script converts Cartesian positions and GPS times to geocentric ",
        "  spherical positions and UTC timestamps.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    try:
        input_ = argv[1]
        output = argv[2]
    except IndexError:
        raise CommandError("Not enough input arguments!") from None
    return input_, output


def main(filename_source, filename_tested):
    """ main subroutine """
    LOGGER.info("Comparing %s to %s ...", filename_tested, filename_source)
    result = test_converted_mod_sp3_product(filename_source, filename_tested)
    if result:
        LOGGER.error("%s failed the test!", filename_tested)
    else:
        LOGGER.info("%s is correct.", filename_tested)


def test_converted_mod_sp3_product(filename_sp3, filename_cdf):
    product_id = splitext(basename(filename_sp3))[0]
    time_start, time_end = extract_time_range(product_id)

    sp3_header, time_gps, position_cart = read_sp3_data(filename_sp3)

    # NOTE: It is assumed the UTC to GPS clock offset is constant for the whole
    #       daily Swarm MOD product and there are no products before 1972-01-01.
    leap_seconds = load_leap_seconds()

    error_count = 0
    with cdf_open(filename_cdf) as cdf:
        error_count += test_metadata(cdf, filename_sp3, sp3_header, leap_seconds)
        error_count += test_data(cdf, time_gps, position_cart, time_start, time_end)

    return error_count


def test_metadata(cdf, filename_sp3, sp3_header, leap_seconds):
    """ Test CDF metadata. """

    product_id = splitext(basename(filename_sp3))[0]
    utc_to_gps_offset = (
        leap_seconds.find_utc_to_tai_offset(sp3_header['start_time']) -
        GPS_TO_TAI_OFFSET
    )

    expected_attributes = {
        "TITLE": [product_id],
        "ORIGINAL_PRODUCT_NAME": [product_id],
        "UTC_TIME_OFFSET": [utc_to_gps_offset],
        "ORIGINAL_TIME_SYSTEM": [sp3_header['time_system']],
        "COORDINATE_SYSTEM": [sp3_header['crs']],
        "SP3_COMMENTS": sp3_header['comments'],
    }

    error_count = 0
    for key, expected_values  in expected_attributes.items():
        if key not in cdf.attrs:
            error_count += 1
            LOGGER.error("Missing global attribute %s!", key)
            continue
        values = cdf.attrs[key]
        if len(values) != len(expected_values):
            error_count += 1
            LOGGER.error(
                "Mismatch of the count of the %s global attribute"
                " elements! %s != %s", key, len(expected_values), len(values)
            )

        for idx, (value, expected) in enumerate(zip(iter(values), expected_values)):
            try:
                assert_equal(value, expected)
            except AssertionError:
                error_count += 1
                LOGGER.error(
                    "Mismatch of the global attribute %s[%s]!"
                    " %r != %r", key, idx, value, expected
                )
    return error_count


def test_data(cdf, time_gps_ref, position_cart_ref, time_start, time_end):
    """ Test CDF content. """
    utc_to_gps_offset = timedelta64(cdf.attrs['UTC_TIME_OFFSET'][0], 's')

    time_start_gps = time_start + utc_to_gps_offset
    time_end_gps = time_end + utc_to_gps_offset

    time_gps = (
        CdfTypeEpoch.decode(cdf.raw_var('Timestamp')[...]) + utc_to_gps_offset
    )
    position_cart = convert(
        stack((
            cdf['Latitude'][...],
            cdf['Longitude'][...],
            cdf['Radius'][...] * 1e-3,
        ), axis=-1),
        GEOCENTRIC_SPHERICAL,
        GEOCENTRIC_CARTESIAN,
    )

    mask = (time_gps_ref >= time_start_gps) & (time_gps_ref < time_end_gps)

    error_count = 0

    try:
        assert_equal(time_gps, time_gps_ref[mask])
    except AssertionError as error:
        error_count += 1
        LOGGER.error("Timestamp values differ! %s", error)

    try:
        assert_allclose(
            position_cart, position_cart_ref[mask], rtol=0, atol=1e-9,
        )
    except AssertionError as error:
        error_count += 1
        LOGGER.error("Position values differ! %s", error)

    return error_count


def read_sp3_data(filename_sp3):
    times, positions  = [], []
    with open(filename_sp3) as fin:
        header, records = read_sp3(fin)
        for record in records:
            times.append(record['timestamp'])
            positions.append((record['px'], record['py'], record['pz']))
    return (
        header,
        asarray(times, 'datetime64[ms]'),
        asarray(positions, 'float64'),
    )


def extract_time_range(product_id):

    def _parse_timestamp(timestamp):
        match = RE_TIMESTAMP.match(timestamp)
        if not match:
            raise ValueError(f"Invalid product timestamp {timestamp}!")
        return datetime64(
            "{year}-{month}-{day}T{hour}:{minute}:{second}"
            "".format(**match.groupdict()), 'ms'
        )

    match = RE_PRODUCT_ID.match(product_id)
    if not match:
        raise ValueError(f"Invalid product id {product_id}!")

    start, end = [_parse_timestamp(item) for item in match.groups()]

    return start, end + timedelta64(1000, 'ms')


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
