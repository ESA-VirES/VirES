#!/usr/bin/env python3
#-------------------------------------------------------------------------------
#
# Convert Swarm MOD orbits from the SP3 text format to CDF.
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
from datetime import datetime
from os import rename, remove
from os.path import basename, splitext, exists
from numpy import asarray, datetime64, timedelta64
from eoxmagmod import convert, GEOCENTRIC_CARTESIAN, GEOCENTRIC_SPHERICAL
from common import (
    setup_logging, cdf_open, CommandError,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
    CDF_DOUBLE, CDF_EPOCH, CdfTypeEpoch,
)
from sp3_reader import read_sp3, GPS_TO_TAI_OFFSET
from leap_seconds import load_leap_seconds


LOGGER = getLogger(__name__)

VERSION = "1.0.0"

CDF_CREATOR = "EOX:convert_mod-%s [%s-%s, libcdf-%s]" % (
    VERSION, SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION
)

COMMON_PARAM = dict(
    compress=GZIP_COMPRESSION,
    compress_param=GZIP_COMPRESSION_LEVEL4
)

CDF_VARIABLE_ATTRIBUTES = {
    "Timestamp": {
        "DESCRIPTION": "UTC timestamp",
        "UNITS": "-",
        "FORMAT": " ",
    },
    "Latitude": {
        "DESCRIPTION": "Position in ITRF - Latitude",
        "UNITS": "deg",
        "FORMAT": "F8.3",
    },
    "Longitude": {
        "DESCRIPTION": "Position in ITRF - Longitude",
        "UNITS": "deg",
        "FORMAT": "F8.3",
    },
    "Radius": {
        "DESCRIPTION": "Position in ITRF - Radius",
        "UNITS": "m",
        "FORMAT": "F9.1",
    },
}

RE_PRODUCT_ID = re.compile(
    r'^[A-Z0-9_]+_(\d{8,8}T\d{6,6})_(\d{8,8}T\d{6,6})_[A-Z0-9_]+$'
)

RE_TIMESTAMP = re.compile(
    r'^(?P<year>\d{4,4})(?P<month>\d{2,2})(?P<day>\d{2,2})T'
    r'(?P<hour>\d{2,2})(?P<minute>\d{2,2})(?P<second>\d{2,2})'
)


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


def main(filename_input, filename_output):
    """ main subroutine """
    filename_tmp = filename_output + ".tmp.cdf"

    if exists(filename_tmp):
        remove(filename_tmp)

    try:
        convert_mod_sp3_product(filename_input, filename_tmp)
        rename(filename_tmp, filename_output)
        LOGGER.info("%s -> %s", filename_input, filename_output)
    #except ConversionSkipped as exc:
    #    LOGGER.warning("%s skipped - %s", filename_input, exc)
    finally:
        if exists(filename_tmp):
            remove(filename_tmp)


def convert_mod_sp3_product(filename_sp3, filename_cdf):
    product_id = splitext(basename(filename_sp3))[0]
    time_start, time_end = extract_time_range(product_id)

    header, time_gps, position_cart = read_sp3_data(filename_sp3)

    position_sph = convert(
        position_cart, GEOCENTRIC_CARTESIAN, GEOCENTRIC_SPHERICAL
    )

    # NOTE: It is assumed the UTC to GPS clock offset is constant for the whole
    #       daily Swarm MOD product and there are no products before 1972-01-01.
    leap_seconds = load_leap_seconds()
    utc_to_gps_offset = (
        leap_seconds.find_utc_to_tai_offset(header['start_time']) -
        GPS_TO_TAI_OFFSET
    )

    _check_value(header['version'], "#c", "SP3 file version")
    _check_value(header['time_system'], "GPS", "time system")
    _check_value(header['crs'], "IGS08", "coordinate system")
    _check_value(header['base_pv'], 0, "P/V base")
    _check_value(header['n_sat'], 1, "number of spacecrafts")

    time_utc = time_gps - timedelta64(utc_to_gps_offset, 's')

    # subset trimming times to stay within the product's nominal time extent
    selection = (time_utc >= time_start) & (time_utc < time_end)

    if not selection.all():
        LOGGER.warn(
            f"{basename(filename_sp3)}: The content of the product "
            f"({datetime64(time_utc.min(), 's')}/"
            f"{datetime64(time_utc.max(), 's')}) "
            "exceeds the nominal temporal extent of the product "
            f"({datetime64(time_start, 's')}/"
            f"{datetime64(time_end, 's') - timedelta64(1, 's')}) "
            "and it will be trimmed."
        )
        time_utc = time_utc[selection]
        position_sph = position_sph[selection]

    with cdf_open(filename_cdf, "w") as cdf:
        cdf.attrs.update({
            "TITLE": product_id,
            "ORIGINAL_PRODUCT_NAME": product_id,
            "UTC_TIME_OFFSET": utc_to_gps_offset,
            "ORIGINAL_TIME_SYSTEM": header['time_system'],
            "COORDINATE_SYSTEM": header['crs'],
            "LEAP_SECOND_TABLE_SOURCE": leap_seconds.source_url,
            "LEAP_SECOND_TABLE_LAST_UPDATE": leap_seconds.last_update,
            "LEAP_SECOND_TABLE_SHA1": leap_seconds.sha1_digest,
            "SP3_COMMENTS": header['comments'],
            "CREATOR": CDF_CREATOR,
            "CREATED": (
                datetime.utcnow().replace(microsecond=0)
            ).isoformat() + "Z",
        })
        _save_cdf_variable(cdf, 'Timestamp', CDF_EPOCH, CdfTypeEpoch.encode(time_utc))
        _save_cdf_variable(cdf, 'Latitude', CDF_DOUBLE, position_sph[:, 0])
        _save_cdf_variable(cdf, 'Longitude', CDF_DOUBLE, position_sph[:, 1])
        _save_cdf_variable(cdf, 'Radius', CDF_DOUBLE, position_sph[:, 2])


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


def _save_cdf_variable(cdf, variable, cdf_type, data, attrs=None):
    cdf.new(
        variable, data, cdf_type, dims=data.shape[1:], **COMMON_PARAM,
    )
    cdf[variable].attrs.update(
        attrs or CDF_VARIABLE_ATTRIBUTES.get(variable) or {}
    )


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
        asarray(positions, 'float64') * 1e3, # km -> m
    )


def _check_value(value, expected, label):
    if value != expected:
        raise ValueError(f"Unexpected {label} value! {value} != {expected}")


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
