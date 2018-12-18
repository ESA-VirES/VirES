#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Coordinate system transformation and utilities.
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

from math import pi
from numpy import (
    asarray, mod, sin, cos, stack, sqrt, arctan2, hypot, fabs, copysign,
)

RAD2DEG = 180./pi
DEG2RAD = pi/180.
WGS84_A = 6378.137
WGS84_B = 6356.7523142
WGS84_EPS2 = (1.0 - (WGS84_B/WGS84_A)**2)


def angle_difference(angle1, angle2, period=360, offset=-180):
    """ Get difference of two angles (unit circle arc distance)."""
    return mod((angle1 - angle2) - offset, period) + offset


def spherical_to_cartesian(latitude, longitude):
    """ Convert spherical polar coordinates to a unit Cartesian vector. """
    lat = DEG2RAD * asarray(latitude)
    lon = DEG2RAD * asarray(longitude)
    cos_lat = cos(lat)
    return stack((cos(lon)*cos_lat, sin(lon)*cos_lat, sin(lat)), axis=-1)


def spherical_to_geodetic(latitude, radius):
    """ Convert spherical geocentric latitude and radius to geodetic WGS84
    latitude and height using the Ferrarri's solution.
    """
    latitude = DEG2RAD * latitude
    geodetic_latitude, height = _to_geodetic(
        radius*sin(latitude), radius*cos(latitude)
    )
    return RAD2DEG*geodetic_latitude, height


def _to_geodetic(z_coord, hypot_xy):
    """ Get geodetic coordinates calculated by the Ferrarri's solution. """
    #pylint: disable=invalid-name
    ee4 = WGS84_EPS2**2
    pa2 = (hypot_xy / WGS84_A)**2
    zt = (1.0 - WGS84_EPS2) * (z_coord / WGS84_A)**2
    rh = (pa2 + zt - ee4)/6.0
    ss = (0.25*ee4) * zt * pa2
    rh3 = rh**3
    tmp = rh3 + ss + sqrt(ss*(ss+2.0*rh3))
    tt = copysign(fabs(tmp)**(1.0/3.0), tmp)
    uu = rh + tt + rh**2 / tt
    vv = sqrt(uu**2 + ee4*zt)
    ww = (0.5*WGS84_EPS2) * (uu + vv - zt)/vv
    kp = 1.0 + WGS84_EPS2*(sqrt(uu + vv + ww**2) + ww)/(uu + vv)
    zkp = kp * z_coord
    return (
        arctan2(zkp, hypot_xy),
        hypot(hypot_xy, zkp)*(1.0/kp - 1.0 + WGS84_EPS2)/WGS84_EPS2
    )
