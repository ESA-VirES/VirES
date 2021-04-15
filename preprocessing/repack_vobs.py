#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Re-pack virtual observatory data to a new CDF file.
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
from datetime import datetime
from os import remove, rename
from os.path import basename, exists, splitext
from numpy import unique, concatenate, asarray, argsort, stack
from common import (
    setup_logging, cdf_open, CommandError,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
    CDF_CHAR, CDF_REAL8, CDF_REAL4, CDF_DOUBLE, CDF_FLOAT,
)


LOGGER = getLogger(__name__)

CDF_CREATOR = "EOX:repack_vobs.py [%s-%s, libcdf-%s]" % (
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION
)

OBS_CODE_ATTRIBUTES = {
    "UNITS": "-",
    "DESCRIPTION": "Seven letter virtual observatory identification code associated with datum",
    "FORMAT": "A7"
}

OBS_CODE_SV_ATTRIBUTES = {
    "UNITS": "-",
    "DESCRIPTION": "Secular variation seven letter virtual observatory identification code associated with datum",
    "FORMAT": "A7"
}

OBS_CODES_ATTRIBUTE = "SITE_CODES"
OBS_RANGES_ATTRIBUTE = "INDEX_RANGES"
OBS_CODE_VARIABLE = "SiteCode"
TIMESTAMP_VARIABLE = "Timestamp"
LATITUDE_VARIABLE = "Latitude"
LONGITUDE_VARIABLE = "Longitude"
RADIUS_VARIABLE = "Radius"

OBS_RANGES_SV_ATTRIBUTE = "INDEX_RANGES_SV"
OBS_CODE_SV_VARIABLE = "SiteCode_SV"
TIMESTAMP_SV_VARIABLE = "Timestamp_SV"
LATITUDE_SV_VARIABLE = "Latitude_SV"
LONGITUDE_SV_VARIABLE = "Longitude_SV"
RADIUS_SV_VARIABLE = "Radius_SV"

VARIABLES = [
    TIMESTAMP_VARIABLE,
    LATITUDE_VARIABLE,
    LONGITUDE_VARIABLE,
    RADIUS_VARIABLE,
    "B_CF",
    "B_OB",
    "sigma_CF",
    "sigma_OB",
]

VARIABLES_SV = [
    TIMESTAMP_SV_VARIABLE,
    LATITUDE_VARIABLE,
    LONGITUDE_VARIABLE,
    RADIUS_VARIABLE,
    "B_SV",
    "sigma_SV",
]

VARIABLES_SV_MAP = {
    LATITUDE_VARIABLE: LATITUDE_SV_VARIABLE,
    LONGITUDE_VARIABLE: LONGITUDE_SV_VARIABLE,
    RADIUS_VARIABLE: RADIUS_SV_VARIABLE,
}

TYPE_MAP = {
    CDF_REAL8: CDF_DOUBLE,
    CDF_REAL4: CDF_FLOAT,
}

# NOTE: There seems to be no way how to get the pad value via the pycdf API.
TIMESTAMP_PAD_VALUE = 59958230400000.0 # 1900-01-01T00:00:00Z


def _covert_rtp_to_nec(data):
    return stack((-data[:, 1], +data[:, 2], -data[:, 0]), axis=1)


def _covert_rtp_to_nec_positive(data):
    return stack((data[:, 1], +data[:, 2], data[:, 0]), axis=1)


DATA_CONVERSION = {
    "B_CF": _covert_rtp_to_nec,
    "B_OB": _covert_rtp_to_nec,
    "B_SV": _covert_rtp_to_nec,
    "sigma_CF": _covert_rtp_to_nec_positive,
    "sigma_OB": _covert_rtp_to_nec_positive,
    "sigma_SV": _covert_rtp_to_nec_positive,
}


class ConversionSkipped(Exception):
    """ Exception raised when the processing is skipped."""


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <input> [<output>]" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Re-pack virtual observatory product and save them into a new CDF file.",
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
        repack_vobs(filename_input, filename_tmp)
        LOGGER.info("%s -> %s", filename_input, filename_output)
        rename(filename_tmp, filename_output)
    except ConversionSkipped as exc:
        LOGGER.warning("%s skipped - %s", filename_input, exc)
    finally:
        if exists(filename_tmp):
            remove(filename_tmp)


def is_repacked(cdf):
    """ True if the CDF has been already repacked. """
    return (
        'CREATOR' in cdf.attrs
        and str(cdf.attrs['CREATOR'][0]).startswith('EOX:repack_vobs.py')
    )


