#!/usr/bin/env python3
#-------------------------------------------------------------------------------
#
# Convert ULF and PC1 products removing invalid records
#
# Author: Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2025 EOX IT Services GmbH
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
# pylint: disable=missing-module-docstring,too-many-arguments,too-many-locals


import re
import sys
import logging
import os.path
import datetime
from collections import namedtuple
import numpy
from common import (
    init_console_logging, CommandError, cdf_open,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
    CDF_TYPE_LABEL, CDF_UINT4, CDF_EPOCH, CdfTypeEpoch,
)


class TestError(AssertionError):
    """ Test error exception. """


class App:
    """ The app. """
    NAME = "convert_ulf_product.py"
    VERSION = "1.0.0"

    logger = logging.getLogger(__name__)

    @classmethod
    def run(cls, *argv):
        """ Run the app. """
        init_console_logging("DEBUG")
        try:
            sys.exit(cls.main(**cls.parse_inputs(argv)))
        except CommandError as error:
            cls.logger.error("%s", error)
            sys.exit(1)

    @staticmethod
    def usage(exename, file=sys.stderr):
        """ Print usage. """
        print(
            f"USAGE: {os.path.basename(exename)} <filename> <output filename>"
            " [--check-if-needed][--test]", file=file
        )
        print("\n".join([
            "DESCRIPTION:",
            "  Convert ULF ULFxMAG_2F and PC1xMAG_2F product to a VirES-friendly ",
            "  format, removing invalid records.",
            "  With the --check-if-needed option, the program tests whether ",
            "  the source file needs to be converted without doing the actual",
            "  conversion. Zero exit code indicates the conversion is required.",
            "  With the --test option, the program tests the existing converted",
            "  file against the source without doing the actual conversion.",
        ]), file=file)

    @classmethod
    def parse_inputs(cls, argv):
        """ Parse input arguments. """
        args = []
        test_converted_only = False
        test_source = False

        for arg in argv[1:]:
            if arg == "--test":
                test_converted_only = True
            elif arg == "--check-if-needed":
                test_source = True
            else:
                args.append(arg)

        try:
            input_filename = args[0]
            output_filename = None if test_source else args[1]
        except IndexError:
            cls.usage(argv[0])
            raise CommandError("Not enough input arguments!") from None

        return {
            "input_filename": input_filename,
            "output_filename": output_filename,
            "test_source": test_source,
            "test_converted_only": test_converted_only,
        }

    @classmethod
    def main(cls, input_filename, output_filename, test_converted_only=False,
             test_source=False):
        """ Main subroutine. """
        if test_source:
            if cls.test_if_conversion_needed(input_filename):
                cls.logger.info(
                    "%s: product conversion is required.",
                    os.path.basename(input_filename)
                )
                return 0
            cls.logger.info(
                "%s: product conversion is not required.",
                os.path.basename(input_filename)
            )
            return 1

        if not test_converted_only:
            cls.convert_product(input_filename, output_filename)

        try:
            cls.test_converted_product(input_filename, output_filename)
        except TestError as error:
            raise CommandError(f"Test of the converted file failed! {error}") from None

        return 0

    @classmethod
    def test_if_conversion_needed(cls, input_filename):
        """ Test if the source product file requires conversion. """
        with cdf_open(input_filename) as cdf:
            return UlfProduct.test_if_conversion_needed(cdf)

    @classmethod
    def convert_product(cls, input_filename, output_filename):
        """ Perform the file conversion. """

        cls.logger.info("converting %s -> %s", input_filename, output_filename)

        with cdf_open(input_filename) as input_cdf:

            tmp_filename = f"{output_filename}.tmp.cdf"

            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)

            try:
                with cdf_open(tmp_filename, "w") as output_cdf:
                    UlfProduct.convert(output_cdf, input_cdf)

                os.rename(tmp_filename, output_filename)

            except:
                if os.path.exists(tmp_filename):
                    os.remove(tmp_filename)
                raise

    @classmethod
    def test_converted_product(cls, input_filename, output_filename):
        """ Test the converted product file against the source.
        Raises TestError exception if the test does not pass.
        """
        cls.logger.info("testing converted %s -> %s", input_filename, output_filename)
        with cdf_open(input_filename) as input_cdf:
            with cdf_open(output_filename) as output_cdf:
                UlfProduct.test_converted(output_cdf, input_cdf)


