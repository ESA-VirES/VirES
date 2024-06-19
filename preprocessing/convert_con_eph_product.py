#!/usr/bin/env python3
#-------------------------------------------------------------------------------
#
# Convert TOLEOS multi-mission CON_EPH_2_ products
#
# Author: Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2024 EOX IT Services GmbH
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
# pylint: disable=missing-module-docstring,too-many-arguments
# pylint: disable=chained-comparison,consider-using-f-string

import re
import sys
import logging
import os.path
import datetime
import numpy
from common import (
    init_console_logging, CommandError, cdf_open,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
    CDF_DOUBLE, CDF_REAL8, CDF_EPOCH, CDF_CHAR, CDF_UINT4,
)


class TestError(AssertionError):
    """ Test error exception. """


class App:
    """ The app. """
    NAME = "convert_con_eph_product.py"
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
            " [--test]", file=file
        )
        print("\n".join([
            "DESCRIPTION:",
            "  Convert TOLEOS CON_EPH_2_ product to a VirES-friendly format.",
            "  With the --test option, the program tests the existing converted",
            "  file against the source.",
        ]), file=file)

    @classmethod
    def parse_inputs(cls, argv):
        """ Parse input arguments. """
        args = []
        test_only = False

        for arg in argv[1:]:
            if arg == "--test":
                test_only = True
            else:
                args.append(arg)

        try:
            input_filename = args[0]
            output_filename = args[1]
        except IndexError:
            cls.usage(argv[0])
            raise CommandError("Not enough input arguments!") from None

        return {
            "input_filename": input_filename,
            "output_filename": output_filename,
            "test_only": test_only,
        }

    @classmethod
    def main(cls, input_filename, output_filename, test_only=False):
        """ Main subroutine. """
        if not test_only:
            cls.convert_con_eph_product(input_filename, output_filename)
        try:
            cls.test_converted_con_eph_product(input_filename, output_filename)
        except TestError as error:
            raise CommandError(f"Test of the converted file failed! {error}") from None

    @classmethod
    def convert_con_eph_product(cls, input_filename, output_filename):
        """ Convert CON_EPH_2_ product to a VirES-friendly format. """
        with cdf_open(input_filename) as input_cdf:
            tmp_filename = f"{output_filename}.tmp.cdf"

            cls.logger.info("converting %s -> %s", input_filename, output_filename)

            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)

            try:
                with cdf_open(tmp_filename, "w") as output_cdf:
                    ConjuntionProduct.convert(output_cdf, input_cdf)

                os.rename(tmp_filename, output_filename)

            except:
                if os.path.exists(tmp_filename):
                    os.remove(tmp_filename)
                raise

    @classmethod
    def test_converted_con_eph_product(cls, input_filename, output_filename):
        """ Test converted CON_EPH_2_ product.
        Raises TestError exception if the test does not pass.
        """
        cls.logger.info("testing converted %s -> %s", input_filename, output_filename)
        with cdf_open(input_filename) as input_cdf:
            with cdf_open(output_filename) as output_cdf:
                ConjuntionProduct.test_converted(output_cdf, input_cdf)


