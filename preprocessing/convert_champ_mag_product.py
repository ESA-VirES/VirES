#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Convert CHAMP MAG products to a Swarm-like format.
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

import sys
import logging
import os.path
import datetime
import numpy
from common import (
    init_console_logging, CommandError, cdf_open,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
    CDF_DOUBLE, CDF_EPOCH,
)


class TestError(AssertionError):
    """ Test error exception. """


class App:
    """ The app. """
    NAME = "convert_champ_mag_product"
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
            f"USAGE: {os.path.basename(exename)} <filename> [<output dir>]|"
            "[--test <output-filename>]", file=file
        )
        print("\n".join([
            "DESCRIPTION:",
            "  Convert CHAMP MAG product to a Swarm like format.",
            "  Optional output directory can be provided.",
            "  The output file is named using the Swarm-like naming convention.",
            "  With the --test option, the program tests the existing converted",
            "  file against the source.",
        ]), file=file)

    @classmethod
    def parse_inputs(cls, argv):
        """ Parse input arguments. """

        output_dir = None
        output_filename = None
        test_only = False
        args = []

        for arg in argv[1:]:
            if arg == "--test":
                test_only = True
            else:
                args.append(arg)

        try:
            input_filename = args[0]
        except IndexError:
            raise CommandError(
                "Not enough input arguments! Missing input filename."
            ) from None

        if test_only:
            try:
                output_filename = args[1]
            except IndexError:
                raise CommandError(
                    "Not enough input arguments! Missing input filename."
                ) from None
        else:
            output_dir = args[1] if len(args) > 1 else None

        return {
            "input_filename": input_filename,
            "output_dir": output_dir,
            "tested_filename": output_filename,
        }

    @classmethod
    def main(cls, input_filename, output_dir=None, tested_filename=None):
        """ Main subroutine. """
        if not tested_filename:
            output_filename = cls.convert_champ_mag_product(
                input_filename, output_dir
            )
        else:
            output_filename = tested_filename
        cls.test_converted_champ_mag_product(input_filename, output_filename)

    @classmethod
    def convert_champ_mag_product(cls, input_filename, output_dir=None):
        """ Convert CHAMP MAG product to a Swarm-like format.
        The function return path to the produced output file.
        The output file is named using the Swarm-like naming schema.
        """
        if not output_dir:
            output_dir = os.path.dirname(input_filename)

        with cdf_open(input_filename) as input_cdf:
            product_id = ChampMagProduct.get_swarm_id(input_cdf)
            tmp_filename = os.path.join(output_dir, f"{product_id}.tmp.cdf")
            output_filename = os.path.join(output_dir, f"{product_id}.cdf")

            cls.logger.info("converting %s -> %s", input_filename, output_filename)

            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)

            try:
                with cdf_open(tmp_filename, "w") as output_cdf:
                    ChampMagProduct.convert(output_cdf, input_cdf)

                os.rename(tmp_filename, output_filename)
            except:
                if os.path.exists(tmp_filename):
                    os.remove(tmp_filename)
                raise

        return output_filename

    @classmethod
    def test_converted_champ_mag_product(cls, input_filename, output_filename):
        """ Test CHAMP MAG product converted to a Swarm-like format.
        """
        cls.logger.info("testing converted %s -> %s", input_filename, output_filename)
        with cdf_open(input_filename) as input_cdf:
            with cdf_open(output_filename) as output_cdf:
                ChampMagProduct.test_converted(output_cdf, input_cdf)


