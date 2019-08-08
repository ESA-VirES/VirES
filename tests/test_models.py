#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# VirES integration tests - model evaluation
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
# pylint: disable=too-many-lines
# pylint: disable=missing-docstring,line-too-long,too-many-ancestors
# pylint: disable=import-error,no-name-in-module,too-few-public-methods,too-many-locals
# pylint: disable=useless-object-inheritance

from unittest import TestCase, main
from math import pi
from datetime import timedelta
from numpy import array, stack, ones, broadcast_to, arcsin, arctan2, nan, empty
from numpy.testing import assert_allclose
from eoxmagmod import (
    vnorm, load_model_shc, load_model_shc_combined,
    mjd2000_to_decimal_year,
    eval_qdlatlon_with_base_vectors, eval_mlt,
    sunpos,
    convert, GEOCENTRIC_SPHERICAL, GEOCENTRIC_CARTESIAN,
    load_model_swarm_mma_2c_external,
    load_model_swarm_mma_2c_internal,
    load_model_swarm_mma_2f_geo_external,
    load_model_swarm_mma_2f_geo_internal,
    load_model_swarm_mio_external,
    load_model_swarm_mio_internal,
    ComposedGeomagneticModel,
)
from eoxmagmod.data import IGRF12, CHAOS6_STATIC, LCS1, MF7
from eoxmagmod.time_util import decimal_year_to_mjd2000_simple
from util.time_util import parse_datetime
from util.wps import (
    WpsPostRequestMixIn, WpsAsyncPostRequestMixIn,
    CsvRequestMixIn, CdfRequestMixIn,
)
from pyamps_wrapper import (
    eval_ionospheric_current_model,
    eval_associated_magnetic_model,
)

MCO_SHA_2C = "./data/SW_OPER_MCO_SHA_2C.shc"
MCO_SHA_2D = "./data/SW_OPER_MCO_SHA_2D.shc"
MCO_CHAOS6 = "./data/SW_OPER_MCO_CHAOS6.shc"
MLI_SHA_2C = "./data/SW_OPER_MLI_SHA_2C.shc"
MLI_SHA_2D = "./data/SW_OPER_MLI_SHA_2D.shc"
MIO_SHA_2C = "./data/SW_OPER_MIO_SHA_2C.txt"
MIO_SHA_2D = "./data/SW_OPER_MIO_SHA_2D.txt"
MMA_SHA_2C = "./data/SW_OPER_MMA_SHA_2C.cdf"
MMA_SHA_2F = "./data/SW_OPER_MMA_SHA_2F.cdf"
MMA_CHAOS6 = "./data/SW_OPER_MMA_CHAOS6.cdf"

RAD2DEG = 180.0/pi

START_TIME = parse_datetime("2016-01-01T23:50:00Z")
END_TIME = parse_datetime("2016-01-02T00:00:00Z")

#-------------------------------------------------------------------------------

class FetchDataCsvMixIn(CsvRequestMixIn, WpsPostRequestMixIn):
    template_source = "test_vires_fetch_data.xml"
    begin_time = START_TIME
    end_time = END_TIME


