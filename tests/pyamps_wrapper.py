#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# VirES integration tests - pyAMPS wrapper
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
#pylint: disable=missing-docstring,too-many-arguments

from datetime import datetime, timedelta
from numpy import nan, stack, empty, asarray
from pyamps import AMPS, get_B_space
from eoxmagmod import (
    mjd2000_to_decimal_year, convert,
    GEOCENTRIC_SPHERICAL, GEODETIC_ABOVE_WGS84,
)


EARTH_RADIUS = 6371.2 # reference radius Earth(km)
DT2000 = datetime(2000, 1, 1)


def mjd2000_to_datetime(mjd2000):
    return DT2000 + timedelta(days=mjd2000)


def datetime_to_mjd20000(dtobj):
    return (dtobj - DT2000).total_seconds() / 86400.0


def round_to_seconds(dtobj):
    return (
        dtobj.replace(microsecond=0) +
        timedelta(seconds=int(dtobj.microsecond >= 500000))
    )


def eval_associated_magnetic_model(epoch, time, latitude, longitude, radius,
                                   v_imf, by_imf, bz_imf, tilt, f107):
    timestamp = asarray([
        round_to_seconds(mjd2000_to_datetime(t)) for t in time
    ])

    geodetic_coordinates = convert(
        stack((latitude, longitude, radius), axis=-1),
        GEOCENTRIC_SPHERICAL, GEODETIC_ABOVE_WGS84
    )

    if time.size:
        b_e, b_n, b_u = get_B_space( #pylint: disable=unbalanced-tuple-unpacking
            time=timestamp,
            glat=geodetic_coordinates[:, 0],
            glon=geodetic_coordinates[:, 1],
            height=geodetic_coordinates[:, 2],
            v=v_imf,
            By=by_imf,
            Bz=bz_imf,
            tilt=tilt,
            f107=f107,
            epoch=float(mjd2000_to_decimal_year(epoch)),
            h_R=110,
            chunksize=1000,
        )
        b_nec = stack((b_n, b_e, -b_u), axis=-1)
    else:
        b_nec = empty((0, 3))

    return b_nec


def eval_ionospheric_current_model(qdlat, mlt, qdbasis,
                                   v_imf, by_imf, bz_imf, tilt, f107):
    model = AMPS(
        v=v_imf, By=by_imf, Bz=bz_imf,
        tilt=tilt, f107=f107,
        resolution=0, dr=90,
    )

    div_free_current_fcn = AMPS.get_divergence_free_current_function(
        model, qdlat, mlt
    )
    total_current = _rotate_from_qd_to_spherical_frame(
        AMPS.get_total_current(model, qdlat, mlt), qdbasis
    )
    upward_current = AMPS.get_upward_current(model, qdlat, mlt)
    upward_current[abs(qdlat) < 45] = nan

    return div_free_current_fcn, total_current, upward_current


def _rotate_from_qd_to_spherical_frame(vector, qdbasis):
    east, north = vector
    return stack((
        qdbasis[..., 0, 0] * east + qdbasis[..., 1, 0] * north,
        qdbasis[..., 0, 1] * east + qdbasis[..., 1, 1] * north
    ), axis=-1)
