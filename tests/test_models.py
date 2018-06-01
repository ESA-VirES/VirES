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
# pylint: disable=missing-docstring,line-too-long,too-many-ancestors
# pylint: disable=import-error,no-name-in-module,too-few-public-methods,too-many-locals

from unittest import TestCase, main
from math import pi
from datetime import timedelta
from numpy import array, stack, ones, broadcast_to, arcsin, arctan2
from numpy.testing import assert_allclose
from time_util import parse_datetime
from eoxmagmod import (
    vnorm, load_model_shc, load_model_shc_combined,
    load_model_igrf, load_model_wmm, load_model_emm,
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
)
from eoxmagmod.data import (
    IGRF11, IGRF12, SIFM,
    CHAOS5_STATIC, CHAOS5_CORE_V4,
    CHAOS6_STATIC, CHAOS6_CORE_X3,
    WMM_2010, WMM_2015,
    EMM_2010_STATIC, EMM_2010_SECVAR,
)
from wps_util import (
    WpsPostRequestMixIn, WpsAsyncPostRequestMixIn, CsvRequestMixIn,
)

MCO_SHA_2C = "./data/SW_OPER_MCO_SHA_2C.shc"
MCO_SHA_2D = "./data/SW_OPER_MCO_SHA_2D.shc"
MCO_SHA_2F = "./data/SW_OPER_MCO_SHA_2F.shc"
MLI_SHA_2C = "./data/SW_OPER_MLI_SHA_2C.shc"
MLI_SHA_2D = "./data/SW_OPER_MLI_SHA_2D.shc"
MIO_SHA_2C = "./data/SW_OPER_MIO_SHA_2C.txt"
MIO_SHA_2D = "./data/SW_OPER_MIO_SHA_2D.txt"
MMA_SHA_2C = "./data/SW_OPER_MMA_SHA_2C.cdf"
MMA_SHA_2F = "./data/SW_OPER_MMA_SHA_2F.cdf"

RAD2DEG = 180.0/pi

START_TIME = parse_datetime("2016-01-01T23:50:00Z")
END_TIME = parse_datetime("2016-01-02T00:00:00Z")

#-------------------------------------------------------------------------------

class FetchDataMixIn(CsvRequestMixIn, WpsPostRequestMixIn):
    template_source = "test_vires_fetch_data.xml"
    begin_time = START_TIME
    end_time = END_TIME


