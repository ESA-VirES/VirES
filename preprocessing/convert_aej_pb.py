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

import re
import sys
import ctypes
from datetime import datetime, timedelta
from os import rename, remove
from os.path import basename, exists
from itertools import chain
from numpy import (
    concatenate, full, nan, broadcast_to, array, isnan, argsort, arange,
    #logical_or, logical_not, zeros,
)
import spacepy
from spacepy import pycdf

VERSION = "1.0.0"
RE_AEJ_PBL_2F = re.compile("^SW_OPER_AEJ[ABC]PBL_2F_")
RE_AEJ_PBS_2F = re.compile("^SW_OPER_AEJ[ABC]PBS_2F_")

MAX_TIME_SELECTION = timedelta(days=25*365.25) # max. time selection of ~25 years

GZIP_COMPRESSION = pycdf.const.GZIP_COMPRESSION
GZIP_COMPRESSION_LEVEL1 = ctypes.c_long(1)
GZIP_COMPRESSION_LEVEL9 = ctypes.c_long(9)
CDF_EPOCH = pycdf.const.CDF_EPOCH
CDF_DOUBLE = pycdf.const.CDF_DOUBLE
CDF_UINT1 = pycdf.const.CDF_UINT1
CDF_UINT2 = pycdf.const.CDF_UINT2

