#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Perform the delayed 20min averaging of the OMNI 1min data.
#
# (20min window box-car filter with 10min delay)
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
from datetime import datetime
from os import makedirs, remove
from os.path import basename, splitext, join, exists
from numpy import concatenate, copy
from numpy.lib.stride_tricks import as_strided
import spacepy
from spacepy import pycdf

TIME_VARIABLE = 'Epoch'
VARIABLES = ['BY_GSM', 'BZ_GSM', 'flow_speed', 'Vx', 'Vy', 'Vz']
REQUIRED_SAMPLING = 60000

CDF_EPOCH = pycdf.const.CDF_EPOCH.value
CDF_DOUBLE = pycdf.const.CDF_DOUBLE.value
CDF_UINT1 = pycdf.const.CDF_UINT1.value
GZIP_COMPRESSION = pycdf.const.GZIP_COMPRESSION
GZIP_COMPRESSION_LEVEL1 = ctypes.c_long(1)
GZIP_COMPRESSION_LEVEL9 = ctypes.c_long(9)
CDF_CREATOR = "EOX:average_omni_hr_1min.py [%s-%s, libcdf-%s]" % (
    spacepy.__name__, spacepy.__version__,
    "%s.%s.%s-%s" % tuple(
        v if isinstance(v, int) else v.decode('ascii')
        for v in pycdf.lib.version
    )
)

METADATA = {
    'Epoch': {
        'type': CDF_EPOCH,
        'attributes': {
            "DESCRIPTION": "Epoch time",
            "UNITS": "-",
        },
    },
    "BY_GSM": {
        "type": CDF_DOUBLE,
        "nodata": 9999.99,
        "attributes": {
            "DESCRIPTION": "1AU IP By (nT), GSM",
            "UNITS": "nT"
        }
    },
    "BZ_GSM": {
        "type": CDF_DOUBLE,
        "nodata": 9999.99,
        "attributes": {
            "DESCRIPTION": "1AU IP Bz (nT), GSM",
            "UNITS": "nT"
        }
    },
    "Vx": {
        "type": CDF_DOUBLE,
        "nodata": 99999.9,
        "attributes": {
            "DESCRIPTION": "Vx Velocity, GSE",
            "UNITS": "km/s"
        }
    },
    "Vy": {
        "type": CDF_DOUBLE,
        "nodata": 99999.9,
        "attributes": {
            "DESCRIPTION": "Vy Velocity, GSE",
            "UNITS": "km/s"
        }
    },
    "Vz": {
        "type": CDF_DOUBLE,
        "nodata": 99999.9,
        "attributes": {
            "DESCRIPTION": "Vz Velocity, GSE",
            "UNITS": "km/s"
        }
    },
    "flow_speed": {
        "type": CDF_DOUBLE,
        "nodata": 99999.9,
        "attributes": {
            "DESCRIPTION": "flow speed, GSE",
            "UNITS": "km/s"
        }
    }
}

METADATA.update({
    "Count_" + variable: {
        "type": CDF_UINT1,
        "attributes": {
            "DESCRIPTION": "Averaging window number of samples of %s" % variable,
            "UNITS": "-"
        }
    }
    for variable in VARIABLES
})


class CommandError(Exception):
    """ Command error exception. """


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <output-dir> [<input-file-list>]" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Perform the delayed 20min averaging of the OMNI 1min data. ",
        "  (20min window box-car filter with 10min delay) ",
        "  The input files are passed either from the standard input (default) ",
        "  or via file. The output files are written in the given output "
        "  directory",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    argv = argv + ['-']
    try:
        output_dir = argv[1]
        input_files = argv[2]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return output_dir, input_files


def main(output_dir, input_files):
    """ Main function. """

    def _get_output_filename(filename, suffix):
        base, ext = splitext(basename(filename))
        return join(output_dir, "%s%s%s" % (base, suffix, ext))


    makedirs(output_dir, exist_ok=True)

    file_list = sys.stdin if input_files == "-" else open(input_files)
    with file_list:
        previous = None
        for input_ in (line.strip() for line in file_list):
            output = _get_output_filename(input_, "_avg20min_delay10min")
            print("%s -> %s" % (input_, output))
            process_file(output, input_, previous)
            previous = input_


def process_file(filename_out, filename_in, filename_in_previous=None):
    """ Process single file. """
    sources = [basename(filename_in)]
    time_in, data_in = read_data(filename_in)
    if filename_in_previous:
        time_prev, data_prev = read_data(filename_in_previous, slice(-20, None))
        time_in, data_in = merge_data((time_prev, time_in), (data_prev, data_in))
        sources = [basename(filename_in_previous)] + sources
    check_timeline(time_in)
    time_out, data_out = process_data(time_in, data_in)
    write_data(filename_out, time_out, data_out, {
        "TITLE": "OMNI HR 1min, 20min window average with 10min delay",
        "SOURCES": sources,
    })

def process_data(time, data):
    """ Perform the actual averaging. """
    result = {}
    for variable in VARIABLES:
        input_ = data[variable]
        nodata = METADATA[variable]['nodata']
        output, counts = boxcar(input_, input_ != nodata, 20)
        result[variable] = output
        result["Count_" + variable] = counts
    return time[20:], result

def boxcar(data, mask, size):
    """ Boxcar filter. """
    def _reshape(array):
        return as_strided(
            array,
            shape=(array.size - size, size + 1),
            strides=(array.itemsize, array.itemsize),
            writeable=False
        )
    data = copy(data)
    data[~mask] = 0.0
    count = _reshape(mask).sum(axis=1)
    average = _reshape(data).sum(axis=1) / count
    return average, count


def write_data(filename, time, data, extra_attrs=None):
    """ Write data to the output file. """
    with cdf_open(filename, "w") as cdf:
        _write_global_attrs(cdf, extra_attrs)
        _set_variable(cdf, TIME_VARIABLE, time)
        for variable in data:
            _set_variable(cdf, variable, data[variable])


def _set_variable(cdf, variable, data):
    meta = METADATA[variable]
    cdf.new(
        variable, data, meta['type'], dims=data.shape[1:],
        compress=GZIP_COMPRESSION, compress_param=GZIP_COMPRESSION_LEVEL1,
    )
    cdf[variable].attrs.update(meta['attributes'])


def _write_global_attrs(cdf, extra_attrs=None):
    cdf.attrs.update({
        "CREATOR": CDF_CREATOR,
        "CREATED": (
            datetime.utcnow().replace(microsecond=0)
        ).isoformat() + "Z",
    })
    cdf.attrs.update(extra_attrs or {})


def read_data(filename, array_slice=Ellipsis):
    """ Read the input data. """
    with cdf_open(filename) as cdf:
        return cdf.raw_var(TIME_VARIABLE)[array_slice], {
            variable: cdf.raw_var(variable)[array_slice]
            for variable in VARIABLES
        }


def check_timeline(time):
    """ Check regular data sampling. """
    dtime = time[1:] - time[:-1]
    if (dtime != REQUIRED_SAMPLING).any():
        print("sampling:", dtime.min(), dtime.max())
        raise ValueError("Irregular sampling detected!")


def merge_data(time, data):
    """ Merge input data arrays. """
    return concatenate(time), {
        variable: concatenate([item[variable] for item in data])
        for variable in VARIABLES
    }


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
            remove(filename)
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
