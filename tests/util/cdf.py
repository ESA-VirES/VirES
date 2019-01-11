#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# VirES CDF file reader
#
# Author: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
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

from os import remove
from os.path import exists
from shutil import copyfileobj
from tempfile import NamedTemporaryFile
from spacepy.pycdf import CDF, CDFError, const

CDF_EPOCH_TYPE = const.CDF_EPOCH.value
CDF_EPOCH_2000 = 63113904000000.0


def read_time_as_mjd2000(cdf, key):
    """ Read time as MJD2000. """
    raw_var = cdf.raw_var(key)
    return cdf_rawtime_to_mjd2000(raw_var[...], raw_var.type())


def cdf_rawtime_to_mjd2000(raw_time, cdf_type):
    """ Convert an array of CDF raw time values to array of MJD2000 values.
    """
    if cdf_type == CDF_EPOCH_TYPE:
        return (raw_time - CDF_EPOCH_2000) / 86400000.0
    else:
        raise TypeError("Unsupported CDF time type %r !" % cdf_type)


def parse_cdf(source, variable_readers=None, default_variable_reader=None,
              variables=None):
    """ Mimic CDF stream parsing. The input stream is grabbed and saved
    to a temporary file.
    """
    params = {"prefix": "vires_", "suffix": ".cdf", "delete": False}
    filename = None
    try:
        with NamedTemporaryFile(**params) as output:
            filename = output.name
            copyfileobj(source, output)
        data = load_cdf(
            filename, variable_readers, default_variable_reader, variables
        )
    finally:
        if filename and exists(filename):
            remove(filename)
    return data


def load_cdf(filename, variable_readers=None, default_variable_reader=None,
             variables=None):
    """ Load data from a CDF file. """

    if not default_variable_reader:
        default_variable_reader = lambda cdf, key: cdf[key][...]

    if not variable_readers:
        variable_readers = {}

    with CDF(filename) as cdf:
        return dict(
            (key, variable_readers.get(key, default_variable_reader)(cdf, key))
            for key in (variables or cdf) if key in cdf
        )