class FetchFilteredDataMixIn(CsvRequestMixIn, WpsPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data.xml"
    begin_time = START_TIME
    end_time = END_TIME


class AsyncFetchFilteredDataMixIn(CsvRequestMixIn, WpsAsyncPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data_async.xml"
    begin_time = START_TIME
    end_time = END_TIME

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


class TestFetchDataSunPosition(TestCase, SunPositionTestMixIn, FetchDataMixIn):
    pass


class TestFetchFilteredDataSunPosition(TestCase, SunPositionTestMixIn, FetchFilteredDataMixIn):
    pass


class TestAsyncFetchFilteredDataSunPosition(TestCase, SunPositionTestMixIn, AsyncFetchFilteredDataMixIn):
    pass

#-------------------------------------------------------------------------------

class DipoleTestMixIn(object):
    variables = ["DipoleAxisVector", "NGPLatitude", "NGPLongitude"]
    model_name = "IGRF12"
    model = load_model_shc(IGRF12)

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

        if len(times) > 0:
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



class TestFetchDataDipole(TestCase, DipoleTestMixIn, FetchDataMixIn):
    pass


class TestFetchFilteredDataDipole(TestCase, DipoleTestMixIn, FetchFilteredDataMixIn):
    pass


class TestAsyncFetchFilteredDataDipole(TestCase, DipoleTestMixIn, AsyncFetchFilteredDataMixIn):
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


class TestFetchDataTiltAngle(TestCase, TiltAngleTestMixIn, FetchDataMixIn):
    pass


class TestFetchFilteredDataTiltAngle(TestCase, TiltAngleTestMixIn, FetchFilteredDataMixIn):
    pass


class TestAsyncFetchFilteredDataTiltAngle(TestCase, TiltAngleTestMixIn, AsyncFetchFilteredDataMixIn):
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
        mlt_ref = eval_mlt(time, qdlon_ref)

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


class TestFetchDataQuasiDipole(TestCase, QuasiDipoleTestMixIn, FetchDataMixIn):
    pass


class TestFetchFilteredDataQuasiDipole(TestCase, QuasiDipoleTestMixIn, FetchFilteredDataMixIn):
    pass


class TestAsyncFetchFilteredDataQuasiDipole(TestCase, QuasiDipoleTestMixIn, AsyncFetchFilteredDataMixIn):
    pass

#-------------------------------------------------------------------------------

class MagneticModelTestMixIn(object):
    model_name = None
    model = None

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
            model_ids=[self.model_name],
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
            model_ids=[self.model_name],
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
            model_ids=[self.model_name],
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

class TestFetchDataModelEMM2010(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "EMM2010"
    model = load_model_emm(EMM_2010_STATIC, EMM_2010_SECVAR)


class TestFetchFilteredDataModelEMM2010(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "EMM2010"
    model = load_model_emm(EMM_2010_STATIC, EMM_2010_SECVAR)


class TestAsyncFetchFilteredDataModelEMM2010(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "EMM2010"
    model = load_model_emm(EMM_2010_STATIC, EMM_2010_SECVAR)


class TestFetchDataModelEMM(TestFetchDataModelEMM2010, FetchDataMixIn):
    model_name = "EMM"


class TestFetchFilteredDataModelEMM(TestFetchFilteredDataModelEMM2010, FetchFilteredDataMixIn):
    model_name = "EMM"


class TestAsyncFetchFilteredDataModelEMM(TestAsyncFetchFilteredDataModelEMM2010, AsyncFetchFilteredDataMixIn):
    model_name = "EMM"

#-------------------------------------------------------------------------------

class TestFetchDataModelWMM2010(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "WMM2010"
    model = load_model_wmm(WMM_2010)


class TestFetchFilteredDataModelWMM2010(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "WMM2010"
    model = load_model_wmm(WMM_2010)


class TestAsyncFetchFilteredDataModelWMM2010(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "WMM2010"
    model = load_model_wmm(WMM_2010)


class TestFetchDataModelWMM2015(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "WMM2015"
    model = load_model_wmm(WMM_2015)


class TestFetchFilteredDataModelWMM2015(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "WMM2015"
    model = load_model_wmm(WMM_2015)


class TestAsyncFetchFilteredDataModelWMM2015(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "WMM2015"
    model = load_model_wmm(WMM_2015)


class TestFetchDataModelWMM(TestFetchDataModelWMM2015):
    model_name = "WMM"


class TestFetchFilteredDataModelWMM(TestFetchFilteredDataModelWMM2015):
    model_name = "WMM"


class TestAsyncFetchFilteredDataModelWMM(TestAsyncFetchFilteredDataModelWMM2015):
    model_name = "WMM"

#-------------------------------------------------------------------------------

class TestFetchDataModelIGRF11(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "IGRF11"
    model = load_model_igrf(IGRF11)


class TestFetchFilteredDataModelIGRF11(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "IGRF11"
    model = load_model_igrf(IGRF11)


class TestAsyncFetchFilteredDataModelIGRF11(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "IGRF11"
    model = load_model_igrf(IGRF11)


class TestFetchDataModelIGRF12(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12)


class TestFetchFilteredDataModelIGRF12(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12)


class TestAsyncFetchFilteredDataModelIGRF12(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12)


class TestFetchDataModelIGRF(TestFetchDataModelIGRF12):
    model_name = "IGRF"


class TestFetchFilteredDataModelIGRF(TestFetchFilteredDataModelIGRF12):
    model_name = "IGRF"


class TestAsyncFetchFilteredDataModelIGRF(TestAsyncFetchFilteredDataModelIGRF12):
    model_name = "IGRF"

#-------------------------------------------------------------------------------

class TestFetchDataModelSIFM(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "SIFM"
    model = load_model_shc(SIFM)


class TestFetchFilteredDataModelSIFM(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "SIFM"
    model = load_model_shc(SIFM)


class TestAsyncFetchFilteredDataModelSIFM(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "SIFM"
    model = load_model_shc(SIFM)

#-------------------------------------------------------------------------------

class TestFetchDataModelCHAOS5Static(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "CHAOS-5-Static"
    model = load_model_shc(CHAOS5_STATIC)


class TestFetchFilteredDataModelCHAOS5Static(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "CHAOS-5-Static"
    model = load_model_shc(CHAOS5_STATIC)


class TestAsyncFetchFilteredDataModelCHAOS5Static(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "CHAOS-5-Static"
    model = load_model_shc(CHAOS5_STATIC)


class TestFetchDataModelCHAOS6Static(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestFetchFilteredDataModelCHAOS6Static(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestAsyncFetchFilteredDataModelCHAOS6Static(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestFetchDataModelCHAOSStatic(TestFetchDataModelCHAOS6Static):
    model_name = "CHAOS-Static"


class TestFetchFilteredDataModelCHAOSStatic(TestFetchFilteredDataModelCHAOS6Static):
    model_name = "CHAOS-Static"


class TestAsyncFetchFilteredDataModelCHAOSStatic(TestAsyncFetchFilteredDataModelCHAOS6Static):
    model_name = "CHAOS-Static"

#-------------------------------------------------------------------------------

class TestFetchDataModelCHAOS5Core(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "CHAOS-5-Core"
    model = load_model_shc(CHAOS5_CORE_V4)


class TestFetchFilteredDataModelCHAOS5Core(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "CHAOS-5-Core"
    model = load_model_shc(CHAOS5_CORE_V4)


class TestAsyncFetchFilteredDataModelCHAOS5Core(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "CHAOS-5-Core"
    model = load_model_shc(CHAOS5_CORE_V4)


class TestFetchDataModelCHAOS6Core(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(CHAOS6_CORE_X3)


class TestFetchFilteredDataModelCHAOS6Core(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(CHAOS6_CORE_X3)


class TestAsyncFetchFilteredDataModelCHAOS6Core(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(CHAOS6_CORE_X3)


class TestFetchDataModelCHAOSCore(TestFetchDataModelCHAOS6Core):
    model_name = "CHAOS-Core"


class TestFetchFilteredDataModelCHAOSCore(TestFetchFilteredDataModelCHAOS6Core):
    model_name = "CHAOS-Core"


class TestAsyncFetchFilteredDataModelCHAOSCore(TestAsyncFetchFilteredDataModelCHAOS6Core):
    model_name = "CHAOS-Core"

#-------------------------------------------------------------------------------

class TestFetchDataModelCHAOS5Combined(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "CHAOS-5-Combined"
    model = load_model_shc_combined(CHAOS5_CORE_V4, CHAOS5_STATIC)


class TestFetchFilteredDataModelCHAOS5Combined(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "CHAOS-5-Combined"
    model = load_model_shc_combined(CHAOS5_CORE_V4, CHAOS5_STATIC)


class TestAsyncFetchFilteredDataModelCHAOS5Combined(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "CHAOS-5-Combined"
    model = load_model_shc_combined(CHAOS5_CORE_V4, CHAOS5_STATIC)


class TestFetchDataModelCHAOS6Combined(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "CHAOS-6-Combined"
    model = load_model_shc_combined(CHAOS6_CORE_X3, CHAOS6_STATIC)


class TestFetchFilteredDataModelCHAOS6Combined(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "CHAOS-6-Combined"
    model = load_model_shc_combined(CHAOS6_CORE_X3, CHAOS6_STATIC)


class TestAsyncFetchFilteredDataModelCHAOS6Combined(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "CHAOS-6-Combined"
    model = load_model_shc_combined(CHAOS6_CORE_X3, CHAOS6_STATIC)


class TestFetchDataModelCHAOSCombined(TestFetchDataModelCHAOS6Combined):
    model_name = "CHAOS-Combined"


class TestFetchFilteredDataModelCHAOSCombined(TestFetchFilteredDataModelCHAOS6Combined):
    model_name = "CHAOS-Combined"


class TestAsyncFetchFilteredDataModelCHAOSCombined(TestAsyncFetchFilteredDataModelCHAOS6Combined):
    model_name = "CHAOS-Combined"

#-------------------------------------------------------------------------------

class TestFetchDataModelMCO2C(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestFetchFilteredDataModelMCO2C(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestAsyncFetchFilteredDataModelMCO2C(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestFetchDataModelMCO2D(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestFetchFilteredDataModelMCO2D(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestAsyncFetchFilteredDataModelMCO2D(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestFetchDataModelMCO2F(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "MCO_SHA_2F"
    model = load_model_shc(MCO_SHA_2F)


class TestFetchFilteredDataModelMCO2F(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "MCO_SHA_2F"
    model = load_model_shc(MCO_SHA_2F)


class TestAsyncFetchFilteredDataModelMCO2F(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MCO_SHA_2F"
    model = load_model_shc(MCO_SHA_2F)

#-------------------------------------------------------------------------------

class TestFetchDataModelMLI2C(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestFetchFilteredDataModelMLI2C(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestAsyncFetchFilteredDataModelMLI2C(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestFetchDataModelMLI2D(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)


class TestFetchFilteredDataModelMLI2D(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)


class TestAsyncFetchFilteredDataModelMLI2D(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)

#-------------------------------------------------------------------------------

class TestFetchDataModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestFetchFilteredDataModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestAsyncFetchFilteredDataModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestFetchDataModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)


class TestFetchFilteredDataModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)


class TestAsyncFetchFilteredDataModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)

#-------------------------------------------------------------------------------

class TestFetchDataModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestFetchFilteredDataModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestAsyncFetchFilteredDataModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestFetchDataModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, FetchDataMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)


class TestFetchFilteredDataModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)


class TestAsyncFetchFilteredDataModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)

#-------------------------------------------------------------------------------

class TestFetchDataModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, FetchDataMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestFetchFilteredDataModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestAsyncFetchFilteredDataModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestFetchDataModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, FetchDataMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestFetchFilteredDataModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestAsyncFetchFilteredDataModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestFetchDataModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, FetchDataMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestFetchFilteredDataModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestAsyncFetchFilteredDataModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestFetchDataModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, FetchDataMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)


class TestFetchFilteredDataModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)


class TestAsyncFetchFilteredDataModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
