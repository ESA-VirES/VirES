#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Calculate orbit direction boundary points in geographic and QD coordinates.
#
# Author: Martin Paces <martin.paces@eox.at>
#
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
import sys
import ctypes
from os import remove
from os.path import basename, exists
from datetime import datetime
from bisect import bisect_left, bisect_right
from numpy import (
    asarray, datetime64, timedelta64, concatenate, searchsorted, full, dtype,
)
import spacepy
from spacepy import pycdf
from eoxmagmod import mjd2000_to_decimal_year, eval_qdlatlon


SAMPLING = timedelta64(1000, 'ms')
MS2DAYS = 1.0/(24*60*60*1e3) # milliseconds to days scale factor
FLAG_START = 1
FLAG_END = -1
FLAG_MIDDLE = 0
FLAG_ASCENDING = 1
FLAG_DESCENDING = -1
FLAG_UNDEFINED = 0

FLAGS_ORBIT_DIRECTION = asarray([FLAG_DESCENDING, FLAG_ASCENDING], 'int8')

LABEL_GEO = "Orbit directions boundaries in geographic coordinates."
LABEL_MAG = "Orbit directions boundaries in quasi-dipole coordinates."

GZIP_COMPRESSION = pycdf.const.GZIP_COMPRESSION
GZIP_COMPRESSION_LEVEL1 = ctypes.c_long(1)
CDF_INT1_TYPE = pycdf.const.CDF_INT1.value
CDF_EPOCH_TYPE = pycdf.const.CDF_EPOCH.value

CDF_CREATOR = "EOX:%s [%s-%s, libcdf-%s]" % (
    basename(sys.argv[0]), spacepy.__name__, spacepy.__version__,
    "%s.%s.%s-%s" % tuple(
        v if isinstance(v, int) else v.decode('ascii')
        for v in pycdf.lib.version
    )
)


class CommandError(Exception):
    """ Command error exception. """
    pass


