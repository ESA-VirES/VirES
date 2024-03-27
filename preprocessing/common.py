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
#from logging import getLogger, DEBUG, StreamHandler, Formatter
import logging
import logging.handlers
import datetime
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

LOG_LEVELS = {
    "NONE": logging.CRITICAL + 10,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}
DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DEFAULT_LOG_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

class CommandError(Exception):
    """ Command error exception. """



class FormatterUTC(logging.Formatter):
    """ Custom log formatter class logging with UTC timestamps with sub-second
    precision.
    """
    converter = datetime.datetime.utcfromtimestamp

    def formatTime(self, record, datefmt=None):
        """ Return the creation time of the specified LogRecord as formatted
        text.

        Note that this method uses the `datetime.datetime.strftime()` method
        rather then the `time.strftime` used by the default `logging.Formatter`
        which if not able to format times with sub-second precision.
        """
        dts = self.converter(record.created)
        return dts.strftime(datefmt) if datefmt else dts.isoformat(" ")


def setup_logging(level=logging.DEBUG, stream=sys.stderr):
    """ Setup logging stream handler.
    Kept for backward compatibility. Deprecated. Will be removed in the future.
    """
    init_console_logging(log_level=level, stream=stream)


def init_console_logging(log_level=logging.INFO,
                         log_format=DEFAULT_LOG_FORMAT,
                         log_time_format=DEFAULT_LOG_TIME_FORMAT,
                         stream=sys.stderr):
    """ Initialize console logging. """
    log_level = LOG_LEVELS.get(log_level, log_level)
    formatter = FormatterUTC(log_format, log_time_format)
    logger = logging.getLogger()
    logger.setLevel(min(logger.level, log_level))
    logger.addHandler(_setup_log_handler(
        handler=logging.StreamHandler(stream),
        formatter=formatter,
        log_level=log_level,
    ))


def init_file_logging(log_file, log_level=logging.INFO,
                      log_format=DEFAULT_LOG_FORMAT,
                      log_time_format=DEFAULT_LOG_TIME_FORMAT):
    """ Initialize file logging. """
    if not log_file:
        return
    log_level = LOG_LEVELS.get(log_level, log_level)
    formatter = FormatterUTC(log_format, log_time_format)
    logger = logging.getLogger()
    logger.setLevel(min(logger.level, log_level))
    logger.addHandler(_setup_log_handler(
        handler=logging.handlers.WatchedFileHandler(log_file),
        formatter=formatter,
        log_level=log_level,
    ))


def _setup_log_handler(handler, formatter, log_level):
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    return handler


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
