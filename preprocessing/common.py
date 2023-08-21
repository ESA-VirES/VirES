#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Common shared data and subroutines.
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
import time
import ctypes
from logging import getLogger, DEBUG, StreamHandler, Formatter
from os.path import exists
import spacepy
from spacepy import pycdf
from numpy import asarray

SPACEPY_NAME = spacepy.__name__
SPACEPY_VERSION = spacepy.__version__
LIBCDF_VERSION = "%s.%s.%s-%s" % tuple(
    v if isinstance(v, int) else v.decode('ascii')
    for v in pycdf.lib.version
)

GZIP_COMPRESSION = pycdf.const.GZIP_COMPRESSION
GZIP_COMPRESSION_LEVEL1 = ctypes.c_long(1)
GZIP_COMPRESSION_LEVEL2 = ctypes.c_long(2)
GZIP_COMPRESSION_LEVEL3 = ctypes.c_long(3)
GZIP_COMPRESSION_LEVEL4 = ctypes.c_long(4)
GZIP_COMPRESSION_LEVEL5 = ctypes.c_long(5)
GZIP_COMPRESSION_LEVEL6 = ctypes.c_long(6)
GZIP_COMPRESSION_LEVEL7 = ctypes.c_long(7)
GZIP_COMPRESSION_LEVEL8 = ctypes.c_long(8)
GZIP_COMPRESSION_LEVEL9 = ctypes.c_long(9)

CDF_EPOCH = pycdf.const.CDF_EPOCH.value
CDF_EPOCH16 = pycdf.const.CDF_EPOCH16.value
CDF_TIME_TT2000 = pycdf.const.CDF_TIME_TT2000.value
CDF_FLOAT = pycdf.const.CDF_FLOAT.value
CDF_DOUBLE = pycdf.const.CDF_DOUBLE.value
CDF_REAL8 = pycdf.const.CDF_REAL8.value # CDF_DOUBLE != CDF_REAL8
CDF_REAL4 = pycdf.const.CDF_REAL4.value # CDF_FLOAT != CDF_REAL4
CDF_UINT1 = pycdf.const.CDF_UINT1.value
CDF_UINT2 = pycdf.const.CDF_UINT2.value
CDF_UINT4 = pycdf.const.CDF_UINT4.value
CDF_INT1 = pycdf.const.CDF_INT1.value
CDF_INT2 = pycdf.const.CDF_INT2.value
CDF_INT4 = pycdf.const.CDF_INT4.value
CDF_INT8 = pycdf.const.CDF_INT8.value
CDF_CHAR = pycdf.const.CDF_CHAR.value

CDF_TYPE_LABEL = {
    CDF_EPOCH: "CDF_EPOCH",
    CDF_EPOCH16: "CDF_EPOCH16",
    CDF_TIME_TT2000: "CDF_TIME_TT2000",
    CDF_FLOAT: "CDF_FLOAT",
    CDF_DOUBLE: "CDF_DOUBLE",
    CDF_REAL4: "CDF_REAL4",
    CDF_REAL8: "CDF_REAL8",
    CDF_UINT1: "CDF_UINT1",
    CDF_UINT2: "CDF_UINT2",
    CDF_UINT4: "CDF_UINT4",
    CDF_INT1: "CDF_INT1",
    CDF_INT2: "CDF_INT2",
    CDF_INT4: "CDF_INT4",
    CDF_INT8: "CDF_INT8",
    CDF_CHAR: "CDF_CHAR",
}


class CommandError(Exception):
    """ Command error exception. """


def setup_logging(level=DEBUG, stream=sys.stderr):
    """ Setup logging stream handler. """
    formatter = Formatter(
        fmt="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    formatter.converter = time.gmtime
    handler = StreamHandler(stream)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger = getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


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


class CdfTypeDummy():
    """ CDF dummy type conversions. """

    @staticmethod
    def decode(values):
        """ Pass trough and do nothing. """
        return values

    @staticmethod
    def encode(values):
        """ Pass trough and do nothing. """
        return values


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
