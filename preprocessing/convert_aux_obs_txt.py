#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Convert ground observatory data from TXT to CDF file format.
#
# Author: Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2020 EOX IT Services GmbH
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
import ctypes
from datetime import datetime, timedelta
from os import remove, rename
from os.path import basename, exists, splitext
from numpy import unique, concatenate, datetime64, asarray
import spacepy
from spacepy import pycdf


GZIP_COMPRESSION = pycdf.const.GZIP_COMPRESSION
GZIP_COMPRESSION_LEVEL4 = ctypes.c_long(4)
GZIP_COMPRESSION_LEVEL = GZIP_COMPRESSION_LEVEL4

CDF_CREATOR = 'EOX:convert_aux_obs_txt.py [%s-%s, libcdf-%s]' % (
    spacepy.__name__, spacepy.__version__,
    '%s.%s.%s-%s' % tuple(
        v if isinstance(v, int) else v.decode('ascii')
        for v in pycdf.lib.version
    )
)


CDF_CHAR_TYPE = pycdf.const.CDF_CHAR.value
CDF_EPOCH_TYPE = pycdf.const.CDF_EPOCH.value
CDF_DOUBLE_TYPE = pycdf.const.CDF_DOUBLE.value
CDF_UINT1_TYPE = pycdf.const.CDF_UINT1.value

CDF_COMMON_ATTRIBUTES = {
    'TITLE': (
        'ESA Swarm level 2 auxiliary product: observatory definitive and/or '
        'quasi-definitive hourly-mean data (AUX_OBS_2_)'
    ),
    'ACKNOWLEDGMENTS': (
        'The data presented in this product rely on data collected at '
        'magnetic observatories. We thank the national institutes that '
        'support them and INTERMAGNET for promoting high standards of '
        'magnetic observatory practice (www.intermagnet.org).'
    ),
}

CDF_VARIABLES = {
    'IAGA_code': {
        'type': {
            'type': CDF_CHAR_TYPE,
            'n_elements': 3,
            'dims': [],
        },
        'attrs': {
            'UNITS': '-',
            'DESCRIPTION': (
                'IAGA three letter observatory identification code '
                'associated with datum'
            ),
            'FORMAT': 'A3',
        }
    },
    'Quality': {
        'type': {
            'type': CDF_CHAR_TYPE,
            'n_elements': 1,
            'dims': [],
        },
        'attrs': {
            'UNITS': '-',
            'DESCRIPTION': 'Data quality: D for definitive and Q for quasi-definitive',
            'FORMAT': 'A1',
        }
    },
    'SensorIndex': {
        'type': {
            'type': CDF_UINT1_TYPE,
            'dims': [],
        },
        'attrs': {
            'UNITS': '-',
            'DESCRIPTION': 'Digit from the 4-character observatory code.',
            'FORMAT': 'I1',
        }
    },
    'Timestamp': {
        'type': {
            'type': CDF_EPOCH_TYPE,
            'dims': [],
        },
        'attrs': {
            'UNITS': '-',
            'DESCRIPTION': 'Date and time',
        }
    },
    'Longitude': {
        'type': {
            'type': CDF_DOUBLE_TYPE,
            'dims': [],
        },
        'attrs': {
            'UNITS': 'deg',
            'DESCRIPTION': 'Longitude',
            'FORMAT': 'F8.3',
        }
    },
    'Latitude': {
        'type': {
            'type': CDF_DOUBLE_TYPE,
            'dims': [],
        },
        'attrs': {
            'UNITS': 'deg',
            'DESCRIPTION': 'Geocentric latitude',
            'FORMAT': 'F7.3',
        }
    },
    'Radius': {
        'type': {
            'type': CDF_DOUBLE_TYPE,
            'dims': [],
        },
        'attrs': {
            'UNITS': 'm',
            'DESCRIPTION': 'Geocentric latitude',
            'FORMAT': 'F9.1',
        }
    },
    'B_NEC': {
        'type': {
            'type': CDF_DOUBLE_TYPE,
            'dims': [3],
        },
        'attrs': {
            'UNITS': 'nT',
            'DESCRIPTION': (
                'Geocentric-north, east, and geocentric-down component of '
                'magnetic field.  NaN values are used as placeholders for '
                'missing data.'
            ),
            'FORMAT': 'F9.2',
        }
    },
}


