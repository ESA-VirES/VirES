#-------------------------------------------------------------------------------
#
#  Various CDF handling utilities.
#
# Authors:  Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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

from spacepy.pycdf import CDF, const

CDF_EPOCH_TYPE = const.CDF_EPOCH.value
CDF_EPOCH_2000 = 63113904000000.0


def load_cdf(filename, variables=None):
    """ Load data from a CDF and convert time-stamps to MJD2000. """
    data = {}
    with CDF(filename) as cdf:
        for key in variables or cdf:
            data[key] = raw_var_to_array(cdf.raw_var(key))
    return data


def raw_var_to_array(raw_var):
    """ Extract CDF variable """
    data = raw_var[...]
    if raw_var.type() == CDF_EPOCH_TYPE:
        data = cdf_epoch_to_mjd2000(data)
    return data


def cdf_epoch_to_mjd2000(raw_time):
    """ Convert CDF epoch to MJD2000. """
    return (raw_time - CDF_EPOCH_2000) / 86400000.0
