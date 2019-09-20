#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Convert AEJxPBL and AEJxPBS products to a simple time-series
#
# Author: Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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

from __future__ import print_function
import re
import sys
import ctypes
from datetime import datetime, timedelta
from os import rename, remove
from os.path import basename, exists
from itertools import chain
from numpy import (
    concatenate, full, nan, broadcast_to, array, logical_or, logical_not, isnan,
    argsort, zeros,
)
import spacepy
from spacepy import pycdf

RE_AEJ_PBL_2F = re.compile("^AEJ[ABC]PBL_2F$")
RE_AEJ_PBS_2F = re.compile("^SW_OPER_AEJ[ABC]PBS_2F$")

MAX_TIME_SELECTION = timedelta(days=25*365.25) # max. time selection of ~25 years

GZIP_COMPRESSION = pycdf.const.GZIP_COMPRESSION
GZIP_COMPRESSION_LEVEL1 = ctypes.c_long(1)
GZIP_COMPRESSION_LEVEL9 = ctypes.c_long(9)
CDF_EPOCH = pycdf.const.CDF_EPOCH
CDF_DOUBLE = pycdf.const.CDF_DOUBLE
CDF_UINT1 = pycdf.const.CDF_UINT1
CDF_UINT2 = pycdf.const.CDF_UINT2

CDF_CREATOR = "EOX:convert_aej_bp.py [%s-%s, libcdf-%s]" % (
    spacepy.__name__, spacepy.__version__,
    "%s.%s.%s-%s" % tuple(
        v if isinstance(v, int) else v.decode('ascii')
        for v in pycdf.lib.version
    )
)

# save variables
COMMON_PARAM = dict(
    compress=GZIP_COMPRESSION,
    compress_param=GZIP_COMPRESSION_LEVEL1
)

# point types
EB0 = 0x0       # Equatorial Boundary 0 (WEJ?)
EB1 = 0x1       # Equatorial Boundary 1 (EEJ?)
PB0 = 0x2       # Polar Boundary 0 (WEJ?)
PB1 = 0x3       # Polar Boundary 1 (EEJ?)
PEAK_MIN = 0x4  # Peak - Minimum of J_QD
PEAK_MAX = 0x5  # Peak - Maximum of J_QD


CDF_VARIABLE_ATTRIBUTES = {
    "Timestamp": {
        "DESCRIPTION": "UTC time",
        "UNITS": "ms",
        "FORMAT": " ",
    },
    "Latitude": {
        "DESCRIPTION": "Position in ITRF of peak - Geocentric latitude",
        "UNITS": "deg",
        "FORMAT": "F9.3",
    },
    "Longitude": {
        "DESCRIPTION": "Position in ITRF of peak - Geocentric longitude",
        "UNITS": "deg",
        "FORMAT": "F9.3",
    },
    "Latitude_QD": {
        "DESCRIPTION": "Quasi-dipole latitude",
        "UNITS": "deg",
        "FORMAT": "F9.3",
    },
    "Longitude_QD": {
        "DESCRIPTION": "Quasi-dipole longitude",
        "UNITS": "deg",
        "FORMAT": "F9.3",
    },
    "MLT": {
        "DESCRIPTION": "Magnetic local time (QD)",
        "UNITS": "h",
        "FORMAT": "F5.2",
    },
    "J_QD": {
        "DESCRIPTION": (
            "Peak horizontal sheet current intensity in the QD frame "
            "(positive in East QD direction). Set to NaN for boundaries."
        ),
        "UNITS": "A/km",
        "FORMAT": "F9.3",
    },
    "Flags": {
        "DESCRIPTION": "Quality indicator",
        "UNITS": "ms",
        "FORMAT": "Z04",
    },
    "PointType": {
        "DESCRIPTION": "Point Type: 0 - EB0, 1 - EB1, 2 - PB0, 3 - PB1, 4 - Minimum, 5 - Maximum, 255 - No-data",
        "UNITS": "ms",
        "FORMAT": "Z02",
    },
    "Timestamp_B": {
        "DESCRIPTION": "UTC time of peak (minimum and maximum) ground magnetic field disturbance.",
        "UNITS": "ms",
        "FORMAT": " ",
    },
    "Latitude_B": {
        "DESCRIPTIONS": "Position of peak (minimum and maximum) ground magnetic field disturbance in ITRF - Latitude",
        "UNITS": "deg",
        "FORMAT": "F9.3",
    },
    "Longitude_B": {
        "DESCRIPTIONS": "Position of peak (minimum and maximum) ground magnetic field disturbance in ITRF - Longitude",
        "UNITS": "deg",
        "FORMAT": "F9.3",
    },
    "B_NEC": {
        "DESCRIPTIONS": "Peak ground magnetic field disturbance, NEC frame.",
        "UNITS": "nT",
        "FORMAT": "F9.3",
    },
}


class CommandError(Exception):
    """ Command error exception. """


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <input> [<output>]" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Convert AEJxPBL products to a simple time-series.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    argv = argv + [None]
    try:
        input_ = argv[1]
        output = argv[2]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return input_, output or input_


def main(filename_input, filename_output):
    """ main subroutine """
    filename_tmp = filename_output + ".tmp.cdf"

    if exists(filename_tmp):
        remove(filename_tmp)

    try:
        convert_aej_pb(filename_input, filename_tmp)
        if exists(filename_tmp):
            print("%s -> %s" % (filename_input, filename_output))
            rename(filename_tmp, filename_output)
        else:
            print("%s skipped" % filename_input)
    finally:
        if exists(filename_tmp):
            remove(filename_tmp)