def repack_vobs(filename_input, filename_output):
    """ Repack VOBS product file. """
    extra_attributes = {
        "ORIGINAL_PRODUCT_NAME": splitext(basename(filename_input))[0],
    }
    with cdf_open(filename_input) as cdf_src:

        # skip already re-packed data
        if is_repacked(cdf_src):
            raise ConversionSkipped("already repacked product")

        _, sites = extract_sites_labels(
            cdf_src[LATITUDE_VARIABLE][...],
            cdf_src[LONGITUDE_VARIABLE][...],
            cdf_src[RADIUS_VARIABLE][...],
        )
        index, ranges = get_obs_index_and_ranges(
            cdf_src.raw_var(TIMESTAMP_VARIABLE)[...], sites
        )

        times_sv = cdf_src.raw_var(TIMESTAMP_SV_VARIABLE)[...]
        offset_sv = get_time_offset(times_sv, TIMESTAMP_PAD_VALUE)
        index_sv, ranges_sv = get_obs_index_and_ranges(
            times_sv[offset_sv:], sites[offset_sv:times_sv.size]
        )
        index_sv += offset_sv
        del times_sv

        assert list(ranges) == list(ranges_sv)

        extra_attributes[OBS_CODES_ATTRIBUTE] = list(ranges)
        extra_attributes[OBS_RANGES_ATTRIBUTE] = list(ranges.values())
        extra_attributes[OBS_RANGES_SV_ATTRIBUTE] = list(ranges_sv.values())

        with cdf_open(filename_output, "w") as cdf_dst:
            _copy_attributes(cdf_dst, cdf_src)
            _update_attributes(cdf_dst, extra_attributes)
            _update_creator(cdf_dst)
            _set_variable(
                cdf_dst, OBS_CODE_VARIABLE, sites[index], CDF_CHAR,
                OBS_CODE_ATTRIBUTES
            )
            for variable in VARIABLES:
                _copy_variable(cdf_dst, cdf_src, variable, variable, index)
            _set_variable(
                cdf_dst, OBS_CODE_SV_VARIABLE, sites[index_sv], CDF_CHAR,
                OBS_CODE_SV_ATTRIBUTES
            )
            for variable in VARIABLES_SV:
                _copy_variable(
                    cdf_dst, cdf_src, variable,
                    VARIABLES_SV_MAP.get(variable, variable), index_sv
                )


def get_time_offset(times, nodata_value):
    """ Get offset to the first valid time value. """
    idx = (times != nodata_value).nonzero()[0]
    return idx[0] if idx.size > 0 else times.size


def get_obs_index_and_ranges_with_offset(times, codes, offset):
    """ Get index sorting the arrays by observatory and time. """
    index, ranges = get_obs_index_and_ranges(times[offset:], codes[offset:])
    return index + offset, ranges


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
    unique_codes, index = unique(codes, return_index=True)
    return list(unique_codes[argsort(index)])


def extract_sites_labels(latitudes, longitudes, radii):
    """ Extract sites labels. """

    def _get_site_code(latitude, longitude):
        return ("%s%2.2d%s%3.3d" % (
            "N" if latitude >= 0.0 else "S", abs(int(round(latitude))),
            "E" if longitude >= 0.0 else "W", abs(int(round(longitude))),
        )).encode('ascii')

    site_map, sites = {}, []
    for location in zip(latitudes, longitudes, radii):
        site_code = site_map.get(location)
        if not site_code:
            latitude, longitude, _ = location
            site_map[location] = site_code = _get_site_code(latitude, longitude)
        sites.append(site_code)

    return site_map, asarray(sites, 'S')


def _update_attributes(cdf, attrs):
    cdf.attrs.update(attrs or {})


def _update_creator(cdf):
    _update_attributes(cdf, {
        "CREATOR": CDF_CREATOR,
        "CREATED": (
            datetime.utcnow().replace(microsecond=0)
        ).isoformat() + "Z",
    })


def _copy_variable(cdf_dst, cdf_src, variable_src, variable_dst, index):
    raw_var = cdf_src.raw_var(variable_src)
    data = cdf_src.raw_var(variable_src)[...][index]
    cdf_dst.new(
        variable_dst,
        DATA_CONVERSION.get(variable_src, lambda v: v)(data),
        TYPE_MAP.get(raw_var.type(), raw_var.type()),
        dims=data.shape[1:],
        compress=GZIP_COMPRESSION,
        compress_param=GZIP_COMPRESSION_LEVEL4,
    )
    cdf_dst[variable_dst].attrs.update(raw_var.attrs)


def _covert_rtp_to_nec(data):
    return stack((-data[:, 1], +data[:, 2], -data[:, 0]), axis=1)


def _set_variable(cdf_dst, variable, data, cdf_type, attrs=None):
    cdf_dst.new(
        variable,
        data,
        cdf_type,
        dims=data.shape[1:],
        compress=GZIP_COMPRESSION,
        compress_param=GZIP_COMPRESSION_LEVEL4,
    )
    if attrs:
        cdf_dst[variable].attrs.update(attrs)


def _copy_attributes(cdf_dst, cdf_src):
    _update_attributes(cdf_dst, {
        key: list(value)
        for key, value in cdf_src.attrs.items()
    })


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