class UlfProduct:
    """ Conversion of ULF products with multiple time-variables filtering
    out records outside the nominal product time-span.
    """

    RE_TIMESTAMP = re.compile(
        r'^(?P<year>\d{4,4})-(?P<month>\d{2,2})-(?P<day>\d{2,2})T'
        r'(?P<hour>\d{2,2}):(?P<minute>\d{2,2}):(?P<second>\d{2,2})$'
    )

    TIMESTAMP_VARIABLE_PREFIX = "Timestamp"

    TIMESPAN_ATTRIBUTE = "Timespan"

    CDF_CREATOR = (
        f"EOX:{App.NAME}-{App.VERSION} [{SPACEPY_NAME}-{SPACEPY_VERSION}, "
        f"libcdf-{LIBCDF_VERSION}]"
    )

    CDF_VARIABLE_PARAMETERS = {
        "compress": GZIP_COMPRESSION,
        "compress_param": GZIP_COMPRESSION_LEVEL4
    }

    SKIPED_ATTRIBUTES = ()

    @classmethod
    def test_if_conversion_needed(cls, cdf):
        """ Test if the CDF file requires conversion. """
        variable_groups = cls._extract_variable_groups(cdf)
        product_start, product_end = cls._read_time_extent_from_attribute(cdf)
        for time_variable in variable_groups:
            start, end = cls._get_time_extent(cdf, time_variable)
            if product_start > start or product_end <= end:
                return True
        return False

    @classmethod
    def convert(cls, cdf_dst, cdf_src):
        """ Convert CDF product. """

        def _get_mapping_index(times, start, end):
            return ((start <= times) & (times < end)).nonzero()[0]

        product_start, product_end = cls._read_time_extent_from_attribute(cdf_src)

        variable_groups = cls._extract_variable_groups(cdf_src)

        mapping_indices = {
            time_variable: _get_mapping_index(
                cls._read_times(cdf_src, time_variable),
                product_start, product_end
            )
            for time_variable in variable_groups
        }

        # write the output product
        cls._set_global_attributes(cdf_dst, cdf_src)

        # copy variables
        for time_variable, (suffix, variables) in variable_groups.items():
            index = mapping_indices[time_variable]

            for variable in variables:
                cls._copy_variable(cdf_dst, cdf_src, variable, index=index)

            cls._save_cdf_variable(
                cdf_dst, f"SourceIndex{suffix}", CDF_UINT4, index,
                attrs={
                    "DESCRIPTION": "Mapping to the original product records.",
                    "UNITS": " ",
                    "FORMAT": "I6",
                }
            )

    @classmethod
    def test_converted(cls, cdf_dst, cdf_src):
        """ Test converted CDF product. """

        def _test_time_variable(variable, index):
            times_src = cls._read_times(cdf_src, variable)
            rejected_dst = numpy.full(times_src.shape, True)
            rejected_dst[index] = False
            rejected_src = (start_src > times_src) | (times_src >= end_src)
            if not numpy.array_equal(rejected_dst, rejected_src):
                raise TestError(
                    f"Selected {variable} values do not match the source!"
                )

        def _test_variable(variable, index):
            data_src = cdf_src.raw_var(variable)[...]
            data_dst = cdf_dst.raw_var(variable)[...]
            if not numpy.array_equal(data_dst, data_src[index], equal_nan=True):
                raise TestError(
                    f"Converted {variable} values do not match the source!"
                )

        start_dst, end_dst = cls._read_time_extent_from_attribute(cdf_dst)
        start_src, end_src = cls._read_time_extent_from_attribute(cdf_src)

        if (start_dst, end_dst) != (start_src, end_src):
            raise TestError("Timespan attribute mismatch!")

        variable_groups_src = cls._extract_variable_groups(cdf_src)
        variable_groups_dst = cls._extract_variable_groups(cdf_dst)

        if set(variable_groups_src) != set(variable_groups_dst):
            raise TestError("Mismatch of time variables!")

        for time_variable, (suffix, variables_src) in variable_groups_src.items():
            variables_dst = variable_groups_dst[time_variable].variables

            index_variable = f"SourceIndex{suffix}"
            if index_variable in variables_dst:
                variables_dst.remove(index_variable)
            else:
                raise TestError(f"Index variable {index_variable} not found!")

            index = cdf_dst.raw_var(index_variable)[...]

            if set(variables_src) != set(variables_dst):
                raise TestError("Mismatch of data variables!")

            _test_time_variable(time_variable, index)
            for variable in variables_src:
                _test_variable(variable, index)

    @classmethod
    def _extract_variable_groups(cls, cdf):
        """ Extract variable groups for each dataset. """
        time_variables = cls._extract_time_variables(cdf)

        Record = namedtuple("Record", ["suffix", "variables"])
        variable_groups = {
            record.variable: Record(record.suffix, [])
            for record in time_variables
        }
        time_variables = cls._extract_time_variables(cdf)

        for variable in cdf:
            for suffix, time_variable in reversed(time_variables):
                if variable.endswith(suffix):
                    variable_groups[time_variable].variables.append(variable)
                    break
            else:
                raise ValueError(
                    f"Failed to assign {variable} variable to a variable group!"
                )

        return variable_groups

    @classmethod
    def _extract_time_variables(cls, cdf):
        Record = namedtuple("Record", ["suffix", "variable"])
        prefix = cls.TIMESTAMP_VARIABLE_PREFIX
        suffix_offset = len(cls.TIMESTAMP_VARIABLE_PREFIX)
        time_variables = [
            Record(variable[suffix_offset:], variable)
            for variable in cdf if variable.startswith(prefix)
        ]
        time_variables = sorted(
            time_variables, key=lambda record: (len(record.suffix), record.suffix)
        )
        return time_variables

    @classmethod
    def _read_time_extent_from_attribute(cls, cdf):

        def _parse_timestamp(timestamp, precision="s"):
            match = cls.RE_TIMESTAMP.match(timestamp)
            if not match:
                raise ValueError(f"Invalid product timestamp {timestamp}!")
            return numpy.datetime64(timestamp, precision)

        def _parse_utc_timetamp(time_str):
            standard, _, timestamp = time_str.partition("=")
            if standard != "UTC":
                raise ValueError(f"Unexpected format of {time_str} timestamp!")
            return _parse_timestamp(timestamp)

        try:
            timespan_start, timespan_end = cdf.attrs[cls.TIMESPAN_ATTRIBUTE]
        except (KeyError, ValueError, TypeError):
            raise ValueError(
                "Failed to read the {cls.TIMESPAN_ATTRIBUTE} global attribute!"
            ) from None
        return (
            _parse_utc_timetamp(timespan_start),
            _parse_utc_timetamp(timespan_end) + numpy.timedelta64(1, "s")
        )

    @classmethod
    def _get_time_extent(cls, cdf, time_variable):
        times = cls._read_times(cdf, time_variable)
        return times.min(), times.max()

    @classmethod
    def _read_times(cls, cdf, time_variable):
        time_variable = cdf.raw_var(time_variable)
        cdf_type = time_variable.type()
        if cdf_type == CDF_EPOCH:
            return CdfTypeEpoch.decode(time_variable[...])
        raise TypeError(
            "Unsupported timestamp type "
            f"{CDF_TYPE_LABEL.get(cdf_type, cdf_type)}!"
        )

    @classmethod
    def _set_global_attributes(cls, cdf_dst, cdf_src):

        # NOTE CDF.attrs.update() does not preserve time data type
        for key, (head, *tail) in cdf_src.attrs.items():
            if key in cls.SKIPED_ATTRIBUTES:
                continue
            cdf_dst.attrs.new(key, head, type=(
                CDF_EPOCH if isinstance(head, datetime.datetime) else None
            ))
            for item in tail:
                cdf_dst.attrs[key].append(item)

        cdf_dst.attrs.update({
            "CREATED": f"{datetime.datetime.utcnow():%Y-%m-%dT%H:%M:%S}Z",
            "CREATOR": cls.CDF_CREATOR,
        })

    @classmethod
    def _copy_variable(cls, cdf_dst, cdf_src, variable_dst, variable_src=None,
                       type_dst=None, convert_data=None, index=Ellipsis):
        if not variable_src:
            variable_src = variable_dst

        var_src = cdf_src.raw_var(variable_src)

        if type_dst is None:
            type_dst = var_src.type()

        data = var_src[...]
        if convert_data:
            data, type_dst = convert_data(data)

        cls._save_cdf_variable(
            cdf_dst, variable_dst, type_dst, data[index], var_src.attrs,
        )

    @classmethod
    def _save_cdf_variable(cls, cdf, variable, cdf_type, data, attrs=None):
        cdf.new(
            variable, data, cdf_type, dims=data.shape[1:],
            **cls.CDF_VARIABLE_PARAMETERS,
        )
        if attrs:
            cdf[variable].attrs.update(attrs)


if __name__ == "__main__":
    App.run(*sys.argv)
