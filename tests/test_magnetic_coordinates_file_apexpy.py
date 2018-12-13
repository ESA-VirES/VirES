#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Test Sun ephemeris calculated by the VirES for Swarm server.
# The values are compared with the values calculated by the apexpy package.
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

from __future__ import print_function
import sys
from os.path import basename
from math import pi
from datetime import datetime
from numpy import (
    vectorize, datetime64, timedelta64,
)
from apexpy import Apex
from util.cdf import load_cdf, CDFError
from util.csv import load_csv
from util.time_util import parse_datetime
from util.coords import spherical_to_geodetic, angle_difference
from util.testing import test_variables


RAD2DEG = 180./pi
DEG2RAD = pi/180.
DT_2000 = datetime(2000, 1, 1)
UNIX_EPOCH = datetime64("1970-01-01T00:00:00", 'us')
SECOND = timedelta64(1000000, 'us')
CDF_EPOCH_2000 = 63113904000000.0
S2DAYS = 1.0/(24*60*60)
MS2DAYS = 1.0/(24*60*60*1e3)
US2DAYS = 1.0/(24*60*60*1e6)

CSV_VALUE_PARSERS = {
    'id': str,
    'Spacecraft': str,
    'Timestamp': parse_datetime,
}

TESTED_VARIABLES = {
    "QDLat": {
        "uom": "deg", "atol": 0.5,
    },
    "QDLon": {
        "uom": "deg", "atol": 0.5,
        "sanitize": lambda v, r: angle_difference(v, r)
    },
    "MLT": {
        "uom": "h", "atol": 0.1,
        "sanitize": lambda v, r: angle_difference(v, r, period=24, offset=-12)
    },
}


class CommandError(Exception):
    """ Command error exception. """
    pass


def main(filename):
    """ main subroutine """

    print("Loading data ..."); sys.stdout.flush()
    data = load_data(filename)

    print("Calculating reference values ..."); sys.stdout.flush()
    reference = eval_magetic_coords(
        data['Timestamp'], data['Latitude'], data['Longitude'], data['Radius']
    )

    test_variables(data, reference, TESTED_VARIABLES)


def parse_inputs(argv):
    """ Parse input arguments. """
    try:
        filename = argv[1]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return filename,


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <tested_file>" % basename(exename), file=file)



def eval_magetic_coords(time, latitude, longitude, radius):
    """ Evaluate quasi dipole coordinates and magnetic local time. """
    geod_lat, geod_height = spherical_to_geodetic(latitude, radius)
    qd_lat, qd_lon, mlt = vectorize(eval_qd_and_mlt)(
        time, geod_lat, longitude, geod_height
    )
    #qd_lat, qd_lon, mlt = vectorize(eval_qd_and_mlt)(
    #    time, latitude, longitude, 450
    #)
    return {
        "Timestamp": time,
        "Latitude": latitude,
        "Longitude": longitude,
        "Radius": radius,
        "QDLat": qd_lat,
        "QDLon": qd_lon,
        "MLT": mlt,
    }


def eval_qd_and_mlt(time, lat, lon, height):
    """ QD-coors + MLT calculation. """
    apex = Apex(time)
    qdlat, qdlon = apex.geo2qd(lat, lon, height)
    mlt = apex.mlon2mlt(qdlon, time)
    return qdlat, qdlon, mlt


def load_data(filename):
    """ Load data from the input file. """
    try:
        return load_cdf(filename)
    except CDFError:
        pass
    return load_csv(filename, CSV_VALUE_PARSERS)


if __name__ == "__main__":
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        usage(sys.argv[0])
