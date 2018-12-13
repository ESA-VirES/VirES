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
    vectorize, datetime64, timedelta64, mod, sin, cos, arccos, arctan2,
)
from apexpy.helpers import subsol
from util.cdf import load_cdf, CDFError
from util.csv import load_csv
from util.time_util import parse_datetime
from util.vector import vector_angle
from util.coords import spherical_to_cartesian, angle_difference
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
    "SunDeclination": {
        "uom": "deg", "atol": 1e-2
    },
    "SunLongitude": {
        "uom": "deg", "atol": 1e-2,
        "sanitize": lambda v, r: angle_difference(v, r)
    },
    "SunHourAngle": {
        "uom": "deg", "atol": 1e-2,
        "sanitize": lambda v, r: angle_difference(v, r)
    },
    "SunVector": {
        "uom": "deg", "atol": 1e-2,
        "sanitize": lambda v, r: vector_angle(v, r)
    },
    "SunZenithAngle": {
        "uom": "deg", "atol": 1e-2,
    },
    "SunAzimuthAngle": {
        "uom": "deg", "atol": 1e-2,
        "sanitize": lambda v, r: angle_difference(v, r)
    },
    "SunRightAscension": {
        "uom": "deg", "atol": 1e-2,
        "sanitize": lambda v, r: angle_difference(v, r)
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
    reference = eval_sun_ephemeris(
        data['Timestamp'], data['Latitude'], data['Longitude']
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


def eval_sun_ephemeris(time, latitude, longitude):
    """ Evaluate Sun ephemeris. """
    sslat, sslon = vectorize(subsol)(time)
    gast = vectorize(eval_gmst)(time) # using mean instead of apparent ST
    svect = spherical_to_cartesian(sslat, sslon)
    shang = mod(longitude - sslon, 360)
    sazm, sznt = eval_sun_azimut_and_zenith(latitude, sslat, shang)
    return {
        "Timestamp": time,
        "Latitude": latitude,
        "Longitude": longitude,
        "SunDeclination": sslat,
        "SunRightAscension": mod(sslon + gast, 360),
        "SunHourAngle": shang,
        "SunLongitude": sslon,
        "SunVector": svect,
        "SunZenithAngle": sznt,
        "SunAzimuthAngle": sazm,
    }


def eval_gmst(time):
    """ Evaluate approximation of the Global Mean Sideral Time in degrees. """
    mjd2000 = S2DAYS * (time - DT_2000).total_seconds()
    gmst = 280.46061837 + 360.98564736629*(mjd2000 - 0.5)
    return mod(gmst, 360)


def eval_sun_azimut_and_zenith(latitude, declination, hour_angle):
    """ For the given local latitude, Sun declination and Sun hour angle
    in degrees calculate local Sun azimuth and zenith.
    """
    latitude = DEG2RAD * latitude
    declination = DEG2RAD * declination
    hour_angle = DEG2RAD * hour_angle

    sin_decl, cos_decl = sin(declination), cos(declination)
    sin_hang, cos_hang = sin(hour_angle), cos(hour_angle)
    sin_lat, cos_lat = sin(latitude), cos(latitude)

    zenith = arccos(sin_lat*sin_decl + cos_lat*cos_decl*cos_hang)
    azimuth = arctan2(
        -sin_hang*cos_decl, cos_lat*sin_decl - sin_lat*cos_decl*cos_hang
    )

    return RAD2DEG*azimuth, RAD2DEG*zenith


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