CDF_CREATOR = "EOX:convert_aej_bp-%s [%s-%s, libcdf-%s]" % (
    VERSION, spacepy.__name__, spacepy.__version__,
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

# point types - bit flags
#
#  bit   | False (0)           | True (1)       | Note
#  -----------------------------------------------------------
#  bit 0 | WEJ                 | EEJ            |
#  bit 1 | Peak                | Boundary       |
#  bit 2 | Equatorial boundary | Polar boundary | if bit 1 set
#  bit 3 | Segment start       | Segment end    | if bit 1 set
#

PEAK_MIN = 0x0    # 0000 WEJ Peak - Minimum of J (WEJ)
PEAK_MAX = 0x1    # 0001 EEJ Peak - Maximum of J (EEJ
WEJ_EB = 0x2      # 0010 WEJ Equatorial Boundary 0 (WEJ)
EEJ_EB = 0x3      # 0011 EEJ Equatorial Boundary 1 (EEJ)
WEJ_PB = 0x6      # 0110 WEJ Polar Boundary 0 (WEJ)
EEJ_PB = 0x7      # 0111 EEJ Polar Boundary 1 (EEJ)
EJ_TYPE_MASK = 0x1     # 0001
BOUNDARY_MASK = 0x2    # 0010
SEGMENT_END_MASK = 0x8 # 1000 segment end bit mask

POINT_TYPE = {
    PEAK_MIN: "PEAK_MIN",
    PEAK_MAX: "PEAK_MAX",
    WEJ_EB: "WEJ_EB",
    EEJ_EB: "EEJ_EB",
    WEJ_PB: "WEJ_PB",
    EEJ_PB: "EEJ_PB",
}

CDF_VARIABLE_MAP = {
    "J": "J_QD",
    "J_DF": "J_DF_SemiQD",
}

CDF_VARIABLE_ATTRIBUTES = {
    "Timestamp": {
        "DESCRIPTION": "Time of observation, UTC",
        "UNITS": "-",
        "FORMAT": " ",
    },
    "Latitude": {
        "DESCRIPTION": "Geocentric latitude in ITRF",
        "UNITS": "deg",
        "FORMAT": "F9.3",
    },
    "Longitude": {
        "DESCRIPTION": "Geocentric longitude in ITRF",
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
        "UNITS": "hour",
        "FORMAT": "F5.2",
    },
    "J_QD": {
        "DESCRIPTION": "Peak eastward sheet current intensity in QD frame",
        "UNITS": "A/km",
        "FORMAT": "F9.3",
    },
    "J_DF_SemiQD": {
        "DESCRIPTION": "Peak divergence-free sheet current density in SemiQD frame",
        "UNITS": "A/km",
        "FORMAT": "F9.3",
    },
    "Flags": {
        "DESCRIPTION": "Quality indicator",
        "UNITS": "-",
        "FORMAT": "Z04",
    },

    "PointType": {
        "DESCRIPTION": (
            "Point type (bit flags): "
            "0 - WEJ peak minimum, "
            "1 - EEJ peak maximum, "
            "2 - WEJ equatorial boundary (pair start), "
            "3 - EEJ equatorial boundary (pair start), "
            "6 - WEJ polar boundary (pair start), "
            "7 - EEJ polar boundary (pair start), "
            "10 - WEJ equatorial boundary (pair end), "
            "11 - EEJ equatorial boundary (pair end), "
            "14 - WEJ polar boundary (pair end), "
            "15 - EEJ polar boundary (pair end). "
            "Bits meaning: "
            "bit0 - WEJ|EEJ, "
            "bit1 - peak|boundary, "
            "bit2 - equatorial|polar, "
            "bit3 - pair-start|pair-end."
        ),
        "UNITS": " ",
        "FORMAT": "Z02",
    },
    "Timestamp_B": {
        "DESCRIPTION": "Time of peaks in ground magnetic field disturbance",
        "UNITS": " ",
        "FORMAT": " ",
    },
    "Latitude_B": {
        "DESCRIPTIONS": "Geodetic latitude of peaks in ground magnetic field disturbance",
        "UNITS": "deg",
        "FORMAT": "F9.3",
    },
    "Longitude_B": {
        "DESCRIPTIONS": "Geodetic longitude of peaks in ground magnetic field disturbance",
        "UNITS": "deg",
        "FORMAT": "F9.3",
    },
    "B": {
        "DESCRIPTIONS": "Peak value of the ground magnetic field disturbance, geodetic NE frame",
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
    """ Convert AEJxPB(L|S)_2F product. """

    with cdf_open(filename_input) as cdf_src:

        # detect product type
        file_name_attr = str(cdf_src.attrs.get("File_Name", ""))
        if RE_AEJ_PBL_2F.match(file_name_attr):
            convert_func = convert_cdf_aej_pbl_2f
        elif RE_AEJ_PBS_2F.match(file_name_attr):
            convert_func = convert_cdf_aej_pbs_2f
        else:
            return

        # check if the file has been already processed
        if str(cdf_src.attrs.get("File_Type", "")).endswith(":VirES"):
            return

        # convert product
        with cdf_open(filename_output, "w") as cdf_dst:
            convert_func(cdf_dst, cdf_src)


def convert_cdf_aej_pbs_2f(cdf_dst, cdf_src):
    """ Convert AEJxPBS_2F product. """
    _copy_attributes(cdf_dst, cdf_src)
    _update_creator(cdf_dst)
    _set_file_type(cdf_dst)
    _convert_cdf_aej_pb_common(cdf_dst, cdf_src, "J_DF")
    _convert_cdf_aej_pbs_b(cdf_dst, cdf_src)
    _set_variable_attrs(cdf_dst)


def convert_cdf_aej_pbl_2f(cdf_dst, cdf_src):
    """ Convert AEJxPBL_2F product. """
    # metadata
    _copy_attributes(cdf_dst, cdf_src)
    _update_creator(cdf_dst)
    _set_file_type(cdf_dst)
    _convert_cdf_aej_pb_common(cdf_dst, cdf_src, "J")
    _set_variable_attrs(cdf_dst)


def _set_variable_attrs(cdf_dst):
    for variable in cdf_dst:
        cdf_dst[variable].attrs = CDF_VARIABLE_ATTRIBUTES.get(variable, {})


def _set_file_type(cdf_dst):
    cdf_dst.attrs["File_Type"] = (
        str(cdf_dst.attrs.get("File_Type", "")) or
        str(cdf_dst.attrs["File_Name"])[8:18]
    ) + ":VirES"


def _convert_cdf_aej_pbs_b(cdf_dst, cdf_src):
    time = _merge_data(cdf_src, ['t_Peak'])
    lat = _merge_data(cdf_src, ['Latitude_B'])
    lon = _merge_data(cdf_src, ['Longitude_B'])
    b_ne = _merge_data(cdf_src, ['B'])

    # sort data by time
    idx = argsort(time)

    # save variables
    cdf_dst.new("Timestamp_B", time[idx], CDF_EPOCH, **COMMON_PARAM)
    cdf_dst.new("Latitude_B", lat[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("Longitude_B", lon[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("B", b_ne[idx], CDF_DOUBLE, **COMMON_PARAM)


def _convert_cdf_aej_pb_common(cdf_dst, cdf_src, j_variable):
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
        broadcast_to(array([WEJ_EB, EEJ_EB], 'uint8'), cdf_src['t_EB'].shape),
        broadcast_to(array([WEJ_PB, EEJ_PB], 'uint8'), cdf_src['t_PB'].shape),
        broadcast_to(array([PEAK_MIN, PEAK_MAX], 'uint8'), cdf_src['t_Peak'].shape),
    ])
    j__ = _concatenate_arrays([
        full(cdf_src['t_EB'].shape, nan),
        full(cdf_src['t_PB'].shape, nan),
        cdf_src[j_variable][...],
    ])
    flags = concatenate([
        cdf_src['Flags' if 'Flags' in cdf_src else 'FLags'][...]
    ] * 6)

    # filter out invalid locations
    #idx = logical_not(logical_or(isnan(lat), isnan(lon))).nonzero()[0]
    idx = arange(time.size)

    # sort index by time
    idx = idx[argsort(time[idx])]

    idx = _reorder_peaks_and_boundaries(idx, time, point_type, lat_qd)

    _tag_segment_end(idx, point_type)

    # save variables
    cdf_dst.new("Timestamp", time[idx], CDF_EPOCH, **COMMON_PARAM)
    cdf_dst.new("Latitude", lat[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("Longitude", lon[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("Latitude_QD", lat_qd[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("Longitude_QD", lon_qd[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("MLT", mlt[idx], CDF_DOUBLE, **COMMON_PARAM)
    cdf_dst.new("Flags", flags[idx], CDF_UINT1, **COMMON_PARAM)
    cdf_dst.new("PointType", point_type[idx], CDF_UINT2, **COMMON_PARAM)
    cdf_dst.new(CDF_VARIABLE_MAP[j_variable], j__[idx], CDF_DOUBLE, **COMMON_PARAM)


def _tag_segment_end(idx, point_type):
    """ Set the segment-end flag for the segment closing boundaries. """
    # tag WEJ end boundaries
    mask = point_type[idx] & (BOUNDARY_MASK|EJ_TYPE_MASK) == BOUNDARY_MASK
    point_type[idx[mask][1::2]] |= SEGMENT_END_MASK

    # EEJ end boundaries
    mask = point_type[idx] & (BOUNDARY_MASK|EJ_TYPE_MASK) == BOUNDARY_MASK|EJ_TYPE_MASK
    point_type[idx[mask][1::2]] |= SEGMENT_END_MASK


def _reorder_peaks_and_boundaries(idx_in, time, point_type, qdlat):
    """ Reorder same-time boundaries and peaks. """

    def _move_before(buf, ptypes):
        for pos, idx in enumerate(buf):
            if point_type[idx] in ptypes:
                buf.insert(pos, buf.pop(-1))
                break

    def _move_after(buf, ptypes):
        for idx in buf:
            if point_type[idx] in ptypes:
                buf.remove(idx)
                buf.append(idx)
                break

    def _reorder_it(it_idx):
        eej_flag, eej_is_valid = None, False
        wej_flag, wej_is_valid = None, False
        buf = []
        for idx in it_idx:

            ptype = point_type[idx]
            if buf and time[buf[-1]] < time[idx]:
                yield from buf
                buf = []
            buf.append(idx)

            is_valid = not isnan(qdlat[idx])

            if ptype in (EEJ_EB, EEJ_PB):
                if eej_flag is None:
                    eej_flag, eej_is_valid = ptype, is_valid
                    if len(buf) > 1:
                        # EEJ start after EEJ peak
                        _move_after(buf, (PEAK_MAX,))
                elif eej_flag != ptype:
                    eej_flag = None
                    if wej_flag is not None and len(buf) > 1:
                        if eej_is_valid and wej_is_valid:
                            # WEJ start or peak before EEJ start
                            _move_after(buf, (WEJ_EB, WEJ_PB))
                            _move_after(buf, (PEAK_MIN,))
                else:
                    print("WARNING: misplaced EEJ boundary at %s!" % time[idx])

            elif ptype == PEAK_MAX:
                if eej_flag is None and len(buf) > 1:
                    # EEJ peak after EEJ end
                    _move_before(buf, (EEJ_EB, EEJ_PB))

            elif ptype in (WEJ_EB, WEJ_PB):
                if wej_flag is None:
                    wej_flag, wej_is_valid = ptype, is_valid
                    if len(buf) > 1:
                        # if WEJ start after WEJ peak
                        _move_after(buf, (PEAK_MIN,))
                elif wej_flag != ptype:
                    wej_flag = None
                    if eej_flag is not None and len(buf) > 1:
                        if eej_is_valid and wej_is_valid:
                            # EEJ start or peak before WEJ start
                            _move_after(buf, (EEJ_EB, EEJ_PB))
                            _move_after(buf, (PEAK_MAX,))
                else:
                    print("WARNING: misplaced WEJ boundary at %s!" % time[idx])

            elif ptype == PEAK_MIN:
                if wej_flag is None and len(buf) > 1:
                    # WEJ peak after WEJ end
                    _move_before(buf, (WEJ_EB, WEJ_PB))

        yield from buf

    return array(list(_reorder_it(iter(idx_in))))


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
