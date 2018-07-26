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
    CHAOS6_STATIC, CHAOS6_CORE_LATEST,
    WMM_2010, WMM_2015,
    EMM_2010_STATIC, EMM_2010_SECVAR,
)
from wps_util import (
    WpsPostRequestMixIn, WpsAsyncPostRequestMixIn,
    CsvRequestMixIn, CdfRequestMixIn,
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
class TimeRangeMixIn(object):
    begin_time = START_TIME
    end_time = END_TIME

class FetchDataCSVMixIn(CsvRequestMixIn, WpsPostRequestMixIn, TimeRangeMixIn):
    template_source = "test_vires_fetch_data.xml"


class FetchFilteredDataCSVMixIn(CsvRequestMixIn, WpsPostRequestMixIn, TimeRangeMixIn):
    template_source = "test_vires_fetch_filtered_data.xml"


class AsyncFetchFilteredDataCSVMixIn(CsvRequestMixIn, WpsAsyncPostRequestMixIn, TimeRangeMixIn):
    template_source = "test_vires_fetch_filtered_data_async.xml"


class FetchFilteredDataCDFMixIn(CdfRequestMixIn, WpsPostRequestMixIn, TimeRangeMixIn):
    template_source = "test_vires_fetch_filtered_data.xml"


class AsyncFetchFilteredDataCDFMixIn(CdfRequestMixIn, WpsAsyncPostRequestMixIn, TimeRangeMixIn):
    template_source = "test_vires_fetch_filtered_data_async.xml"

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


class TestFetchDataCSVSunPosition(TestCase, SunPositionTestMixIn, FetchDataCSVMixIn):
    pass


class TestFetchFilteredDataCSVSunPosition(TestCase, SunPositionTestMixIn, FetchFilteredDataCSVMixIn):
    pass


class TestAsyncFetchFilteredDataCSVSunPosition(TestCase, SunPositionTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    pass


class TestFetchFilteredDataCDFSunPosition(TestCase, SunPositionTestMixIn, FetchFilteredDataCDFMixIn):
    pass


class TestAsyncFetchFilteredDataCDFSunPosition(TestCase, SunPositionTestMixIn, AsyncFetchFilteredDataCDFMixIn):
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



class TestFetchDataCSVDipole(TestCase, DipoleTestMixIn, FetchDataCSVMixIn):
    pass


class TestFetchFilteredDataCSVDipole(TestCase, DipoleTestMixIn, FetchFilteredDataCSVMixIn):
    pass


class TestAsyncFetchFilteredDataCSVDipole(TestCase, DipoleTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    pass


class TestFetchFilteredDataCDFDipole(TestCase, DipoleTestMixIn, FetchFilteredDataCDFMixIn):
    pass


class TestAsyncFetchFilteredDataCDFDipole(TestCase, DipoleTestMixIn, AsyncFetchFilteredDataCDFMixIn):
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


class TestFetchDataCSVTiltAngle(TestCase, TiltAngleTestMixIn, FetchDataCSVMixIn):
    pass


class TestFetchFilteredDataCSVTiltAngle(TestCase, TiltAngleTestMixIn, FetchFilteredDataCSVMixIn):
    pass


class TestAsyncFetchFilteredDataCSVTiltAngle(TestCase, TiltAngleTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    pass


class TestFetchFilteredDataCDFTiltAngle(TestCase, TiltAngleTestMixIn, FetchFilteredDataCDFMixIn):
    pass


class TestAsyncFetchFilteredDataCDFTiltAngle(TestCase, TiltAngleTestMixIn, AsyncFetchFilteredDataCDFMixIn):
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


class TestFetchDataCSVQuasiDipole(TestCase, QuasiDipoleTestMixIn, FetchDataCSVMixIn):
    pass


class TestFetchFilteredDataCSVQuasiDipole(TestCase, QuasiDipoleTestMixIn, FetchFilteredDataCSVMixIn):
    pass


class TestAsyncFetchFilteredDataCSVQuasiDipole(TestCase, QuasiDipoleTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    pass


class TestFetchFilteredDataCDFQuasiDipole(TestCase, QuasiDipoleTestMixIn, FetchFilteredDataCDFMixIn):
    pass


class TestAsyncFetchFilteredDataCDFQuasiDipole(TestCase, QuasiDipoleTestMixIn, AsyncFetchFilteredDataCDFMixIn):
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

class TestFetchDataCSVModelEMM2010(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "EMM2010"
    model = load_model_emm(EMM_2010_STATIC, EMM_2010_SECVAR)


class TestFetchFilteredDataCSVModelEMM2010(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "EMM2010"
    model = load_model_emm(EMM_2010_STATIC, EMM_2010_SECVAR)


class TestAsyncFetchFilteredDataCSVModelEMM2010(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "EMM2010"
    model = load_model_emm(EMM_2010_STATIC, EMM_2010_SECVAR)


class TestFetchFilteredDataCDFModelEMM2010(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "EMM2010"
    model = load_model_emm(EMM_2010_STATIC, EMM_2010_SECVAR)


class TestAsyncFetchFilteredDataCDFModelEMM2010(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "EMM2010"
    model = load_model_emm(EMM_2010_STATIC, EMM_2010_SECVAR)


class TestFetchDataCSVModelEMM(TestFetchDataCSVModelEMM2010, FetchDataCSVMixIn):
    model_name = "EMM"


class TestFetchFilteredDataCSVModelEMM(TestFetchFilteredDataCSVModelEMM2010, FetchFilteredDataCSVMixIn):
    model_name = "EMM"


class TestAsyncFetchFilteredDataCSVModelEMM(TestAsyncFetchFilteredDataCSVModelEMM2010, AsyncFetchFilteredDataCSVMixIn):
    model_name = "EMM"


class TestFetchFilteredDataCDFModelEMM(TestFetchFilteredDataCDFModelEMM2010, FetchFilteredDataCDFMixIn):
    model_name = "EMM"


class TestAsyncFetchFilteredDataCDFModelEMM(TestAsyncFetchFilteredDataCDFModelEMM2010, AsyncFetchFilteredDataCDFMixIn):
    model_name = "EMM"

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelWMM2010(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "WMM2010"
    model = load_model_wmm(WMM_2010)


class TestFetchFilteredDataCSVModelWMM2010(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "WMM2010"
    model = load_model_wmm(WMM_2010)


class TestAsyncFetchFilteredDataCSVModelWMM2010(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "WMM2010"
    model = load_model_wmm(WMM_2010)


class TestFetchFilteredDataCDFModelWMM2010(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "WMM2010"
    model = load_model_wmm(WMM_2010)


class TestAsyncFetchFilteredDataCDFModelWMM2010(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "WMM2010"
    model = load_model_wmm(WMM_2010)


class TestFetchDataCSVModelWMM2015(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "WMM2015"
    model = load_model_wmm(WMM_2015)


class TestFetchFilteredDataCSVModelWMM2015(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "WMM2015"
    model = load_model_wmm(WMM_2015)


class TestAsyncFetchFilteredDataCSVModelWMM2015(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "WMM2015"
    model = load_model_wmm(WMM_2015)


class TestFetchFilteredDataCDFModelWMM2015(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "WMM2015"
    model = load_model_wmm(WMM_2015)


class TestAsyncFetchFilteredDataCDFModelWMM2015(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "WMM2015"
    model = load_model_wmm(WMM_2015)


class TestFetchDataCSVModelWMM(TestFetchDataCSVModelWMM2015):
    model_name = "WMM"


class TestFetchFilteredDataCSVModelWMM(TestFetchFilteredDataCSVModelWMM2015):
    model_name = "WMM"


class TestAsyncFetchFilteredDataCSVModelWMM(TestAsyncFetchFilteredDataCSVModelWMM2015):
    model_name = "WMM"


class TestFetchFilteredDataCDFModelWMM(TestFetchFilteredDataCDFModelWMM2015):
    model_name = "WMM"


class TestAsyncFetchFilteredDataCDFModelWMM(TestAsyncFetchFilteredDataCDFModelWMM2015):
    model_name = "WMM"

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelIGRF11(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "IGRF11"
    model = load_model_igrf(IGRF11)


class TestFetchFilteredDataCSVModelIGRF11(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "IGRF11"
    model = load_model_igrf(IGRF11)


class TestAsyncFetchFilteredDataCSVModelIGRF11(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "IGRF11"
    model = load_model_igrf(IGRF11)


class TestFetchFilteredDataCDFModelIGRF11(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "IGRF11"
    model = load_model_igrf(IGRF11)


class TestAsyncFetchFilteredDataCDFModelIGRF11(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "IGRF11"
    model = load_model_igrf(IGRF11)


class TestFetchDataCSVModelIGRF12(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12)


class TestFetchFilteredDataCSVModelIGRF12(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12)


class TestAsyncFetchFilteredDataCSVModelIGRF12(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12)


class TestFetchFilteredDataCDFModelIGRF12(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12)


class TestAsyncFetchFilteredDataCDFModelIGRF12(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "IGRF12"
    model = load_model_shc(IGRF12)


class TestFetchDataCSVModelIGRF(TestFetchDataCSVModelIGRF12):
    model_name = "IGRF"


class TestFetchFilteredDataCSVModelIGRF(TestFetchFilteredDataCSVModelIGRF12):
    model_name = "IGRF"


class TestAsyncFetchFilteredDataCSVModelIGRF(TestAsyncFetchFilteredDataCSVModelIGRF12):
    model_name = "IGRF"


class TestFetchFilteredDataCDFModelIGRF(TestFetchFilteredDataCDFModelIGRF12):
    model_name = "IGRF"


class TestAsyncFetchFilteredDataCDFModelIGRF(TestAsyncFetchFilteredDataCDFModelIGRF12):
    model_name = "IGRF"

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelSIFM(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "SIFM"
    model = load_model_shc(SIFM)


class TestFetchFilteredDataCSVModelSIFM(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "SIFM"
    model = load_model_shc(SIFM)


class TestAsyncFetchFilteredDataCSVModelSIFM(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "SIFM"
    model = load_model_shc(SIFM)


class TestFetchFilteredDataCDFModelSIFM(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "SIFM"
    model = load_model_shc(SIFM)


class TestAsyncFetchFilteredDataCDFModelSIFM(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "SIFM"
    model = load_model_shc(SIFM)

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelCHAOS5Static(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "CHAOS-5-Static"
    model = load_model_shc(CHAOS5_STATIC)


class TestFetchFilteredDataCSVModelCHAOS5Static(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "CHAOS-5-Static"
    model = load_model_shc(CHAOS5_STATIC)


class TestAsyncFetchFilteredDataCSVModelCHAOS5Static(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "CHAOS-5-Static"
    model = load_model_shc(CHAOS5_STATIC)


class TestFetchFilteredDataCDFModelCHAOS5Static(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "CHAOS-5-Static"
    model = load_model_shc(CHAOS5_STATIC)


class TestAsyncFetchFilteredDataCDFModelCHAOS5Static(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "CHAOS-5-Static"
    model = load_model_shc(CHAOS5_STATIC)


class TestFetchDataCSVModelCHAOS6Static(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestFetchFilteredDataCSVModelCHAOS6Static(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestAsyncFetchFilteredDataCSVModelCHAOS6Static(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestFetchFilteredDataCDFModelCHAOS6Static(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestAsyncFetchFilteredDataCDFModelCHAOS6Static(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "CHAOS-6-Static"
    model = load_model_shc(CHAOS6_STATIC)


class TestFetchDataCSVModelCHAOSStatic(TestFetchDataCSVModelCHAOS6Static):
    model_name = "CHAOS-Static"


class TestFetchFilteredDataCSVModelCHAOSStatic(TestFetchFilteredDataCSVModelCHAOS6Static):
    model_name = "CHAOS-Static"


class TestAsyncFetchFilteredDataCSVModelCHAOSStatic(TestAsyncFetchFilteredDataCSVModelCHAOS6Static):
    model_name = "CHAOS-Static"


class TestFetchFilteredDataCDFModelCHAOSStatic(TestFetchFilteredDataCDFModelCHAOS6Static):
    model_name = "CHAOS-Static"


class TestAsyncFetchFilteredDataCDFModelCHAOSStatic(TestAsyncFetchFilteredDataCDFModelCHAOS6Static):
    model_name = "CHAOS-Static"

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelCHAOS5Core(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "CHAOS-5-Core"
    model = load_model_shc(CHAOS5_CORE_V4)


class TestFetchFilteredDataCSVModelCHAOS5Core(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "CHAOS-5-Core"
    model = load_model_shc(CHAOS5_CORE_V4)


class TestAsyncFetchFilteredDataCSVModelCHAOS5Core(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "CHAOS-5-Core"
    model = load_model_shc(CHAOS5_CORE_V4)


class TestFetchFilteredDataCDFModelCHAOS5Core(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "CHAOS-5-Core"
    model = load_model_shc(CHAOS5_CORE_V4)


class TestAsyncFetchFilteredDataCDFModelCHAOS5Core(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "CHAOS-5-Core"
    model = load_model_shc(CHAOS5_CORE_V4)


class TestFetchDataCSVModelCHAOS6Core(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(CHAOS6_CORE_LATEST)


class TestFetchFilteredDataCSVModelCHAOS6Core(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(CHAOS6_CORE_LATEST)


class TestAsyncFetchFilteredDataCSVModelCHAOS6Core(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(CHAOS6_CORE_LATEST)


class TestFetchFilteredDataCDFModelCHAOS6Core(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(CHAOS6_CORE_LATEST)


class TestAsyncFetchFilteredDataCDFModelCHAOS6Core(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "CHAOS-6-Core"
    model = load_model_shc(CHAOS6_CORE_LATEST)


class TestFetchDataCSVModelCHAOSCore(TestFetchDataCSVModelCHAOS6Core):
    model_name = "CHAOS-Core"


class TestFetchFilteredDataCSVModelCHAOSCore(TestFetchFilteredDataCSVModelCHAOS6Core):
    model_name = "CHAOS-Core"


class TestAsyncFetchFilteredDataCSVModelCHAOSCore(TestAsyncFetchFilteredDataCSVModelCHAOS6Core):
    model_name = "CHAOS-Core"


class TestFetchFilteredDataCDFModelCHAOSCore(TestFetchFilteredDataCDFModelCHAOS6Core):
    model_name = "CHAOS-Core"


class TestAsyncFetchFilteredDataCDFModelCHAOSCore(TestAsyncFetchFilteredDataCDFModelCHAOS6Core):
    model_name = "CHAOS-Core"

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelCHAOS5Combined(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "CHAOS-5-Combined"
    model = load_model_shc_combined(CHAOS5_CORE_V4, CHAOS5_STATIC)


class TestFetchFilteredDataCSVModelCHAOS5Combined(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "CHAOS-5-Combined"
    model = load_model_shc_combined(CHAOS5_CORE_V4, CHAOS5_STATIC)


class TestAsyncFetchFilteredDataCSVModelCHAOS5Combined(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "CHAOS-5-Combined"
    model = load_model_shc_combined(CHAOS5_CORE_V4, CHAOS5_STATIC)


class TestFetchFilteredDataCDFModelCHAOS5Combined(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "CHAOS-5-Combined"
    model = load_model_shc_combined(CHAOS5_CORE_V4, CHAOS5_STATIC)


class TestAsyncFetchFilteredDataCDFModelCHAOS5Combined(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "CHAOS-5-Combined"
    model = load_model_shc_combined(CHAOS5_CORE_V4, CHAOS5_STATIC)


class TestFetchDataCSVModelCHAOS6Combined(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "CHAOS-6-Combined"
    model = load_model_shc_combined(CHAOS6_CORE_LATEST, CHAOS6_STATIC)


class TestFetchFilteredDataCSVModelCHAOS6Combined(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "CHAOS-6-Combined"
    model = load_model_shc_combined(CHAOS6_CORE_LATEST, CHAOS6_STATIC)


class TestAsyncFetchFilteredDataCSVModelCHAOS6Combined(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "CHAOS-6-Combined"
    model = load_model_shc_combined(CHAOS6_CORE_LATEST, CHAOS6_STATIC)


class TestFetchFilteredDataCDFModelCHAOS6Combined(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "CHAOS-6-Combined"
    model = load_model_shc_combined(CHAOS6_CORE_LATEST, CHAOS6_STATIC)


class TestAsyncFetchFilteredDataCDFModelCHAOS6Combined(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "CHAOS-6-Combined"
    model = load_model_shc_combined(CHAOS6_CORE_LATEST, CHAOS6_STATIC)


class TestFetchDataCSVModelCHAOSCombined(TestFetchDataCSVModelCHAOS6Combined):
    model_name = "CHAOS-Combined"


class TestFetchFilteredDataCSVModelCHAOSCombined(TestFetchFilteredDataCSVModelCHAOS6Combined):
    model_name = "CHAOS-Combined"


class TestAsyncFetchFilteredDataCSVModelCHAOSCombined(TestAsyncFetchFilteredDataCSVModelCHAOS6Combined):
    model_name = "CHAOS-Combined"


class TestFetchFilteredDataCDFModelCHAOSCombined(TestFetchFilteredDataCDFModelCHAOS6Combined):
    model_name = "CHAOS-Combined"


class TestAsyncFetchFilteredDataCDFModelCHAOSCombined(TestAsyncFetchFilteredDataCDFModelCHAOS6Combined):
    model_name = "CHAOS-Combined"

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelMCO2C(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestFetchFilteredDataCSVModelMCO2C(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestAsyncFetchFilteredDataCSVModelMCO2C(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestFetchFilteredDataCDFModelMCO2C(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestAsyncFetchFilteredDataCDFModelMCO2C(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MCO_SHA_2C"
    model = load_model_shc(MCO_SHA_2C)


class TestFetchDataCSVModelMCO2D(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestFetchFilteredDataCSVModelMCO2D(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestAsyncFetchFilteredDataCSVModelMCO2D(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestFetchFilteredDataCDFModelMCO2D(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestAsyncFetchFilteredDataCDFModelMCO2D(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MCO_SHA_2D"
    model = load_model_shc(MCO_SHA_2D)


class TestFetchDataCSVModelMCO2F(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "MCO_SHA_2F"
    model = load_model_shc(MCO_SHA_2F)


class TestFetchFilteredDataCSVModelMCO2F(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MCO_SHA_2F"
    model = load_model_shc(MCO_SHA_2F)


class TestAsyncFetchFilteredDataCSVModelMCO2F(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MCO_SHA_2F"
    model = load_model_shc(MCO_SHA_2F)


class TestFetchFilteredDataCDFModelMCO2F(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MCO_SHA_2F"
    model = load_model_shc(MCO_SHA_2F)


class TestAsyncFetchFilteredDataCDFModelMCO2F(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MCO_SHA_2F"
    model = load_model_shc(MCO_SHA_2F)

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelMLI2C(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestFetchFilteredDataCSVModelMLI2C(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestAsyncFetchFilteredDataCSVModelMLI2C(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestFetchFilteredDataCDFModelMLI2C(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestAsyncFetchFilteredDataCDFModelMLI2C(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MLI_SHA_2C"
    model = load_model_shc(MLI_SHA_2C)


class TestFetchDataCSVModelMLI2D(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)


class TestFetchFilteredDataCSVModelMLI2D(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)


class TestAsyncFetchFilteredDataCSVModelMLI2D(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)


class TestFetchFilteredDataCDFModelMLI2D(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)


class TestAsyncFetchFilteredDataCDFModelMLI2D(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MLI_SHA_2D"
    model = load_model_shc(MLI_SHA_2D)

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestFetchFilteredDataCSVModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestAsyncFetchFilteredDataCSVModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestFetchFilteredDataCDFModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestAsyncFetchFilteredDataCDFModelMMA2CPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MMA_SHA_2C-Primary"
    model = load_model_swarm_mma_2c_external(MMA_SHA_2C)


class TestFetchDataCSVModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)


class TestFetchFilteredDataCSVModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)


class TestAsyncFetchFilteredDataCSVModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)


class TestFetchFilteredDataCDFModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)


class TestAsyncFetchFilteredDataCDFModelMMA2CSecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MMA_SHA_2C-Secondary"
    model = load_model_swarm_mma_2c_internal(MMA_SHA_2C)

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestFetchFilteredDataCSVModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestAsyncFetchFilteredDataCSVModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestFetchFilteredDataCDFModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestAsyncFetchFilteredDataCDFModelMMA2FPrimary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MMA_SHA_2F-Primary"
    model = load_model_swarm_mma_2f_geo_external(MMA_SHA_2F)


class TestFetchDataCSVModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, FetchDataCSVMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)


class TestFetchFilteredDataCSVModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)


class TestAsyncFetchFilteredDataCSVModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)


class TestFetchFilteredDataCDFModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)


class TestAsyncFetchFilteredDataCDFModelMMA2FSecondary(TestCase, MagneticModelTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MMA_SHA_2F-Secondary"
    model = load_model_swarm_mma_2f_geo_internal(MMA_SHA_2F)

#-------------------------------------------------------------------------------

class TestFetchDataCSVModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, FetchDataCSVMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestFetchFilteredDataCSVModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestAsyncFetchFilteredDataCSVModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestFetchFilteredDataCDFModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestAsyncFetchFilteredDataCDFModelMIO2CPrimary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MIO_SHA_2C-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2C)


class TestFetchDataCSVModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, FetchDataCSVMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestFetchFilteredDataCSVModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestAsyncFetchFilteredDataCSVModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestFetchFilteredDataCDFModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestAsyncFetchFilteredDataCDFModelMIO2CSecondary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MIO_SHA_2C-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2C)


class TestFetchDataCSVModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, FetchDataCSVMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestFetchFilteredDataCSVModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestAsyncFetchFilteredDataCSVModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestFetchFilteredDataCDFModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestAsyncFetchFilteredDataCDFModelMIO2DPrimary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MIO_SHA_2D-Primary"
    model = load_model_swarm_mio_external(MIO_SHA_2D)


class TestFetchDataCSVModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, FetchDataCSVMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)


class TestFetchFilteredDataCSVModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCSVMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)


class TestAsyncFetchFilteredDataCSVModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCSVMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)


class TestFetchFilteredDataCDFModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, FetchFilteredDataCDFMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)


class TestAsyncFetchFilteredDataCDFModelMIO2DSecondary(TestCase, MagneticModelMIOTestMixIn, AsyncFetchFilteredDataCDFMixIn):
    model_name = "MIO_SHA_2D-Secondary"
    model = load_model_swarm_mio_internal(MIO_SHA_2D)

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