class FetchFilteredDataCsvMixIn(CsvRequestMixIn, WpsPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data.xml"
    begin_time = START_TIME
    end_time = END_TIME


class FetchFilteredDataCdfMixIn(CdfRequestMixIn, WpsPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data.xml"
    begin_time = START_TIME
    end_time = END_TIME


class AsyncFetchFilteredDataCsvMixIn(CsvRequestMixIn, WpsAsyncPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data_async.xml"
    begin_time = START_TIME
    end_time = END_TIME


class AsyncFetchFilteredDataCdfMixIn(CdfRequestMixIn, WpsAsyncPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data_async.xml"
    begin_time = START_TIME
    end_time = END_TIME

#-------------------------------------------------------------------------------

class AMPSIonosphericCurrentTestMixIn(object):
    variables = [
        "IMF_V", "IMF_BY_GSM", "IMF_BZ_GSM", "DipoleTiltAngle", "F10_INDEX",
        "QDLat", "MLT", "QDBasis",
        "DivergenceFreeCurrentFunction",
        "TotalCurrent",
        "UpwardCurrent",
    ]

    def test_ionospheric_current_model(self):
        request = self.get_request(
            begin_time=self.begin_time,
            end_time=self.end_time,
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        times = array(response["Timestamp"])

        qdlat = array(response["QDLat"])
        mlt = array(response["MLT"])
        qdbasis = array(response["QDBasis"])

        if times.size > 0:
            #median_time = times[times.size // 2]
            #idx = argmax(abs(times - median_time), axis=0)
            idx = times.size // 2

            v_imf = array(response["IMF_V"])[idx]
            by_gsm_imf = array(response["IMF_BY_GSM"])[idx]
            bz_gsm_imf = array(response["IMF_BZ_GSM"])[idx]
            tilt_angle = array(response["DipoleTiltAngle"])[idx]
            f107 = array(response["F10_INDEX"])[idx]
        else:
            v_imf = nan
            by_gsm_imf = nan
            bz_gsm_imf = nan
            tilt_angle = nan
            f107 = nan

        div_free_current_funct = array(response["DivergenceFreeCurrentFunction"])
        total_current = array(response["TotalCurrent"])
        upward_current = array(response["UpwardCurrent"])

        div_free_current_funct_ref, total_current_ref, upward_current_ref = (
            eval_ionospheric_current_model(
                qdlat, mlt, qdbasis, v_imf, by_gsm_imf, bz_gsm_imf,
                tilt_angle, f107
            )
        )

        assert_allclose(div_free_current_funct, div_free_current_funct_ref, atol=1e-6)
        assert_allclose(total_current, total_current_ref, atol=1e-5)
        assert_allclose(upward_current, upward_current_ref, atol=1e-6)


class TestFetchDataAMPSIonosphericCurrent(TestCase, AMPSIonosphericCurrentTestMixIn, FetchDataMixIn):
    pass


class TestFetchFilteredDataAMPSIonosphericCurrent(TestCase, AMPSIonosphericCurrentTestMixIn, FetchFilteredDataMixIn):
    pass


class TestAsyncFetchFilteredDataAMPSIonosphericCurrent(TestCase, AMPSIonosphericCurrentTestMixIn, AsyncFetchFilteredDataMixIn):
    pass

#-------------------------------------------------------------------------------


class AMPSAssociatedMagneticFieldTestMixIn(object):
    variables = [
        'IMF_V', 'IMF_BY_GSM', 'IMF_BZ_GSM', 'DipoleTiltAngle', 'F107',
        "F_AMPS", "B_NEC_AMPS"
    ]

    def test_associated_magnetic_field(self):
        request = self.get_request(
            begin_time=self.begin_time,
            end_time=self.end_time,
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        times = array(response["Timestamp"])
        lats = array(response["Latitude"])
        lons = array(response["Longitude"])
        rads = array(response["Radius"])*1e-3

        v_imf = array(response["IMF_V"])
        by_gsm_imf = array(response["IMF_BY_GSM"])
        bz_gsm_imf = array(response["IMF_BZ_GSM"])
        tilt_angle = array(response["DipoleTiltAngle"])
        f107 = array(response["F107"])

        f_amps = array(response["F_AMPS"])
        b_amps = array(response["B_NEC_AMPS"])

        if times.size > 0:
            idx = times.size // 2
            b_amps_ref = eval_associated_magnetic_model(
                times[idx], times, lats, lons, rads,
                v_imf, by_gsm_imf, bz_gsm_imf, tilt_angle, f107
            )
        else:
            b_amps_ref = empty((0, 3))

        f_amps_ref = vnorm(b_amps_ref)

        assert_allclose(b_amps, b_amps_ref, atol=2e-6)
        assert_allclose(f_amps, f_amps_ref, atol=1e-6)


class TestFetchDataAMPSAssociatedMagneticField(TestCase, AMPSAssociatedMagneticFieldTestMixIn, FetchDataMixIn):
    pass


class TestFetchFilteredDataAMPSAssociatedMagneticField(TestCase, AMPSAssociatedMagneticFieldTestMixIn, FetchFilteredDataMixIn):
    pass


class TestAsyncFetchFilteredDataAMPSAssociatedMagneticField(TestCase, AMPSAssociatedMagneticFieldTestMixIn, AsyncFetchFilteredDataMixIn):
    pass


#-------------------------------------------------------------------------------

class SunPositionTestMixIn(object):
    variables = [
        "SunDeclination", "SunRightAscension", "SunHourAngle",
        "SunAzimuthAngle", "SunZenithAngle",
        "SunLongitude", "SunVector",
    ]

    def test_sun_position(self):
        request = self.get_request(
            begin_time=self.begin_time,
            end_time=self.end_time,
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        times = array(response["Timestamp"])
        lats = array(response["Latitude"])
        lons = array(response["Longitude"])
        rads = array(response["Radius"])*1e-3

        declination = array(response["SunDeclination"])
        right_ascension = array(response["SunRightAscension"])
        hour_angle = array(response["SunHourAngle"])
        azimuth = array(response["SunAzimuthAngle"])
        zenith = array(response["SunZenithAngle"])
        sun_longitude = array(response["SunLongitude"])
        sun_vector = array(response["SunVector"])

        (
            declination_ref, right_ascension_ref, hour_angle_ref,
            azimuth_ref, zenith_ref
        ) = sunpos(times, lats, lons, rads, 0)
        sun_longitude_ref = lons - hour_angle_ref
        sun_vector_ref = convert(
            stack((declination_ref, sun_longitude_ref, ones(times.size)), axis=1),
            GEOCENTRIC_SPHERICAL, GEOCENTRIC_CARTESIAN
        )

        assert_allclose(declination, declination_ref, atol=1e-6)
        assert_allclose(right_ascension, right_ascension_ref, atol=1e-6)
        assert_allclose(hour_angle, hour_angle_ref, atol=1e-6)
        assert_allclose(azimuth, azimuth_ref, atol=1e-6)
        assert_allclose(zenith, zenith_ref, atol=1e-6)
        assert_allclose(sun_longitude, sun_longitude_ref, atol=1e-6)
        assert_allclose(sun_vector, sun_vector_ref, atol=1e-6)

    def test_zero_lenght(self):
        request = self.get_request(
            begin_time=self.begin_time + timedelta(seconds=0.1),
            end_time=self.begin_time + timedelta(seconds=0.2),
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        self.assertEqual(len(response["Timestamp"]), 0)


class TestFetchDataCsvSunPosition(TestCase, SunPositionTestMixIn, FetchDataCsvMixIn):
    pass


class TestFetchFilteredDataCsvSunPosition(TestCase, SunPositionTestMixIn, FetchFilteredDataCsvMixIn):
    pass


class TestFetchFilteredDataCdfSunPosition(TestCase, SunPositionTestMixIn, FetchFilteredDataCdfMixIn):
    pass


class TestAsyncFetchFilteredDataCsvSunPosition(TestCase, SunPositionTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    pass


class TestAsyncFetchFilteredDataCdfSunPosition(TestCase, SunPositionTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    pass

#-------------------------------------------------------------------------------

class DipoleTestMixIn(object):
    variables = ["DipoleAxisVector", "NGPLatitude", "NGPLongitude"]
    model_name = "IGRF12"
    model = load_model_shc(IGRF12, interpolate_in_decimal_years=True)

    def test_dipole(self):
        request = self.get_request(
            begin_time=self.begin_time,
            end_time=self.end_time,
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        times = array(response["Timestamp"])

        dipole_axis = array(response["DipoleAxisVector"])
        ngp_latitude = array(response["NGPLatitude"])
        ngp_longitude = array(response["NGPLongitude"])

        if times.size > 0:
            mean_time = 0.5*(times.min() + times.max())
        else:
            mean_time = 0.0 # MJD2000

        # construct north pointing unit vector of the dipole axis
        # from the spherical harmonic coefficients
        coeff, _ = self.model.coefficients(mean_time, max_degree=1)
        dipole_axis_ref = coeff[[2, 2, 1], [0, 1, 0]]
        dipole_axis_ref *= -1.0/vnorm(dipole_axis_ref)
        dipole_axis_ref = broadcast_to(dipole_axis_ref, (times.size, 3))
        ngp_latitude_ref = RAD2DEG * arcsin(dipole_axis_ref[..., 2])
        ngp_longitude_ref = RAD2DEG * arctan2(
            dipole_axis_ref[..., 1], dipole_axis_ref[..., 0]
        )

        assert_allclose(dipole_axis, dipole_axis_ref)
        assert_allclose(ngp_latitude, ngp_latitude_ref)
        assert_allclose(ngp_longitude, ngp_longitude_ref)

    def test_zero_lenght(self):
        request = self.get_request(
            begin_time=self.begin_time + timedelta(seconds=0.1),
            end_time=self.begin_time + timedelta(seconds=0.2),
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        self.assertEqual(len(response["Timestamp"]), 0)



class TestFetchDataCsvDipole(TestCase, DipoleTestMixIn, FetchDataCsvMixIn):
    pass


class TestFetchFilteredDataCsvDipole(TestCase, DipoleTestMixIn, FetchFilteredDataCsvMixIn):
    pass


class TestFetchFilteredDataCdfDipole(TestCase, DipoleTestMixIn, FetchFilteredDataCdfMixIn):
    pass


class TestAsyncFetchFilteredDataCsvDipole(TestCase, DipoleTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    pass


class TestAsyncFetchFilteredDataCdfDipole(TestCase, DipoleTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    pass

#-------------------------------------------------------------------------------

class TiltAngleTestMixIn(object):
    variables = ["SunVector", "DipoleAxisVector", "DipoleTiltAngle"]

    def test_dipole_tilt_angle(self):
        request = self.get_request(
            begin_time=self.begin_time,
            end_time=self.end_time,
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        earth_sun_vector = array(response["SunVector"])
        dipole_axis_vector = array(response["DipoleAxisVector"])
        dipole_tilt_angle = array(response["DipoleTiltAngle"])

        dipole_tilt_angle_ref = RAD2DEG * arcsin(
            (earth_sun_vector * dipole_axis_vector).sum(axis=1)
        )

        assert_allclose(dipole_tilt_angle, dipole_tilt_angle_ref)

    def test_zero_lenght(self):
        request = self.get_request(
            begin_time=self.begin_time + timedelta(seconds=0.1),
            end_time=self.begin_time + timedelta(seconds=0.2),
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        self.assertEqual(len(response["Timestamp"]), 0)


class TestFetchDataCsvTiltAngle(TestCase, TiltAngleTestMixIn, FetchDataCsvMixIn):
    pass


class TestFetchFilteredDataCsvTiltAngle(TestCase, TiltAngleTestMixIn, FetchFilteredDataCsvMixIn):
    pass


class TestFetchFilteredDataCdfTiltAngle(TestCase, TiltAngleTestMixIn, FetchFilteredDataCdfMixIn):
    pass


class TestAsyncFetchFilteredDataCsvTiltAngle(TestCase, TiltAngleTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    pass


class TestAsyncFetchFilteredDataCdfTiltAngle(TestCase, TiltAngleTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    pass


#-------------------------------------------------------------------------------

class QuasiDipoleTestMixIn(object):
    variables = ['MLT', 'QDLat', 'QDLon', 'QDBasis']

    def test_quasi_dipole(self):
        request = self.get_request(
            begin_time=self.begin_time,
            end_time=self.end_time,
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        time = array(response["Timestamp"])
        lats = array(response["Latitude"])
        lons = array(response["Longitude"])
        rads = array(response["Radius"])*1e-3
        mlt = array(response["MLT"])
        qdlat = array(response["QDLat"])
        qdlon = array(response["QDLon"])
        qdbasis = array(response["QDBasis"])

        qdlat_ref, qdlon_ref, f11, f12, f21, f22, _ = eval_qdlatlon_with_base_vectors(
            lats, lons, rads, mjd2000_to_decimal_year(time)
        )
        mlt_ref = eval_mlt(qdlon_ref, time)

        qdbasis_ref = stack(
            (f11, f12, f21, f22), axis=1
        ).reshape((time.size, 2, 2))

        assert_allclose(mlt, mlt_ref, rtol=1e-6)
        assert_allclose(qdlat, qdlat_ref, rtol=1e-6)
        assert_allclose(qdlon, qdlon_ref, rtol=1e-6)
        assert_allclose(qdbasis, qdbasis_ref, rtol=1e-6)

    def test_zero_lenght(self):
        request = self.get_request(
            begin_time=self.begin_time + timedelta(seconds=0.1),
            end_time=self.begin_time + timedelta(seconds=0.2),
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        self.assertEqual(len(response["Timestamp"]), 0)


class TestFetchDataCsvQuasiDipole(TestCase, QuasiDipoleTestMixIn, FetchDataCsvMixIn):
    pass


class TestFetchFilteredDataCsvQuasiDipole(TestCase, QuasiDipoleTestMixIn, FetchFilteredDataCsvMixIn):
    pass


class TestFetchFilteredDataCdfQuasiDipole(TestCase, QuasiDipoleTestMixIn, FetchFilteredDataCdfMixIn):
    pass


class TestAsyncFetchFilteredDataCsvQuasiDipole(TestCase, QuasiDipoleTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    pass


class TestAsyncFetchFilteredDataCdfQuasiDipole(TestCase, QuasiDipoleTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    pass

#-------------------------------------------------------------------------------

def load_composed_model(*items):
    composed_model = ComposedGeomagneticModel()
    for model, scale, parameters in items:
        composed_model.push(model, scale, **parameters)
    return composed_model


class MagneticModelTestMixIn(object):
    model_name = None
    model_expression = None
    model = None

    @property
    def full_model_expression(self):
        return (
            "%s=%s" % (self.model_name, self.model_expression)
            if self.model_expression else self.model_name
        )

    @property
    def variables(self):
        return ["F_%s"%self.model_name, "B_NEC_%s"%self.model_name]

    @property
    def residual_variables(self):
        return ["F_res_%s"%self.model_name, "B_NEC_res_%s"%self.model_name]

    @property
    def measurements_variables(self):
        return ["F", "B_NEC"]

    def test_model_residuals(self):
        request = self.get_request(
            begin_time=self.begin_time,
            end_time=self.end_time,
            model_ids=[self.full_model_expression],
            variables=(
                self.measurements_variables +
                self.residual_variables +
                self.variables
            ),
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)

        real_f = array(response["F"])
        real_b = array(response["B_NEC"])
        model_f = array(response["F_%s" % self.model_name])
        model_b = array(response["B_NEC_%s" % self.model_name])
        diff_f = array(response["F_res_%s" % self.model_name])
        diff_b = array(response["B_NEC_res_%s" % self.model_name])

        assert_allclose(diff_f, real_f - model_f, atol=2e-4)
        assert_allclose(diff_b, real_b - model_b, atol=2e-4)

    def test_model(self):
        request = self.get_request(
            begin_time=self.begin_time,
            end_time=self.end_time,
            model_ids=[self.full_model_expression],
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)

        time = array(response["Timestamp"])
        coords = stack((
            array(response["Latitude"]),
            array(response["Longitude"]),
            array(response["Radius"])*1e-3,
        ), axis=1)
        mag_field = array(response["B_NEC_%s" % self.model_name])
        mag_intensity = array(response["F_%s" % self.model_name])

        assert_allclose(mag_intensity, vnorm(mag_field))
        assert_allclose(
            mag_field, self.model.eval(time, coords, scale=[1, 1, -1]),
            atol=2e-4,
        )

    def test_zero_lenght(self):
        request = self.get_request(
            begin_time=self.begin_time + timedelta(seconds=0.1),
            end_time=self.begin_time + timedelta(seconds=0.2),
            variables=self.variables,
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)
        self.assertEqual(len(response["Timestamp"]), 0)


class MagneticModelMIOTestMixIn(MagneticModelTestMixIn):

    @property
    def f107_variables(self):
        return ["F107"]

    def test_model(self):
        request = self.get_request(
            begin_time=self.begin_time,
            end_time=self.end_time,
            model_ids=[self.full_model_expression],
            variables=(self.variables + self.f107_variables),
            collection_ids={"Alpha": ["SW_OPER_MAGA_LR_1B"]},
        )
        response = self.get_parsed_response(request)

        time = array(response["Timestamp"])
        coords = stack((
            array(response["Latitude"]),
            array(response["Longitude"]),
            array(response["Radius"])*1e-3,
        ), axis=1)
        mag_field = array(response["B_NEC_%s" % self.model_name])
        mag_intensity = array(response["F_%s" % self.model_name])
        f107 = array(response["F107"])

        assert_allclose(mag_intensity, vnorm(mag_field))
        assert_allclose(
            mag_field,
            self.model.eval(time, coords, f107=f107, scale=[1, 1, -1]),
            atol=2e-4,
        )

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelIGRF12(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12, interpolate_in_decimal_years=True)


class TestFetchFilteredDataCsvModelIGRF12(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12, interpolate_in_decimal_years=True)


class TestFetchFilteredDataCdfModelIGRF12(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12, interpolate_in_decimal_years=True)


class TestAsyncFetchFilteredDataCsvModelIGRF12(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12, interpolate_in_decimal_years=True)


class TestAsyncFetchFilteredDataCdfModelIGRF12(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12, interpolate_in_decimal_years=True)

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelLCS1(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "LCS-1"
    model = load_model_shc(LCS1)


class TestFetchFilteredDataCsvModelLCS1(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "LCS-1"
    model = load_model_shc(LCS1)


class TestFetchFilteredDataCdfModelLCS1(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "LCS-1"
    model = load_model_shc(LCS1)


class TestAsyncFetchFilteredDataCsvModelLCS1(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "LCS-1"
    model = load_model_shc(LCS1)


class TestAsyncFetchFilteredDataCdfModelLCS1(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "LCS-1"
    model = load_model_shc(LCS1)

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelMF7(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "MF7"
    model = load_model_shc(MF7)


class TestFetchFilteredDataCsvModelMF7(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MF7"
    model = load_model_shc(MF7)


class TestFetchFilteredDataCdfModelMF7(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MF7"
    model = load_model_shc(MF7)


class TestAsyncFetchFilteredDataCsvModelMF7(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MF7"
    model = load_model_shc(MF7)


class TestAsyncFetchFilteredDataCdfModelMF7(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MF7"
    model = load_model_shc(MF7)

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelCHAOS6Static(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestFetchFilteredDataCsvModelCHAOS6Static(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestFetchFilteredDataCdfModelCHAOS6Static(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestAsyncFetchFilteredDataCsvModelCHAOS6Static(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestAsyncFetchFilteredDataCdfModelCHAOS6Static(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelCHAOS6Core(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(
        MCO_CHAOS6,
        to_mjd2000=decimal_year_to_mjd2000_simple
    )


class TestFetchFilteredDataCsvModelCHAOS6Core(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(
        MCO_CHAOS6,
        to_mjd2000=decimal_year_to_mjd2000_simple
    )


class TestFetchFilteredDataCdfModelCHAOS6Core(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(
        MCO_CHAOS6,
        to_mjd2000=decimal_year_to_mjd2000_simple
    )


class TestAsyncFetchFilteredDataCsvModelCHAOS6Core(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(
        MCO_CHAOS6,
        to_mjd2000=decimal_year_to_mjd2000_simple
    )


class TestAsyncFetchFilteredDataCdfModelCHAOS6Core(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(
        MCO_CHAOS6,
        to_mjd2000=decimal_year_to_mjd2000_simple
    )

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelCHAOS6MMAPrimary(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "CHAOS-6-MMA-Primary"
    model = load_model_swarm_mma_2c_external(MMA_CHAOS6)


class TestFetchFilteredDataCsvModelCHAOS6MMAPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "CHAOS-6-MMA-Primary"
    model = load_model_swarm_mma_2c_external(MMA_CHAOS6)


class TestFetchFilteredDataCdfModelCHAOS6MMAPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "CHAOS-6-MMA-Primary"
    model = load_model_swarm_mma_2c_external(MMA_CHAOS6)


class TestAsyncFetchFilteredDataCsvModelCHAOS6MMAPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "CHAOS-6-MMA-Primary"
    model = load_model_swarm_mma_2c_external(MMA_CHAOS6)


class TestAsyncFetchFilteredDataCdfModelCHAOS6MMAPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "CHAOS-6-MMA-Primary"
    model = load_model_swarm_mma_2c_external(MMA_CHAOS6)


class TestFetchDataCsvModelCHAOS6MMASecondary(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "CHAOS-6-MMA-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_CHAOS6)


class TestFetchFilteredDataCsvModelCHAOS6MMASecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "CHAOS-6-MMA-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_CHAOS6)


class TestFetchFilteredDataCdfModelCHAOS6MMASecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "CHAOS-6-MMA-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_CHAOS6)


class TestAsyncFetchFilteredDataCsvModelCHAOS6MMASecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "CHAOS-6-MMA-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_CHAOS6)


class TestAsyncFetchFilteredDataCdfModelCHAOS6MMASecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "CHAOS-6-MMA-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_CHAOS6)

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelMCO2C(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestFetchFilteredDataCsvModelMCO2C(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestFetchFilteredDataCdfModelMCO2C(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestAsyncFetchFilteredDataCsvModelMCO2C(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestAsyncFetchFilteredDataCdfModelMCO2C(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestFetchDataCsvModelMCO2D(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestFetchFilteredDataCsvModelMCO2D(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestFetchFilteredDataCdfModelMCO2D(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestAsyncFetchFilteredDataCsvModelMCO2D(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestAsyncFetchFilteredDataCdfModelMCO2D(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestFetchDataCsvModelMCO2X(TestFetchDataCsvModelCHAOS6Core):
    model_name = "MCO_SHA_2X"


class TestFetchFilteredDataCsvModelMCO2X(TestFetchFilteredDataCsvModelCHAOS6Core):
    model_name = "MCO_SHA_2X"


class TestFetchFilteredDataCdfModelMCO2X(TestFetchFilteredDataCdfModelCHAOS6Core):
    model_name = "MCO_SHA_2X"


class TestAsyncFetchFilteredDataCsvModelMCO2X(TestAsyncFetchFilteredDataCsvModelCHAOS6Core):
    model_name = "MCO_SHA_2X"


class TestAsyncFetchFilteredDataCdfModelMCO2X(TestAsyncFetchFilteredDataCdfModelCHAOS6Core):
    model_name = "MCO_SHA_2X"

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelMLI2C(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestFetchFilteredDataCsvModelMLI2C(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestFetchFilteredDataCdfModelMLI2C(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestAsyncFetchFilteredDataCsvModelMLI2C(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestAsyncFetchFilteredDataCdfModelMLI2C(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestFetchDataCsvModelMLI2D(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)


class TestFetchFilteredDataCsvModelMLI2D(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)


class TestFetchFilteredDataCdfModelMLI2D(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)


class TestAsyncFetchFilteredDataCsvModelMLI2D(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)


class TestAsyncFetchFilteredDataCdfModelMLI2D(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestFetchFilteredDataCsvModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestFetchFilteredDataCdfModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestAsyncFetchFilteredDataCsvModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestAsyncFetchFilteredDataCdfModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestFetchDataCsvModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)


class TestFetchFilteredDataCsvModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)


class TestFetchFilteredDataCdfModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)


class TestAsyncFetchFilteredDataCsvModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)


class TestAsyncFetchFilteredDataCdfModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestFetchFilteredDataCsvModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestFetchFilteredDataCdfModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestAsyncFetchFilteredDataCsvModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestAsyncFetchFilteredDataCdfModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestFetchDataCsvModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)


class TestFetchFilteredDataCsvModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)


class TestFetchFilteredDataCdfModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)


class TestAsyncFetchFilteredDataCsvModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)


class TestAsyncFetchFilteredDataCdfModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, FetchDataCsvMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestFetchFilteredDataCsvModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestFetchFilteredDataCdfModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestAsyncFetchFilteredDataCsvModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestAsyncFetchFilteredDataCdfModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestFetchDataCsvModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, FetchDataCsvMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestFetchFilteredDataCsvModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestFetchFilteredDataCdfModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestAsyncFetchFilteredDataCsvModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestAsyncFetchFilteredDataCdfModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestFetchDataCsvModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, FetchDataCsvMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestFetchFilteredDataCsvModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestFetchFilteredDataCdfModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestAsyncFetchFilteredDataCsvModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestAsyncFetchFilteredDataCdfModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestFetchDataCsvModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, FetchDataCsvMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)


class TestFetchFilteredDataCsvModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)


class TestFetchFilteredDataCdfModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)


class TestAsyncFetchFilteredDataCsvModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)


class TestAsyncFetchFilteredDataCdfModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)

#-------------------------------------------------------------------------------

class TestFetchDataCsvModelExpression(TestCase, MagneticModelTestMixIn, FetchDataCsvMixIn):
    model_name = "MODEL"
    model_expression = (
        '+"CHAOS-6-Core"(max_degree=30)'
        '+"CHAOS-6-Static"(max_degree=30)'
        '+"CHAOS-6-MMA-Primary"'
        '+"CHAOS-6-MMA-Secondary"'
    )
    model = load_composed_model(
        (load_model_shc_combined(
            MCO_CHAOS6, CHAOS6_STATIC,
            to_mjd2000=decimal_year_to_mjd2000_simple
        ), 1, {'max_degree': 30}),
        (load_model_swarm_mma_2c_external(MMA_CHAOS6), 1, {}),
        (load_model_swarm_mma_2c_internal(MMA_CHAOS6), 1, {}),
    )


class TestFetchFilteredDataCsvModelExpression(TestCase, MagneticModelTestMixIn, FetchFilteredDataCsvMixIn):
    model_name = "MODEL"
    model_expression = (
        '+"CHAOS-6-Core"(max_degree=30)'
        '+"CHAOS-6-Static"(max_degree=30)'
        "+'CHAOS-6-MMA-Primary'"
        "+'CHAOS-6-MMA-Secondary'"
    )
    model = load_composed_model(
        (load_model_shc_combined(
            MCO_CHAOS6, CHAOS6_STATIC,
            to_mjd2000=decimal_year_to_mjd2000_simple
        ), 1, {'max_degree': 30}),
        (load_model_swarm_mma_2c_external(MMA_CHAOS6), 1, {}),
        (load_model_swarm_mma_2c_internal(MMA_CHAOS6), 1, {}),
    )


class TestFetchFilteredDataCdfModelExpression(TestCase, MagneticModelTestMixIn, FetchFilteredDataCdfMixIn):
    model_name = "MODEL"
    model_expression = (
        '+"CHAOS-6-Core"(max_degree=30)'
        '+"CHAOS-6-Static"(max_degree=30)'
        "+'CHAOS-6-MMA-Primary'"
        "+'CHAOS-6-MMA-Secondary'"
    )
    model = load_composed_model(
        (load_model_shc_combined(
            MCO_CHAOS6, CHAOS6_STATIC,
            to_mjd2000=decimal_year_to_mjd2000_simple
        ), 1, {'max_degree': 30}),
        (load_model_swarm_mma_2c_external(MMA_CHAOS6), 1, {}),
        (load_model_swarm_mma_2c_internal(MMA_CHAOS6), 1, {}),
    )


class TestAsyncFetchFilteredDataCsvModelExpression(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    model_name = "MODEL"
    model_expression = (
        '+"CHAOS-6-Core"(max_degree=30)'
        '+"CHAOS-6-Static"(max_degree=30)'
        "+'CHAOS-6-MMA-Primary'"
        "+'CHAOS-6-MMA-Secondary'"
    )
    model = load_composed_model(
        (load_model_shc_combined(
            MCO_CHAOS6, CHAOS6_STATIC,
            to_mjd2000=decimal_year_to_mjd2000_simple
        ), 1, {'max_degree': 30}),
        (load_model_swarm_mma_2c_external(MMA_CHAOS6), 1, {}),
        (load_model_swarm_mma_2c_internal(MMA_CHAOS6), 1, {}),
    )


class TestAsyncFetchFilteredDataCdfModelExpression(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    model_name = "MODEL"
    model_expression = (
        '+"CHAOS-6-Core"(max_degree=30)'
        '+"CHAOS-6-Static"(max_degree=30)'
        "+'CHAOS-6-MMA-Primary'"
        "+'CHAOS-6-MMA-Secondary'"
    )
    model = load_composed_model(
        (load_model_shc_combined(
            MCO_CHAOS6, CHAOS6_STATIC,
            to_mjd2000=decimal_year_to_mjd2000_simple
        ), 1, {'max_degree': 30}),
        (load_model_swarm_mma_2c_external(MMA_CHAOS6), 1, {}),
        (load_model_swarm_mma_2c_internal(MMA_CHAOS6), 1, {}),
    )

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