class ChampMagProduct:
    """ Conversion of original CHAMP magnetic products to Swarm-like format. """

    ID_TEMPLATE = "CH_ME_MAG_LR_3_{start:%Y%m%dT%H%M%S}_{end:%Y%m%dT%H%M%S}_0100"

    CDF_CREATOR = (
        f"EOX:{App.NAME}-{App.VERSION} [{SPACEPY_NAME}-{SPACEPY_VERSION}, "
        f"libcdf-{LIBCDF_VERSION}]"
    )

    CDF_VARIABLE_PARAMETERS = {
        "compress": GZIP_COMPRESSION,
        "compress_param": GZIP_COMPRESSION_LEVEL4
    }

    RADIUS_ATTRIBUTES = {
        "DESCRIPTION": "geocentric radius",
        "UNIT": "m",
        "FORMAT": "F13.3",
    }

    REMOVED_ALTITUDE_ATTRIBUTES = ["INFO"]

    TESTED_GLOBAL_ATTRIBUTES = [
        "PRODUCT",
        "HISTORY",
        "MJD2000",
        "EPOCH_S",
        "EPOCH_E",
        "NR_OF_RECORDS",
        "MAG_ID",
    ]

    TESTED_VARIABLE_ATTRIBUTES = [
        "VALIDMIN", "VALIDMAX", "UNIT", "FORMAT", "SYSTEM", "FILLVAL", "SAMPLE",
    ]
    TESTED_CONVERTED_RADIUS_ATTRIBUTES = [
        "VALIDMIN", "VALIDMAX",
    ]

    @classmethod
    def get_swarm_id(cls, cdf):
        """ Get new Swarm-like product ID. """
        start = cdf.attrs["EPOCH_S"][0]
        end = cdf.attrs["EPOCH_E"][0]
        return cls.ID_TEMPLATE.format(start=start, end=end)

    @classmethod
    def convert(cls, cdf_dst, cdf_src):
        """ Convert champ product to the Swarm-like format. """
        cls._set_global_attributes(cdf_dst, cdf_src)
        cls._copy_variable(cdf_dst, cdf_src, "Timestamp", "EPOCH")
        cls._copy_variable(cdf_dst, cdf_src, "Latitude", "GEO_LAT", CDF_DOUBLE)
        cls._copy_variable(cdf_dst, cdf_src, "Longitude", "GEO_LON", CDF_DOUBLE)
        cls._copy_radius_from_altitude(
            cdf_dst, cdf_src, "Radius", "GEO_ALT", CDF_DOUBLE,
        )
        cls._copy_variable(cdf_dst, cdf_src, "F", "FGM_SCAL", CDF_DOUBLE)
        cls._copy_variable(cdf_dst, cdf_src, "B_VFM", "FGM_VEC", CDF_DOUBLE)
        cls._copy_variable(cdf_dst, cdf_src, "B_NEC", "NEC_VEC", CDF_DOUBLE)
        cls._copy_variable(cdf_dst, cdf_src, "Flags_Position", "GEO_STAT")
        cls._copy_variable(cdf_dst, cdf_src, "Flags_B", "FGM_FLAGS")
        cls._copy_variable(cdf_dst, cdf_src, "Flags_q", "ASC_STAT")
        cls._copy_variable(cdf_dst, cdf_src, "Mode_q", "ASC_MODE")
        cls._copy_variable(cdf_dst, cdf_src, "q_ICRF_CRF", "ASC_QUAT", CDF_DOUBLE)

    @classmethod
    def _copy_variable(cls, cdf_dst, cdf_src, variable_dst, variable_src=None,
                       type_dst=None):
        if not variable_src:
            variable_src = variable_dst

        var_src = cdf_src.raw_var(variable_src)

        if type_dst is None:
            type_dst = var_src.type()

        attributes = dict(var_src.attrs)

        cls._save_cdf_variable(cdf_dst, variable_dst, type_dst, var_src[...], {
            "ORIGINAL_NAME": variable_src,
            "UNIT": attributes.pop("UNIT", "-"),
            "DESCRIPTION": attributes.pop("INFO", ""),
            **attributes,
        })

    @classmethod
    def _copy_radius_from_altitude(cls, cdf_dst, cdf_src, variable_dst,
                                   variable_src=None, type_dst=None):
        if not variable_src:
            variable_src = variable_dst

        var_src = cdf_src.raw_var(variable_src)

        if type_dst is None:
            type_dst = var_src.type()

        attributes = dict(var_src.attrs)
        for key in cls.REMOVED_ALTITUDE_ATTRIBUTES:
            attributes.pop(key, None)
        for key in cls.RADIUS_ATTRIBUTES:
            attributes.pop(key, None)

        ref_radius = attributes.pop("REFRADIUS")

        attributes["VALIDMIN"] = cls._altitude_km_to_radius_m(
            attributes["VALIDMIN"], ref_radius
        )
        attributes["VALIDMAX"] = cls._altitude_km_to_radius_m(
            attributes["VALIDMAX"], ref_radius
        )
        data = cls._altitude_km_to_radius_m(var_src[...], ref_radius)

        cls._save_cdf_variable(cdf_dst, variable_dst, type_dst, data, {
            "ORIGINAL_NAME": variable_src,
            **cls.RADIUS_ATTRIBUTES,
            **attributes,
        })

    @staticmethod
    def _altitude_km_to_radius_m(altitude_km, ref_radius_km):
        return 1e3 * (altitude_km + ref_radius_km)

    @classmethod
    def _save_cdf_variable(cls, cdf, variable, cdf_type, data, attrs=None):
        cdf.new(
            variable, data, cdf_type, dims=data.shape[1:],
            **cls.CDF_VARIABLE_PARAMETERS,
        )
        if attrs:
            cdf[variable].attrs.update(attrs)

    @classmethod
    def _set_global_attributes(cls, cdf_dst, cdf_src):

        # NOTE CDF.attrs.update() does not preserve time data type
        for key, (head, *tail) in cdf_src.attrs.items():
            cdf_dst.attrs.new(key, head, type=(
                CDF_EPOCH if isinstance(head, datetime.datetime) else None
            ))
            for item in tail:
                cdf_dst.attrs[key].append(item)

        cdf_dst.attrs.update({
            "TITLE": f"{cls.get_swarm_id(cdf_src)}.cdf",
            "SOURCE": os.path.basename(cdf_src.pathname),
            "CREATED": f"{datetime.datetime.utcnow():%Y-%m-%dT%H:%M:%S}Z",
            "CREATOR": cls.CDF_CREATOR,
        })

    @classmethod
    def test_converted(cls, cdf_dst, cdf_src):
        """ Test converted CHAMP ME 3 MAG product. """

        def _attrs_not_equal(dst, src):
            if isinstance(dst, (str, bytes)) or isinstance(src, (str, bytes)):
                return dst != src
            return not numpy.array_equal(dst, src, equal_nan=True)

        def _test_attribute(variable, dst_attrs, src_attrs, dst_key, src_key=None):
            if not src_key:
                src_key = dst_key
            if src_key not in src_attrs:
                return
            if dst_key not in dst_attrs:
                raise TestError(f"Missing {dst_key} attribute of {variable} variable!")
            if _attrs_not_equal(dst_attrs[dst_key], src_attrs[src_key]):
                raise TestError(f"Wrong {dst_key} attribute of {variable} variable!")

        def _test_converted_radius_attribute(variable, ref_radius, dst_attrs,
                                             src_attrs, dst_key, src_key=None):
            if not src_key:
                src_key = dst_key
            if src_key not in src_attrs:
                return
            if dst_key not in dst_attrs:
                raise TestError(f"Missing {dst_key} attribute of {variable} variable!")
            if _attrs_not_equal(
                dst_attrs[dst_key],
                cls._altitude_km_to_radius_m(src_attrs[src_key], ref_radius)
            ):
                raise TestError(f"Wrong {dst_key} attribute of {variable} variable!")

        def _test_new_radius_attribute(variable, dst_attrs, dst_key):
            if dst_key not in dst_attrs:
                raise TestError(f"Missing {dst_key} attribute of {variable} variable!")
            if _attrs_not_equal(dst_attrs[dst_key], cls.RADIUS_ATTRIBUTES[dst_key].encode("ASCII")):
                raise TestError(f"Wrong {dst_key} attribute of {variable} variable!")

        def _test_copied_variable(dst, var_dst, src, var_src):
            if not numpy.array_equal(var_dst[...], var_src[...], equal_nan=True):
                raise TestError(f"{dst} values do not match source {src} values!")
            _test_attribute(dst, var_dst.attrs, var_src.attrs, "DESCRIPTION", "INFO")
            for key in cls.TESTED_VARIABLE_ATTRIBUTES:
                _test_attribute(dst, var_dst.attrs, var_src.attrs, key)

        def _test_radius(dst, var_dst, src, var_src):
            ref_radius = var_src.attrs["REFRADIUS"]
            if not numpy.array_equal(
                var_dst[...],
                cls._altitude_km_to_radius_m(var_src[...], ref_radius),
                equal_nan=True
            ):
                raise TestError(f"{dst} values do not match source {src} values!")
            _test_new_radius_attribute(dst, var_dst.attrs, "DESCRIPTION")
            for key in cls.TESTED_VARIABLE_ATTRIBUTES:
                if key in cls.TESTED_CONVERTED_RADIUS_ATTRIBUTES:
                    _test_converted_radius_attribute(
                        dst, ref_radius, var_dst.attrs, var_src.attrs, key
                    )
                elif key in cls.RADIUS_ATTRIBUTES:
                    _test_new_radius_attribute(dst, var_dst.attrs, key)
                else:
                    _test_attribute(dst, var_dst.attrs, var_src.attrs, key)

        # test global attributes
        if [f"{cls.get_swarm_id(cdf_src)}.cdf"] != list(cdf_dst.attrs["TITLE"]):
            raise TestError("Wrong global TITLE attribute!")

        for key in cls.TESTED_GLOBAL_ATTRIBUTES:
            if key in cdf_src.attrs and key not in cdf_dst.attrs:
                raise TestError(f"Missing global {key} attribute!")
            if list(cdf_src.attrs[key]) != list(cdf_dst.attrs[key]):
                raise TestError(f"Global {key} attribute not equal!")

        # test variables
        tested_variables = set()
        for key in cdf_dst:
            var_dst = cdf_dst.raw_var(key)
            src_key = var_dst.attrs["ORIGINAL_NAME"].decode("UTF-8")
            var_src = cdf_src.raw_var(src_key)
            if key == "Radius":
                _test_radius(key, var_dst, src_key, var_src)
            else:
                _test_copied_variable(key, var_dst, src_key, var_src)
            tested_variables.add(src_key)

        for key in cdf_src:
            if key not in tested_variables:
                raise TestError(f"Missing converted {key} variable!")


if __name__ == "__main__":
    App.run(*sys.argv)