class ConjuntionProduct:
    """ Conversion of TOLEOS CON_EPH_2_ products."""

    CDF_CREATOR = (
        f"EOX:{App.NAME}-{App.VERSION} [{SPACEPY_NAME}-{SPACEPY_VERSION}, "
        f"libcdf-{LIBCDF_VERSION}]"
    )

    CDF_VARIABLE_PARAMETERS = {
        "compress": GZIP_COMPRESSION,
        "compress_param": GZIP_COMPRESSION_LEVEL4
    }

    SKIPED_ATTRIBUTES = ("INFO", "CREATOR")

    TYPE_CONVERSIONS = {
        CDF_REAL8: CDF_DOUBLE,
    }

    TRANSLATED_VARIABLES = [
        "crossover_satellites",
        "plane_alignment_satellites",
    ]

    EXPANDED_VARIABLES = {
        "crossover_times": [
            "crossover_time_1",
            "crossover_time_2",
        ],
        "crossover_satellites": [
            "crossover_satellite_1",
            "crossover_satellite_2",
        ],
        "crossover_altitudes": [
            "crossover_altitude_1",
            "crossover_altitude_2",
        ],
        "crossover_local_solar_times": [
            "crossover_local_solar_time_1",
            "crossover_local_solar_time_2",
        ],
        "plane_alignment_time": ["plane_alignment_time"],
        "plane_alignment_satellites": [
            "plane_alignment_satellite_1",
            "plane_alignment_satellite_2",
        ],
        "plane_alignment_ltan": [
            "plane_alignment_ltan_1",
            "plane_alignment_ltan_2",
        ],
        "plane_alignment_altitudes": [
            "plane_alignment_altitude_1",
            "plane_alignment_altitude_2",
        ],
        "plane_alignment_ltan_rates": [
            "plane_alignment_ltan_rate_1",
            "plane_alignment_ltan_rate_2",
        ],
    }

    SATELITES_LEGEND = (
        "symbols: SWx - Swarm, CH - CHAMP,  GO - GOCE, GRx - GRACE, "
        "GFx - GRACE-FO"
    )

    VARIABLE_DESCRIPTION = {
        "crossover_time_1": "Crossover time of the first satellite (UTC)",
        "crossover_time_2": "Crossover time of the second satellite (UTC)",
        "crossover_satellite_1": f"ID of the first satellite ({SATELITES_LEGEND})",
        "crossover_satellite_2": f"ID of the second satellite ({SATELITES_LEGEND})",
        "crossover_altitude_1": "Altitude of the first satellite at crossover (GRS80)",
        "crossover_altitude_2": "Altitude of the second satellite at crossover (GRS80)",
        "crossover_local_solar_time_1": "Local solar time of the first satellite at crossover",
        "crossover_local_solar_time_2": "Local solar time of the second satellites at crossover",
        "plane_alignment_satellite_1": f"ID of the first satellite ({SATELITES_LEGEND})",
        "plane_alignment_satellite_2": f"ID of the second satellite ({SATELITES_LEGEND})",
        "plane_alignment_ltan_1": "LTAN of the first satellite" ,
        "plane_alignment_ltan_2": "LTAN of the second satellite",
        "plane_alignment_altitude_1": "Altitude of the first satellite",
        "plane_alignment_altitude_2": "Altitude of the second satellite" ,
        "plane_alignment_ltan_rate_1": "LTAN drift rate of the first satellite",
        "plane_alignment_ltan_rate_2": "LTAN drift rate of the second satellite",
    }

    RE_SC_MAPPING_PATTERN = re.compile(
        r"^Satellite ID of (?P<mission>\S+)(?: (?P<spacecraft>\S+))?"
        r" = (?P<index>[0-9]+)$"
    )

    SPACECRAFT_MAPPING = {
        ("Swarm", "A"): "SWA".encode("ASCII"),
        ("Swarm", "B"): "SWB".encode("ASCII"),
        ("Swarm", "C"): "SWC".encode("ASCII"),
        ("CHAMP", None): "CH".encode("ASCII"),
        ("GOCE", None): "GO".encode("ASCII"),
        ("GRACE", "1"): "GR1".encode("ASCII"),
        ("GRACE", "2"): "GR2".encode("ASCII"),
        ("GRACE-FO", "1"): "GF1".encode("ASCII"),
        ("GRACE-FO", "2"): "GF2".encode("ASCII"),
    }

    @classmethod
    def convert(cls, cdf_dst, cdf_src):
        """ Convert CON_EPH_2_ product to a VirES-friendly format. """

        # setup spacecraft translation from integer index to ASCII 3 letter code
        convert_spacecraft = cls._get_spacecraft_translator(
            cls._extrat_spacecraft_mapping(cdf_src)
        )

        def _get_data_conversion(variable):
            """ Get data conversion function or None if no conversion is applied. """
            if variable in cls.TRANSLATED_VARIABLES:
                return convert_spacecraft
            return None

        # setup data type conversion
        def _convert_data_type(cdf_type):
            """ Translate input CDF data type to the output one. """
            return cls.TYPE_CONVERSIONS.get(cdf_type, cdf_type)

        # generate sorting indices for the internal datasets
        sorting_indices = cls._get_sorting_indices(cdf_src)

        def _pick_sorting_index(variable):
            """ Pick the right sorting index matching the variable name. """
            for prefix, index in sorting_indices.items():
                if variable.startswith(prefix):
                    return index
            raise ValueError(
                f"Failed to sorting index matching the {variable!r} variable!"
            )

        # write the output product

        cls._set_global_attributes(cdf_dst, cdf_src)

        for variable in cdf_src:
            var_src = cdf_src[variable]

            options = {
                "type_dst": _convert_data_type(var_src.type()),
                "convert_data": _get_data_conversion(variable),
                "index": _pick_sorting_index(variable),
            }

            if len(var_src.shape) > 1 and variable in cls.EXPANDED_VARIABLES:
                cls._expand_variable(
                    cdf_dst, cdf_src, cls.EXPANDED_VARIABLES[variable],
                    variable, **options,
                )
            else:
                cls._copy_variable(cdf_dst, cdf_src, variable, **options)

        # write the indices mapping the sorted values to the original order

        for prefix, index in sorting_indices.items():
            cls._save_cdf_variable(
                cdf_dst, f"{prefix}index", CDF_UINT4,
                cls._reverse_sorting_index(index),
                {
                    "DESCRIPTION": (
                        "Index mapping the sorted data values"
                        " to the original order."
                    ),
                    "UNIT": "-",
                },
            )

    @classmethod
    def test_converted(cls, cdf_dst, cdf_src):
        """ Test converted CON_EPH_2_ product. """

        tested_variables = set()

        def test_time_order(variable):
            times = cdf_dst.raw_var(variable)[...]
            if times.size > 1 and (times[1:] - times[:-1]).min() < 0:
                raise TestError(f"Time variable {variable!r} is not sorted!")

        def test_variable(variable, index):
            tested_variables.add(variable)
            data_src = cdf_src.raw_var(variable)[...]
            data_dst = cdf_dst.raw_var(variable)[...]
            if not numpy.array_equal(data_dst[index], data_src, equal_nan=True):
                raise TestError(
                    f"Converted values do not match the source {variable!r} ones!"
                )

        def test_expanded_variable(variable, index):
            tested_variables.add(variable)
            data_src = cdf_src.raw_var(variable)[...]
            data_dst = numpy.stack([
                cdf_dst.raw_var(item)[...]
                for item in cls.EXPANDED_VARIABLES[variable]
            ], axis=-1)
            if not numpy.array_equal(data_dst[index], data_src, equal_nan=True):
                raise TestError(
                    f"Converted values do not match the {variable!r} source!"
                )

        def test_expanded_satellite_variable(variable, index, mapping):
            tested_variables.add(variable)
            data_src = cdf_src.raw_var(variable)[...]
            data_dst = numpy.stack([
                translate_spacecraft(cdf_dst.raw_var(item)[...], mapping)
                for item in cls.EXPANDED_VARIABLES[variable]
            ], axis=-1)
            if not numpy.array_equal(data_dst[index], data_src, equal_nan=True):
                raise TestError(
                    f"Converted values do not match the {variable!r} source!"
                )

        def translate_spacecraft(data, mapping):
            return numpy.vectorize(
                lambda symbol: mapping[symbol], otypes=["int"]
            )(data)

        # test sorted times
        test_time_order("crossover_time_1")
        test_time_order("plane_alignment_time")

        # test converted values
        reverse_spacecraft_mapping = {
            dst: src
            for src, dst in cls._extrat_spacecraft_mapping(cdf_src).items()
        }
        reverse_index = cdf_dst["crossover_index"][...]

        test_variable("crossover_time_difference", reverse_index)
        test_variable("crossover_latitude", reverse_index)
        test_variable("crossover_longitude", reverse_index)
        test_variable("crossover_magnetic_latitude", reverse_index)
        test_variable("crossover_magnetic_longitude", reverse_index)
        test_expanded_variable("crossover_times", reverse_index)
        test_expanded_variable("crossover_altitudes", reverse_index)
        test_expanded_variable("crossover_local_solar_times", reverse_index)
        test_expanded_satellite_variable(
            "crossover_satellites", reverse_index, reverse_spacecraft_mapping
        )

        reverse_index = cdf_dst["plane_alignment_index"][...]
        if len(cdf_src["plane_alignment_time"].shape) == 1:
            test_variable("plane_alignment_time", reverse_index)
        else:
            test_expanded_variable("plane_alignment_time", reverse_index)
        test_expanded_variable("plane_alignment_ltan", reverse_index)
        test_expanded_variable("plane_alignment_altitudes", reverse_index)
        test_expanded_variable("plane_alignment_ltan_rates", reverse_index)
        test_expanded_satellite_variable(
            "plane_alignment_satellites", reverse_index, reverse_spacecraft_mapping
        )

        # check if there is any variable not tested
        not_tested_variables = [
            variable for variable in cdf_src
            if variable not in tested_variables
        ]

        if not_tested_variables:
            raise TestError("Extra non-tested variables detected: {}".format(
                ", ".join(not_tested_variables)
            ))


    @classmethod
    def _get_sorting_indices(cls, cdf):

        def _get_crossover_sorting_index():
            times = cdf.raw_var("crossover_times")[:, 0]
            delta_times = cdf.raw_var("crossover_time_difference")[:]
            return cls._get_sorting_index(times, delta_times)

        def _get_plane_alignment_sorting_index():
            times = cdf.raw_var("plane_alignment_time")[:]
            if times.ndim == 2:
                times = times[:, 0]
            return cls._get_sorting_index(times)

        return {
            "crossover_": _get_crossover_sorting_index(),
            "plane_alignment_": _get_plane_alignment_sorting_index(),
        }

    @classmethod
    def _get_spacecraft_translator(cls, spacecraft_mapping):
        dtype = "S3" # 3 character ASCII
        convert = numpy.vectorize(
            lambda idx: spacecraft_mapping[idx], otypes=[dtype]
        )
        def _translate_spacecraft(data):
            return convert(data).astype(dtype), CDF_CHAR
        return _translate_spacecraft

    @classmethod
    def _expand_variable(cls, cdf_dst, cdf_src, variables_dst, variable_src,
                         type_dst=None, convert_data=None, index=Ellipsis):
        var_src = cdf_src.raw_var(variable_src)

        if type_dst is None:
            type_dst = var_src.type()

        for idx, variable_dst in enumerate(variables_dst):
            attributes = dict(var_src.attrs)
            if variable_dst in cls.VARIABLE_DESCRIPTION:
                attributes["DESCRIPTION"] = cls.VARIABLE_DESCRIPTION[variable_dst]
            data = var_src[:, idx, ...]
            if convert_data:
                data, type_dst = convert_data(data)

            cls._save_cdf_variable(
                cdf_dst, variable_dst, type_dst, data[index], attributes
            )

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

    @classmethod
    def _extrat_spacecraft_mapping(cls, cdf_src):

        def _parse_line(line):
            match = cls.RE_SC_MAPPING_PATTERN.match(line)
            try:
                record = match.groupdict()
                return (
                    int(record["index"]),
                    cls.SPACECRAFT_MAPPING[
                        (record["mission"], record["spacecraft"])
                    ]
                )
            except (AttributeError, ValueError, KeyError) as error:
                raise ValueError(
                    f"Failed to parse spacecraft mapping from {line!r}!"
                ) from error

        return dict(_parse_line(line) for line in cdf_src.attrs["INFO"])

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
    def _reverse_sorting_index(cls, index):
        """ Get index mapping sorted array to its unsorted original. """
        return cls._get_sorting_index(index)

    @staticmethod
    def _get_sorting_index(*columns):
        """ Get index sorting an array by multiple columns. """
        argsort_options = {"axis": 0, "kind": "stable"}
        if not columns:
            return Ellipsis
        columns = list(reversed(columns))
        column = columns[0]
        index = numpy.argsort(column, **argsort_options)
        for column in columns[1:]:
            index = index[numpy.argsort(column[index], **argsort_options)]
        return index


if __name__ == "__main__":
    App.run(*sys.argv)