def convert_aej_pb(filename_input, filename_output):
    """ Convert AEB product. """
    with cdf_open(filename_input) as cdf_src:
        if RE_AEJ_PBL_2F.match(str(cdf_src.attrs.get("File_Type", ""))):
            convert_func = convert_cdf_aej_pbl_2f
        elif RE_AEJ_PBS_2F.match(str(cdf_src.attrs.get("TITLE", ""))[:18]):
            print(str(cdf_src.attrs.get("TITLE", ""))[:18])
            convert_func = convert_cdf_aej_pbs_2f
        else:
            return
        with cdf_open(filename_output, "w") as cdf_dst:
            convert_func(cdf_dst, cdf_src)


def convert_cdf_aej_pbs_2f(cdf_dst, cdf_src):
    """ Convert AEJxPBS_2F product. """
    _copy_attributes(cdf_dst, cdf_src)
    _update_creator(cdf_dst)
    cdf_dst.attrs["File_Type"] = str(cdf_dst.attrs["TITLE"])[8:18] + ":VirES"
    _convert_cdf_aej_pb_common(cdf_dst, cdf_src)


def convert_cdf_aej_pbl_2f(cdf_dst, cdf_src):
    """ Convert AEJxPBL_2F product. """
    # metadata
    _copy_attributes(cdf_dst, cdf_src)
    _update_creator(cdf_dst)
    cdf_dst.attrs["File_Type"] = str(cdf_dst.attrs["File_Type"]) + ":VirES"
    idx = _convert_cdf_aej_pb_common(cdf_dst, cdf_src)
    j__ = _concatenate_arrays([
        full(cdf_src['t_EB'].shape, nan),
        full(cdf_src['t_PB'].shape, nan),
        cdf_src['J'][...],
    ])
    cdf_dst.new("J_QD", j__[idx], CDF_DOUBLE, **COMMON_PARAM)

    for variable in cdf_dst:
        cdf_dst[variable].attrs = CDF_VARIABLE_ATTRIBUTES.get(variable, {})


def _convert_cdf_aej_pbs_b(cdf_dst, cdf_src):
    time = _merge_data(cdf_src, ['t_Peak'])
    lat = _merge_data(cdf_src, ['Latitude_B'])
    lon = _merge_data(cdf_src, ['Longitude_B'])
    b_nec = zeros((time.shape[0], 3))
    b_nec[:, 0:2] = _merge_data(cdf_src, ['B'])

    # sort data by time
    idx = argsort(time)

    # save variables
    cdf_dst.new("Timestamp_B", time[idx], CDF_EPOCH, **COMMON_PARAM)
    cdf_dst.new("Latitude_B", lat[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("Longitude_B", lon[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("B_NEC", b_nec[idx], CDF_DOUBLE, **COMMON_PARAM)

    for variable in cdf_dst:
        cdf_dst[variable].attrs = CDF_VARIABLE_ATTRIBUTES.get(variable, {})


def _convert_cdf_aej_pb_common(cdf_dst, cdf_src):
    # data
    time = _merge_data(
        cdf_src, ['t_EB', 't_PB', 't_Peak']
    )
    lat = _merge_data(
        cdf_src, ['Latitude_EB', 'Latitude_PB', 'Latitude_Peak']
    )
    lon = _merge_data(
        cdf_src, ['Longitude_EB', 'Longitude_PB', 'Longitude_Peak']
    )
    lat_qd = _merge_data(
        cdf_src, ['Latitude_EB_QD', 'Latitude_PB_QD', 'Latitude_Peak_QD']
    )
    lon_qd = _merge_data(
        cdf_src, ['Longitude_EB_QD', 'Longitude_PB_QD', 'Longitude_Peak_QD']
    )
    mlt = _merge_data(
        cdf_src, ['MLT_EB', 'MLT_PB', 'MLT_Peak']
    )
    point_type = _concatenate_arrays([
        broadcast_to(array([EB0, EB1], 'uint8'), cdf_src['t_EB'].shape),
        broadcast_to(array([PB0, PB1], 'uint8'), cdf_src['t_PB'].shape),
        broadcast_to(array([PEAK_MIN, PEAK_MAX], 'uint8'), cdf_src['t_Peak'].shape),
    ])
    flags = concatenate([
        cdf_src['Flags' if 'Flags' in cdf_src else 'FLags'][...]
    ] * 6)

    # filter out invalid locations
    idx = logical_not(logical_or(isnan(lat), isnan(lon))).nonzero()[0]

    # sort index by time
    idx = idx[argsort(time[idx])]

    # save variables
    cdf_dst.new("Timestamp", time[idx], CDF_EPOCH, **COMMON_PARAM)
    cdf_dst.new("Latitude", lat[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("Longitude", lon[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("Latitude_QD", lat_qd[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("Longitude_QD", lon_qd[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("MLT", mlt[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("Flags", flags[idx], CDF_UINT1, **COMMON_PARAM)
    cdf_dst.new("PointType", point_type[idx], CDF_UINT2, **COMMON_PARAM)

    return idx

def _merge_data(cdf, variables):
    return _concatenate_arrays([
        cdf.raw_var(variable)[...] for variable in variables
    ])


def _concatenate_arrays(arrays):
    return concatenate(list(chain.from_iterable(
        [item[:, i] for i in range(item.shape[1])]
        for item in arrays
    )))


def _update_creator(cdf):
    for key in ["Creator", "Creation_Date"]:
        if key in cdf.attrs:
            del cdf.attrs[key]

    cdf.attrs.update({
        "CREATOR": CDF_CREATOR,
        "CREATED": (
            datetime.utcnow().replace(microsecond=0)
        ).isoformat() + "Z",
    })


def _copy_attributes(cdf_dst, cdf_src):
    cdf_dst.attrs.update(cdf_src.attrs)


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
