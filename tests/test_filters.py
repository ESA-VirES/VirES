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
from numpy import asarray
from numpy.testing import assert_allclose, assert_equal
from time_util import (
    parse_datetime, parse_duration, datetime_to_mjd2000, timedelta_to_days,
)
from cdf_util import load_cdf
from wps_util import (
    WpsPostRequestMixIn, WpsAsyncPostRequestMixIn,
    CsvRequestMixIn, CdfRequestMixIn,
    InvalidParameterValue,
)
from filter_util import (
    EqualityFilter, RangeFilter, ComponentRangeFilter, RangeFilterCO, OrderBy,
    DailySubsampling, Subsampling,
)


DEFAULT_ATOL = 1e-6
ATOL = {
    "Timestamp": 1e-9,
}

START_TIME = parse_datetime("2016-01-01T22:00:00Z")
END_TIME = parse_datetime("2016-01-02T02:00:00Z")

MAGx_LR_1B = "./data/SW_OPER_MAGx_LR_1B.cdf"

#-------------------------------------------------------------------------------

class FetchFilteredDataCsvMixIn(CsvRequestMixIn, WpsPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data.xml"


class AsyncFetchFilteredDataCsvMixIn(CsvRequestMixIn, WpsAsyncPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data_async.xml"


class FetchFilteredDataCdfMixIn(CdfRequestMixIn, WpsPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data.xml"


class AsyncFetchFilteredDataCdfMixIn(CdfRequestMixIn, WpsAsyncPostRequestMixIn):
    template_source = "test_vires_fetch_filtered_data_async.xml"

#-------------------------------------------------------------------------------

class FilteredDataTestMixIn(object):
    variables = []
    filters = []
    samplig = None
    collections = {}
    reference_data = None
    reference_data_filters = []
    time_variable = None
    order_by = ()

    def assert_almost_equal_datasets(self, tested, expected):
        def _compare_variable(variable):
            try:
                if tested[variable].dtype.kind == 'S':
                    assert_equal(tested[variable], expected[variable])
                else:
                    assert_allclose(
                        tested[variable], expected[variable],
                        atol=ATOL.get(variable, DEFAULT_ATOL)
                    )
            except AssertionError as error:
                raise AssertionError("variable %s: %s" % (variable, error))

        if set(tested) != set(expected):
            raise AssertionError("Variable mismatch!\n+ %s\n- %s" % (
                ", ".join(sorted(tested)), ", ".join(sorted(expected)),
            ))

        _compare_variable(self.time_variable)
        for key in (key for key in expected if key != self.time_variable):
            _compare_variable(key)


    def _fetch_data(self, begin_time, end_time, filters=None, sampling=None):
        """ Fetch data from the tested server. """
        request = self.get_request(
            variables=self.variables,
            begin_time=begin_time,
            end_time=end_time,
            filters=filters,
            sampling_step=sampling,
            collection_ids=self.collections,
        )
        data = self.get_parsed_response(request)
        # make sure arrays are returned
        data = {key: asarray(value) for key, value in data.items()}
        # optional ordering
        data = OrderBy(*self.order_by).filter(data)
        return data

    def _expected_data(self, begin_time, end_time, filters=None, sampling=None):
        """ Load expected data from the reference data file. """
        return self._apply_filters(
            load_cdf(self.reference_data, self.variables),
            [
                RangeFilterCO(
                    self.time_variable,
                    datetime_to_mjd2000(begin_time),
                    datetime_to_mjd2000(end_time)
                ),
                DailySubsampling(
                    self.time_variable,
                    None if sampling is None else timedelta_to_days(sampling),
                    atol=5.787037037037037e-09 # 0.5ms tolerance
                ),
            ] + self.reference_data_filters + (filters or []) + [
                OrderBy(*self.order_by)
            ]
        )

    @staticmethod
    def _apply_filters(data, filters):
        for filter_ in filters:
            data = filter_.filter(data)
        return data

    def _compare_data(self, begin_time, end_time, filters=None, sampling=None):
        response = self._fetch_data(begin_time, end_time, filters, sampling)
        expected = self._expected_data(begin_time, end_time, filters, sampling)
        self.assert_almost_equal_datasets(response, expected)
        return response, expected

#-------------------------------------------------------------------------------

class MAGxLRTestMixIn(FilteredDataTestMixIn):
    variables = [
        'Timestamp', 'Latitude', 'Longitude', 'Radius', 'Spacecraft',
        'B_NEC', 'B_VFM', 'F', 'B_error', 'F_error', 'Flags_B', 'Flags_F',
        'Flags_Platform', 'Flags_q', 'dF_AOCS', 'dF_other', 'dB_AOCS',
        'dB_other', 'dB_Sun', 'q_NEC_CRF', 'ASM_Freq_Dev', 'Att_error',
        'SyncStatus',
    ]
    time_variable = "Timestamp"
    order_by = ("Spacecraft",)
    begin_time = START_TIME
    end_time = END_TIME
    reference_data = MAGx_LR_1B
    collections = {
        "AA": ["SW_OPER_MAGA_LR_1B"],
        "BB": ["SW_OPER_MAGB_LR_1B"],
        "CC": ["SW_OPER_MAGC_LR_1B"],
    }

    def test_no_filter(self):
        self._compare_data(self.begin_time, self.end_time)

    def test_scalar_filter(self):
        self._compare_data(
            self.begin_time, self.end_time,
            filters=[
                RangeFilter('Flags_F', 0, 1),
                RangeFilter('F', 3e4, 4e4),
            ]
        )

    def test_vector_filter(self):
        self._compare_data(
            self.begin_time, self.end_time,
            filters=[
                RangeFilter('Flags_B', 0, 1),
                ComponentRangeFilter('B_NEC', 2, -1e3, 1e-3),
            ]
        )

    def test_sampling_short(self):
        self._compare_data(
            self.begin_time, self.end_time,
            sampling=parse_duration("PT1.5S"),
        )

    def test_sampling_long(self):
        self._compare_data(
            self.begin_time, self.end_time,
            sampling=parse_duration("PT2.5H"),
        )

    def test_scalar_filter_on_vector_data_single_filter(self):
        self.assertRaises(
            InvalidParameterValue,
            self._fetch_data, self.begin_time, self.end_time,
            filters=[
                RangeFilter('B_NEC', -1e3, 1e-3)
            ]
        )

    def test_scalar_filter_on_vector_data_multiple_filters(self):
        self.assertRaises(
            InvalidParameterValue,
            self._fetch_data, self.begin_time, self.end_time,
            filters=[
                RangeFilter('Flags_B', 0, 1),
                RangeFilter('B_NEC', -1e3, 1e-3)
            ]
        )

class TestMAGxLRFilteredCSV(TestCase, MAGxLRTestMixIn, FetchFilteredDataCsvMixIn):
    pass

class TestMAGxLRFilteredCDF(TestCase, MAGxLRTestMixIn, FetchFilteredDataCdfMixIn):
    pass

class TestMAGxLRFilteredAsyncCDF(TestCase, MAGxLRTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    pass

class TestMAGxLRFilteredAsyncCSV(TestCase, MAGxLRTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    pass

#-------------------------------------------------------------------------------

class MAGALRTestMixIn(MAGxLRTestMixIn):
    order_by = ()
    reference_data = MAGx_LR_1B
    reference_data_filters = [EqualityFilter("Spacecraft", 'A')]
    collections = {"AA": ["SW_OPER_MAGA_LR_1B"]}


class TestMAGALRFilteredCSV(TestCase, MAGALRTestMixIn, FetchFilteredDataCsvMixIn):
    pass

class TestMAGALRFilteredCDF(TestCase, MAGALRTestMixIn, FetchFilteredDataCdfMixIn):
    pass

class TestMAGALRFilteredAsyncCDF(TestCase, MAGALRTestMixIn, AsyncFetchFilteredDataCdfMixIn):
    pass

class TestMAGALRFilteredAsyncCSV(TestCase, MAGALRTestMixIn, AsyncFetchFilteredDataCsvMixIn):
    pass

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