class CommandError(Exception):
    """ Command error exception. """


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <input> [<output>]" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Convert observatory data from TXT to CDF file format.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    argv = argv + [None]
    try:
        input_ = argv[1]
        output = argv[2]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return input_, output or get_output_filename(input_)


def main(filename_input, filename_output):
    """ main subroutine """

    data = read_aux_obs_txt(filename_input)

    filename_tmp = filename_output + ".tmp.cdf"

    if exists(filename_tmp):
        remove(filename_tmp)

    try:
        write_aux_obs_cdf(filename_tmp, data, filename_input)
        if exists(filename_tmp):
            print("%s -> %s" % (filename_input, filename_output))
            rename(filename_tmp, filename_output)
        else:
            print("%s skipped" % filename_input)
    finally:
        if exists(filename_tmp):
            remove(filename_tmp)


def get_obs_index_and_ranges(data):
    """ Get index sorting the arrays by observatory and time. """
    times = data['Timestamp']
    codes = data['IAGA_code'].astype('U')
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
    return [str(code) for code in unique(codes)]


def write_aux_obs_cdf(filename, data, filename_input):
    """ Write AUX_OBS data to a new CDF file. """
    index, ranges = get_obs_index_and_ranges(data)

    attributes = {}
    attributes.update(CDF_COMMON_ATTRIBUTES)
    attributes.update({
        'ORIGINAL_PRODUCT_NAME': splitext(basename(filename_input))[0],
        'IAGA_CODES': list(ranges),
        'INDEX_RANGES': list(ranges.values()),
        'CREATOR': CDF_CREATOR,
        'CREATED': (
            datetime.utcnow().replace(microsecond=0)
        ).isoformat() + 'Z',
    })

    with cdf_open(filename, "w") as cdf:
        cdf.attrs.update(attributes)
        for variable, values in data.items():
            _write_variable(cdf, variable, values[index, ...])


def _write_variable(cdf, variable, data):
    type_info = CDF_VARIABLES[variable]['type']
    cdf.new(
        variable, _convert_data(data, type_info['type']),
        compress=GZIP_COMPRESSION, compress_param=GZIP_COMPRESSION_LEVEL,
        **type_info
    )

    attrs = CDF_VARIABLES[variable].get('attrs')
    if attrs:
        cdf[variable].attrs.update(attrs)


def _convert_data(data, cdf_type):
    if cdf_type == CDF_EPOCH_TYPE:
        return CdfTypeEpoch.encode(data)
    return data


def read_aux_obs_txt(filename):
    """ Parse hourly text file. """

    def _parse_record(record):
        obs, lat, lon, rad, year, month, day, utime, b_n, b_e, b_c = record
        quality = b'Q'
        iaga_code = obs[:3].encode('ascii')
        sensor_id = int(obs[3:])
        lat, lon, rad = float(lat), float(lon), float(rad)*1e3
        b_nec = float(b_n), float(b_e), float(b_c)
        timestamp = datetime64((
            datetime(int(year), int(month), int(day)) +
            timedelta(hours=float(utime))
        ).isoformat('T'), 'ms')
        return (iaga_code, sensor_id, timestamp, lat, lon, rad, b_nec, quality)

    def _parse_file(file_in):
        for line in file_in:
            # strip comments and whitespaces
            line = line.partition("#")[0].strip()
            # skip blank lines
            if line:
                yield _parse_record(line.split())

    def _records_to_arrays(records):
        fields = [
            'IAGA_code', 'SensorIndex', 'Timestamp',
            'Latitude', 'Longitude', 'Radius',
            'B_NEC', 'Quality',
        ]
        data = {field: [] for field in fields}
        for record in records:
            for field, value in zip(fields, record):
                data[field].append(value)
        return {field: asarray(values) for field, values in data.items()}

    with open(filename) as file_in:
        return _records_to_arrays(_parse_file(file_in))


def get_output_filename(filename):
    """ Get output filename from the input filename. """
    path, ext = splitext(filename)
    if ext != '.txt':
        path = filename
    return path + '.cdf'


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


class CdfTypeEpoch():
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


if __name__ == "__main__":
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        usage(sys.argv[0])