class DataIntegrityError(ValueError):
    """ Command error exception. """
    pass


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print(
        "USAGE: %s <manifest> <geo-output> <mag-output>"
        % basename(exename), file=file
    )
    print("\n".join([
        "DESCRIPTION:",
        "  Read Swarm MAGx_LR products write orbit direction boundary points "
        "  in geographic and magnetic coordinates.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    try:
        input_ = argv[1]
        output_geo = argv[2]
        output_mag = argv[3]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return input_, output_geo, output_mag


def main(manifest_filename, output_geo, output_mag):
    """ main subroutine. """
    print("registering products ...")
    products = open(manifest_filename) if manifest_filename != '-' else sys.stdin
    with products:
        product_registry = register_products(
            (f.strip() for f in products), gap_threshold=(SAMPLING * 1.5)
        )

    print("extracting boundary points ...")
    orbit_direction_boundaries = process_ranges(
        product_registry, sampling=SAMPLING
    )

    print("writing output ...")
    for odb, filename in zip(orbit_direction_boundaries, [output_geo, output_mag]):
        print(filename)
        odb.verify()
        write_orbit_direction_boudaries(filename, odb, product_registry)

    print("done.")


def write_orbit_direction_boudaries(filename, orbit_direction_boundaries,
                                    product_registry):
    """ Write orbit boundaries file. """
    if exists(filename):
        remove(filename)

    with cdf_open(filename, "w") as cdf:
        _write_orbit_direction_boudaries(
            cdf, orbit_direction_boundaries,
            product_registry, _get_product_id(filename)
        )


def _get_product_id(filename):
    """ construct id from a basename. """
    return basename(filename).rpartition('.')[0]


def _write_orbit_direction_boudaries(cdf, orbit_direction_boundaries,
                                     product_registry, product_id):
    """ Write orbit boundaries CDF file. """

    def _set_variable(cdf, variable, data, attrs):
        cdf_type, data_convertor = _TYPE_MAP[data.dtype]
        cdf.new(
            variable, data_convertor.encode(data),
            cdf_type, dims=data.shape[1:],
            compress=GZIP_COMPRESSION, compress_param=GZIP_COMPRESSION_LEVEL1,
        )
        cdf[variable].attrs.update(attrs)

    cdf.attrs.update({
        "TITLE": "%s (%s)" % (orbit_direction_boundaries.label, product_id),
        "CREATOR": CDF_CREATOR,
        "CREATED": (
            datetime.utcnow().replace(microsecond=0)
        ).isoformat() + "Z",
        "SOURCES": [
            _get_product_id(product)
            for _, _, product in product_registry.ranges
        ],
        "SOURCE_TIME_RANGES": [
            "%sZ/%sZ" % (start, end)
            for start, end, _ in product_registry.ranges
        ],
    })
    _set_variable(cdf, "Timestamp", orbit_direction_boundaries.times, {
        "UNITS": "-",
        "DESCRIPTION": "Time stamp",
    })

    _set_variable(cdf, "BoundaryType", orbit_direction_boundaries.type_flags, {
        "UNITS": "-",
        "DESCRIPTION": (
            "Boundary type (regular %s, block start %s, block end %s)" % (
                FLAG_MIDDLE, FLAG_START, FLAG_END
            )
        )
    })

    _set_variable(cdf, "OrbitDirection", orbit_direction_boundaries.pass_flags, {
        "UNITS": "-",
        "DESCRIPTION": (
            "Orbit direction after this point. "
            "(ascending %s, descending %s, undefined %s)" % (
                FLAG_ASCENDING, FLAG_DESCENDING, FLAG_UNDEFINED
            )
        )
    })


def process_ranges(product_registry, sampling):
    """ Process the product ranges. """
    previous_end = None
    previous_product = None
    accumulators = [
        GeoLatitudeExtrema(LABEL_GEO, end_margin=sampling),
        QDLatitudeExtrema(LABEL_MAG, end_margin=sampling),
    ]

    for start, end, product in product_registry.ranges:
        print("%s/%s %s" % (start, end, _get_product_id(product)))

        if previous_product is None:
            data = load_data_from_product(product, start, end)
            for item in accumulators:
                item.set_start(*data)

        elif start - previous_end > product_registry.gap_threshold:
            data = load_data_from_product(
                previous_product, previous_end - sampling, previous_end
            )
            for item in accumulators:
                item.set_end(*data)

            data = load_data_from_product(product, start, end)
            for item in accumulators:
                item.set_start(*data)
        else:
            data = load_data_from_products(
                [previous_product, product], start - 4*sampling, end
            )

        for item in accumulators:
            item.set_body(*data)

        previous_end, previous_product = end, product

    if previous_product is not None:
        data = load_data_from_product(
            previous_product, previous_end - 2*sampling, previous_end
        )
        for item in accumulators:
            item.set_end(*data)

    return accumulators


class ExtremaBase(object):
    """ base extrema class """

    def get_values(self, times, lats, lons, rads):
        """ Get values over which the extrema are searched """
        raise NotImplementedError

    @property
    def times(self):
        """ Get extrema times. """
        return concatenate(self.times_list)

    @property
    def type_flags(self):
        """ Get extrema times. """
        return concatenate(self.type_flags_list)

    @property
    def pass_flags(self):
        """ Get extrema times. """
        return concatenate(self.pass_flags_list)

    @staticmethod
    def _low_pass_filter(times, values):
        """ Simple smoothing filter.
        The low-pass filter trims the data by one element from each side.
        """
        new_times = times[1:-1]
        new_values = values[1:-1].copy()
        new_values += values[2:]
        new_values += values[:-2]
        new_values *= 1.0/3.0
        return new_times, new_values

    def verify(self):
        """ Verify data. """

        times = self.times
        type_flags = self.type_flags
        pass_flags = self.pass_flags

        if not (times[1:] > times[:-1]).all():
            raise DataIntegrityError("Times are not strictly increasing!")

        flags = type_flags[type_flags != FLAG_MIDDLE]
        if (
                (flags[::2] != FLAG_START).any() or
                (flags[1::2] != FLAG_END).any() or
                flags.size % 2 != 0
            ):
            raise DataIntegrityError("Block flags mismatch!")

        idx_start, = (type_flags == FLAG_START).nonzero()
        idx_stop, = (type_flags == FLAG_END).nonzero()

        if (pass_flags[idx_stop] != FLAG_UNDEFINED).any():
            raise DataIntegrityError("Orbit direction flags mismatch!")

        for start, stop in zip(idx_start, idx_stop):
            # flags within a block must be alternating directions
            flags = pass_flags[start:stop]
            if (
                    (flags == FLAG_UNDEFINED).any() or
                    (flags[1:] == flags[:-1]).any()
                ):
                raise DataIntegrityError("Orbit direction flags mismatch!")

    def __init__(self, label, end_margin):
        self.label = label
        self.margin = end_margin
        self.times_list = []
        self.type_flags_list = []
        self.pass_flags_list = []

    def _push(self, times, type_flags, pass_flags):
        self.times_list.append(asarray(times))
        self.type_flags_list.append(asarray(type_flags, 'int8'))
        self.pass_flags_list.append(asarray(pass_flags, 'int8'))

    def set_start(self, times, lats, lons, rads):
        """ Set start of a contiguous data acquisition. """
        # TODO: head filtering
        values = self.get_values(times[:3], lats[:3], lons[:3], rads[:3])
        is_ascending = values[1] - values[0] >= 0
        # start the block
        self._push(
            [times[0]], [FLAG_START], FLAGS_ORBIT_DIRECTION[[int(is_ascending)]]
        )
        # process the unfiltered head
        self._set_body(times[:3], values)

    def set_end(self, times, lats, lons, rads):
        """ Set end of a contiguous data acquisition. """
        values = self.get_values(times[-3:], lats[-3:], lons[-3:], rads[-3:])
        # process the unfiltered tail
        self._set_body(times[-3:], values)
        # terminate the block
        self._push(
            [times[-1] + self.margin], [FLAG_END], [FLAG_UNDEFINED],
        )

    def set_body(self, times, lats, lons, rads):
        """ Set body of a contiguous data acquisition. """
        values = self.get_values(times, lats, lons, rads)
        self._set_body(*self._low_pass_filter(times, values))

    def _set_body(self, times, values):
        extrema_times, ascending_pass = find_inversion_points(times, values)
        self._push(
            extrema_times,
            full(extrema_times.shape, FLAG_MIDDLE, 'int8'),
            FLAGS_ORBIT_DIRECTION[ascending_pass.astype('int')],
        )


class GeoLatitudeExtrema(ExtremaBase):
    """ Geographic latitude extrema class """
    def get_values(self, times, lats, lons, rads):
        return lats


class QDLatitudeExtrema(ExtremaBase):
    """ Geographic latitude extrema class """
    def get_values(self, times, lats, lons, rads):
        qd_lats, _ = eval_qdlatlon(
            lats, lons, rads*1e-3,
            mjd2000_to_decimal_year(datetime64_to_mjd2000(times))
        )
        return qd_lats


def datetime64_to_mjd2000(times):
    """ Convert datetime64 array to MJD2000. """
    return MS2DAYS*(
        asarray(times, 'M8[ms]') - datetime64('2000')
    ).astype('float64')


def find_inversion_points(times, lats):
    """ Find points of max/min. latitudes were the orbit direction gets
    inverted.
    """
    index = lookup_extrema(lats)
    ascending_pass = lats[index] < 0
    extrema_times = find_extrema(
        times.astype('float64'), lats, index
    ).astype(times.dtype)
    return extrema_times, ascending_pass


def lookup_extrema(values):
    """ Find indices of local extrema of the array values. """
    non_descending = values[1:] - values[:-1] >= 0
    return 1 + (non_descending[1:] != non_descending[:-1]).nonzero()[0]


def find_extrema(x, y, idx):
    """ Find approximate location of the extreme values. """
    #pylint: disable=invalid-name
    idx0, idx1, idx2 = idx - 1, idx, idx + 1
    x0 = x[idx0]
    a1 = x[idx1] - x0
    a2 = x[idx2] - x0
    y0 = y[idx0]
    b1 = y[idx1] - y0
    b2 = y[idx2] - y0
    a1b2, a2b1 = a1*b2, a2*b1
    return x0 + 0.5*(a1*a1b2 - a2*a2b1)/(a1b2 - a2b1)


def load_data_from_products(products, start, end):
    """ Load data concatenated from multiple products. """
    accm = ([], [], [], [])

    for product in products:
        data = load_data_from_product(product, start, end)
        for idx, data_item in enumerate(data):
            accm[idx].append(data_item)

    return tuple(concatenate(list_item) for list_item in accm)


def load_data_from_product(product, start, end):
    """ Load data concatenated from a single product. """
    with cdf_open(product) as cdf:
        times = CdfTypeEpoch.decode(cdf.raw_var("Timestamp")[...])
        slice_ = sorted_range(times, start, end)
        times = times[slice_]
        lats = cdf["Latitude"][slice_]
        lons = cdf["Longitude"][slice_]
        rads = cdf["Radius"][slice_]
    return times, lats, lons, rads


def sorted_range(data, start, end, left_closed=True, right_closed=True,
                 margin=0):
    """ Get a slice of a sorted data array matched by the given interval. """
    idx_start = searchsorted(data, start, 'left' if left_closed else 'right')
    idx_end = searchsorted(data, end, 'right' if right_closed else 'left')
    if margin > 0:
        idx_start = max(0, idx_start - margin)
        idx_end = idx_end + margin
    return slice(idx_start, idx_end)


def register_products(products, gap_threshold):
    """ Register input products. """
    product_registry = ProductRegistry(gap_threshold=gap_threshold)
    for product in products:
        product_registry.push(product)
    return product_registry


class ProductRegistry(object):
    """ Product registry class. """

    def __init__(self, gap_threshold):
        self.gap_threshold = gap_threshold
        self.ranges = []

    def select(self, start, end):
        """ Select registered products overlapped by the given time range. """
        idx_start = bisect_right(self.ranges, (start,)) - 1
        idx_end = bisect_right(self.ranges, (end,)) + 1
        return [
            (p_start, p_end, product)
            for p_start, p_end, product in self.ranges[idx_start:idx_end]
            if p_start <= end and p_end >= start
        ]

    def push(self, product, ranges=None):
        """ Push product to registry. """
        if ranges is None:
            ranges = self._extract_ranges(product)

        for start, end in ranges:
            self._push_range(start, end, product)

    def _extract_ranges(self, product):
        times = self._extract_times(product)

        if times.size < 1: # empty product
            return
        elif times.size < 2: # single point
            yield (times[0], times[-1])
        else: # multiple points
            gap_index, = (
                (times[1:] - times[:-1]) > self.gap_threshold
            ).nonzero()
            gap_index = [0] + list(gap_index + 1) + [times.size]

            ranges = (
                (start, gap_index[index+1]-1)
                for index, start in enumerate(gap_index[:-1])
            )
            for start, end in ranges:
                yield (times[start], times[end])

    @staticmethod
    def _extract_times(product):
        """ Extract time extent of a product. """
        with cdf_open(product) as cdf:
            times = CdfTypeEpoch.decode(cdf.raw_var("Timestamp")[...])
        return times

    def _push_range(self, start, end, product):
        idx_before = bisect_left(self.ranges, (start,))

        idx_after = idx_before
        while idx_after < len(self.ranges) and self.ranges[idx_after][0] < end:
            idx_after += 1

        if idx_after > idx_before:
            self.ranges = (
                self.ranges[:idx_before] + [
                    (start, end, product)
                ] + self.ranges[idx_after:]
            )
        else:
            self.ranges.insert(idx_before, (start, end, product))


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


class CdfTypeDummy(object):
    """ CDF dummy type conversions. """

    @staticmethod
    def decode(values):
        """ Pass trough and do nothing. """
        return values

    @staticmethod
    def encode(values):
        """ Pass trough and do nothing. """
        return values


class CdfTypeEpoch(object):
    """ CDF Epoch Time type conversions. """
    CDF_EPOCH_1970 = 62167219200000.0

    @classmethod
    def decode(cls, cdf_raw_time):
        """ Convert CDF raw time to datetime64[ms]. """
        return asarray(
            cdf_raw_time - cls.CDF_EPOCH_1970
        ).astype('datetime64[ms]')

    @classmethod
    def encode(cls, time):
        """ Convert datetime64[ms] to CDF raw time. """
        time = asarray(time, 'datetime64[ms]').astype('int64')
        return time + cls.CDF_EPOCH_1970


_TYPE_MAP = {
    dtype("int8"): (CDF_INT1_TYPE, CdfTypeDummy),
    dtype("datetime64[ms]"): (CDF_EPOCH_TYPE, CdfTypeEpoch),
}


if __name__ == "__main__":
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        usage(sys.argv[0])
