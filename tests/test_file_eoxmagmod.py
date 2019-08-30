#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Test Sun ephemeris, magnetic coordinates and dipole axis parameters calculated
# by the VirES for Swarm server. The values are compared with the values
# calculated by the eoxmagmod package.
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
from datetime import datetime
from math import pi
from numpy import empty, stack, ones, vectorize, arcsin, arctan2
from eoxmagmod import (
    mjd2000_to_decimal_year, eval_mlt, eval_qdlatlon_with_base_vectors,
    sunpos, convert, GEOCENTRIC_SPHERICAL, GEOCENTRIC_CARTESIAN,
    vnorm,
)
from eoxmagmod.magnetic_model.loader_shc import load_coeff_shc
from eoxmagmod.data import IGRF12
from util.cdf import load_cdf, CDFError, read_time_as_mjd2000
from util.csv import load_csv
from util.vector import vector_angle
from util.time_util import parse_datetime
from util.coords import angle_difference
from util.testing import test_variables


RAD2DEG = 180./pi
DT_2000 = datetime(2000, 1, 1)
S2DAYS = 1.0/(24*60*60)

CDF_VARIABLE_READERS = {
    "Timestamp": read_time_as_mjd2000,
}

CSV_VALUE_PARSERS = {
    'id': str,
    'Spacecraft': str,
    'Timestamp': (
        lambda v: S2DAYS * (parse_datetime(v) - DT_2000).total_seconds()
    ),
}

TESTED_VARIABLES = {
    "SunDeclination": {
        "uom": "deg", "atol": 1e-3
    },
    "SunLongitude": {
        "uom": "deg", "atol": 1e-3,
        "sanitize": lambda v, r: angle_difference(v, r)
    },
    "SunHourAngle": {
        "uom": "deg", "atol": 1e-3,
        "sanitize": lambda v, r: angle_difference(v, r)
    },
    "SunVector": {
        "uom": "deg", "atol": 1e-3,
        "sanitize": lambda v, r: vector_angle(v, r)
    },
    "SunZenithAngle": {
        "uom": "deg", "atol": 1e-3,
    },
    "SunAzimuthAngle": {
        "uom": "deg", "atol": 1e-3,
        "sanitize": lambda v, r: angle_difference(v, r)
    },
    "SunRightAscension": {
        "uom": "deg", "atol": 1e-3,
        "sanitize": lambda v, r: angle_difference(v, r)
    },
    "QDLat": {
        "uom": "deg", "atol": 1e-3,
    },
    "QDLon": {
        "uom": "deg", "atol": 1e-3,
        "sanitize": lambda v, r: angle_difference(v, r)
    },
    "QDBasis": {
        "uom": "", "atol": 1e-6,
    },
    "MLT": {
        "uom": "h", "atol": 1e-3,
        "sanitize": lambda v, r: angle_difference(v, r, period=24, offset=-12)
    },
    "DipoleAxisVector": {
        "uom": "deg", "atol": 1e-3,
        "sanitize": lambda v, r: vector_angle(v, r)
    },
    "NGPLatitude": {
        "uom": "deg", "atol": 1e-3
    },
    "NGPLongitude": {
        "uom": "deg", "atol": 1e-3,
        "sanitize": lambda v, r: angle_difference(v, r)
    },
    "DipoleTiltAngle": {
        "uom": "deg", "atol": 1e-3
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
    reference = {}
    reference.update(eval_sun_ephemeris(
        data['Timestamp'], data['Latitude'], data['Longitude'], data['Radius']
    ))
    reference.update(eval_magetic_coords(
        data['Timestamp'], data['Latitude'], data['Longitude'], data['Radius']
    ))
    reference.update(eval_dipole(
        data['Timestamp'], reference['SunVector']
    ))

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


def eval_dipole(mjd2000, sun_vector):
    """ Eval magnetic dipole parameters. """

    model_coefficients = load_coeff_shc(
        IGRF12, interpolate_in_decimal_years=True
    )

    def get_dipole_axis(time):
        """ Calculate north pointing unit vector of the dipole axis
        from the spherical harmonic coefficients.
        """
        coeff, _ = model_coefficients(time, max_degree=1)
        dipole_axis_ref = coeff[[2, 2, 1], [0, 1, 0]]
        dipole_axis_ref *= -1.0/vnorm(dipole_axis_ref)
        return tuple(dipole_axis_ref)

    dipole_axis = stack(vectorize(get_dipole_axis)(mjd2000), axis=-1)
    ngp_latitude = RAD2DEG * arcsin(dipole_axis[..., 2])
    ngp_longitude = RAD2DEG * arctan2(dipole_axis[..., 1], dipole_axis[..., 0])
    dipole_tilt_angle = RAD2DEG * arcsin((sun_vector * dipole_axis).sum(axis=1))

    return {
        "Timestamp": mjd2000,
        "DipoleAxisVector": dipole_axis,
        "NGPLatitude": ngp_latitude,
        "NGPLongitude": ngp_longitude,
        "DipoleTiltAngle": dipole_tilt_angle,
    }


def eval_magetic_coords(mjd2000, latitude, longitude, radius):
    """ Evaluate quasi dipole coordinates and magnetic local time. """
    qd_lat, qd_lon, f11, f12, f21, f22, _ = eval_qdlatlon_with_base_vectors(
        latitude, longitude, radius*1e-3, mjd2000_to_decimal_year(mjd2000)
    )
    mlt = eval_mlt(qd_lon, mjd2000)
    qdbasis = empty((mjd2000.size, 2, 2))
    qdbasis[:, 0, 0], qdbasis[:, 0, 1] = f11, f12
    qdbasis[:, 1, 0], qdbasis[:, 1, 1] = f21, f22

    return {
        "Timestamp": mjd2000,
        "Latitude": latitude,
        "Longitude": longitude,
        "Radius": radius,
        "QDLat": qd_lat,
        "QDLon": qd_lon,
        "QDBasis": qdbasis,
        "MLT": mlt,
    }


def eval_sun_ephemeris(mjd2000, latitude, longitude, radius):
    """ Evaluate Sun ephemeris. """
    sslat, srasc, shang, sazm, sznt = sunpos(
        mjd2000, latitude, longitude, 1e-3*radius, 0
    )
    sslon = longitude - shang
    svect = convert(
        stack((sslat, sslon, ones(mjd2000.size)), axis=1),
        GEOCENTRIC_SPHERICAL, GEOCENTRIC_CARTESIAN
    )

    return {
        "Timestamp": mjd2000,
        "Latitude": latitude,
        "Longitude": longitude,
        "SunDeclination": sslat,
        "SunRightAscension": srasc,
        "SunHourAngle": shang,
        "SunLongitude": sslon,
        "SunVector": svect,
        "SunZenithAngle": sznt,
        "SunAzimuthAngle": sazm,
    }


def load_data(filename):
    """ Load data from the input file. """
    try:
        return load_cdf(filename, CDF_VARIABLE_READERS)
    except CDFError:
        pass
    return load_csv(filename, CSV_VALUE_PARSERS)


if __name__ == "__main__":
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        usage(sys.argv[0])
