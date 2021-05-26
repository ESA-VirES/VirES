#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Test converted PRISM (MITx_LP, MITxTEC and PPIxFAC) products against
# the original.
#
# Author: Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
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

import sys
import re
from logging import getLogger
from os.path import basename
from numpy import isnan, inf, zeros, empty, asarray
from numpy.testing import assert_equal
from common import (
    setup_logging, CommandError, CDF_TYPE_LABEL, cdf_open
)
from compare_cdf import compare_attributes, compare_variable

LOGGER = getLogger(__name__)

PQ_NOT_DEFINED = -2 # Position_Quality flag - position not defined

PRODUCT_TYPES = {
    "MITx_LP_2F": (
        re.compile("^MIT[ABC]_LP_2F"), re.compile("^SW_OPER_MIT[ABC]_LP_2F_"),
    ),
    "MITxTEC_2F": (
        re.compile("^MIT[ABC]TEC_2F"), re.compile("^SW_OPER_MIT[ABC]TEC_2F_"),
    ),
    "PPIxFAC_2F": (
        re.compile("^PPI[ABC]FAC_2F"), re.compile("^SW_OPER_PPI[ABC]FAC_2F_"),
    ),
}
TEST_FUNCTION = {}


class TestError(Exception):
    """ Test error exception. """


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <source-CDF> <converted-CDF>" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Test a converted MITx_LP, MITxTEC or PPIxFAC product against its "
        "source.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    try:
        source = argv[1]
        tested = argv[2]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return source, tested


def main(filename_source, filename_tested):
    """ main subroutine """
    LOGGER.info("Comparing %s to %s ...", filename_tested, filename_source)
    result = test_converted_prism_product(filename_source, filename_tested)
    if result:
        LOGGER.error("%s failed the test!", filename_tested)
    else:
        LOGGER.info("%s is correct.", filename_tested)


def test_converted_prism_product(filename_source, filename_tested):
    """ Test converted MITx_LP, MITxTEC or PPIxFAC product. """

    def _get_product_type(file_type, file_name):
        for product_type, (type_filter, name_filter) in PRODUCT_TYPES.items():
            if type_filter.match(file_type) and name_filter.match(file_name):
                return product_type, file_type.endswith(":VirES")
        return None

    with cdf_open(filename_source) as cdf_src:
        source_product_type, is_converted = _get_product_type(
            str(cdf_src.attrs.get("File_Type", "")),
            str(cdf_src.attrs.get("File_Name", "")),
        )
        if source_product_type not in PRODUCT_TYPES or is_converted:
            LOGGER.error("The reference file is not a supported source product!")
            return True

        with cdf_open(filename_tested) as cdf_dst:
            product_type, is_converted = _get_product_type(
                str(cdf_dst.attrs.get("File_Type", "")),
                str(cdf_dst.attrs.get("File_Name", "")),
            )
            if product_type not in PRODUCT_TYPES or not is_converted:
                LOGGER.error("The tested file is not a supported converted product!")
                return True

            if source_product_type != product_type:
                LOGGER.error(
                    "The reference and tested file are not of the same product "
                    "type! %s != %s", source_product_type, product_type
                )
                return True

            return TEST_FUNCTION[product_type](cdf_src, cdf_dst)


def test_converted_mit_lp(cdf_src, cdf_dst):
    """ Test converted  MITx_LP_2F product. """
    error_count = 0
    error_count += compare_attributes(
        cdf_src.attrs, cdf_dst.attrs,
        excluded=['Creator', 'File_Type'],
    )
    error_count += _compare_file_type(cdf_src, cdf_dst)
    error_count += _compare_variables(
        cdf_dst,
        cdf_src,
        variables=[
            "Timestamp",
            "Counter",
            "Latitude",
            "Longitude",
            "Radius",
            "Latitude_QD",
            "Longitude_QD",
            "MLT",
            "L_value",
            "SZA",
            "Ne",
            "Te",
            "Depth",
            "DR",
            "Width",
            "dL",
            "EW_Gradient",
            "PW_Gradient",
            "Quality",
        ]
    )
    try:
        mask_src, row_index, col_index = _load_masks(cdf_src, cdf_dst)
    except TestError:
        error_count += 1
        return error_count
    error_count += _compare_packed_variables(
        cdf_src, cdf_dst, mask_src, row_index, col_index,
        variables=[
            "Timestamp_ID",
            "Latitude_ID",
            "Longitude_ID",
            "Radius_ID",
            "Latitude_QD_ID",
            "Longitude_QD_ID",
            "MLT_ID",
            "L_value_ID",
            "SZA_ID",
            "Ne_ID",
            "Te_ID",
            "Position_Quality_ID",
        ]
    )
    error_count += _compare_mapped_variables(
        cdf_dst, row_index, variables={
            "Counter_ID": "Counter",
        }
    )
    error_count += _check_point_type(
        cdf_dst, col_index, "PointType_ID",
        point_types=[
            0b000, # LP MIT equatorward edge of the equatorward wall
            0b001, # LP MIT poleward edge of the equatorward wall
            0b010, # LP MIT equatorward edge of poleward wall
            0b011, # LP MIT poleward edge of the poleward boundary
            0b100, # LP SETE equatorward bounding position
            0b101, # LP SETE poleward bounding position
            0b110, # LP Te peak position
        ]
    )
    error_count += _check_time_extent(cdf_src, cdf_dst, mask_src)
    return error_count

TEST_FUNCTION["MITx_LP_2F"] = test_converted_mit_lp


def test_converted_mit_tec(cdf_src, cdf_dst):
    """ Test converted  MITxTEC_2F product. """
    error_count = 0
    error_count += compare_attributes(
        cdf_src.attrs, cdf_dst.attrs,
        excluded=['Creator', 'File_Type'],
    )
    error_count += _compare_file_type(cdf_src, cdf_dst)
    error_count += _compare_variables(
        cdf_dst,
        cdf_src,
        variables=[
            "Timestamp",
            "Counter",
            "Latitude",
            "Longitude",
            "Radius",
            "Latitude_QD",
            "Longitude_QD",
            "MLT",
            "L_value",
            "SZA",
            "TEC",
            "Depth",
            "DR",
            "Width",
            "dL",
            "EW_Gradient",
            "PW_Gradient",
            "Quality",
        ]
    )
    try:
        mask_src, row_index, col_index = _load_masks(cdf_src, cdf_dst)
    except TestError:
        error_count += 1
        return error_count
    error_count += _compare_packed_variables(
        cdf_src, cdf_dst, mask_src, row_index, col_index,
        variables=[
            "Timestamp_ID",
            "Latitude_ID",
            "Longitude_ID",
            "Radius_ID",
            "Latitude_QD_ID",
            "Longitude_QD_ID",
            "MLT_ID",
            "L_value_ID",
            "SZA_ID",
            "TEC_ID",
            "Position_Quality_ID",
        ]
    )
    error_count += _compare_mapped_variables(
        cdf_dst, row_index, variables={
            "Counter_ID": "Counter",
        }
    )
    error_count += _check_point_type(
        cdf_dst, col_index, "PointType_ID",
        point_types=[
            0b000, # LP MIT equatorward edge of the equatorward wall
            0b001, # LP MIT poleward edge of the equatorward wall
            0b010, # LP MIT equatorward edge of poleward wall
            0b011, # LP MIT poleward edge of the poleward boundary
        ]
    )
    error_count += _check_time_extent(cdf_src, cdf_dst, mask_src)
    return error_count

TEST_FUNCTION["MITxTEC_2F"] = test_converted_mit_tec


def test_converted_ppi_fac(cdf_src, cdf_dst):
    """ Test converted PPIxFAC_2F product. """
    error_count = 0
    error_count += compare_attributes(
        cdf_src.attrs, cdf_dst.attrs,
        excluded=['Creator', 'File_Type'],
    )
    error_count += _compare_file_type(cdf_src, cdf_dst)
    error_count += _compare_variables(
        cdf_dst,
        cdf_src,
        variables=[
            "Timestamp",
            "Counter",
            "Latitude",
            "Longitude",
            "Radius",
            "Latitude_QD",
            "Longitude_QD",
            "MLT",
            "L_value",
            "SZA",
            "Sigma",
            "PPI",
            "dL",
            "Quality",
        ]
    )
    try:
        mask_src, row_index, col_index = _load_masks(cdf_src, cdf_dst)
    except TestError:
        error_count += 1
        return error_count
    error_count += _compare_packed_variables(
        cdf_src, cdf_dst, mask_src, row_index, col_index,
        variables=[
            "Timestamp_ID",
            "Latitude_ID",
            "Longitude_ID",
            "Radius_ID",
            "Latitude_QD_ID",
            "Longitude_QD_ID",
            "MLT_ID",
            "L_value_ID",
            "SZA_ID",
            "Position_Quality_ID",
        ]
    )
    error_count += _compare_mapped_variables(
        cdf_dst, row_index, variables={
            "Counter_ID": "Counter",
        }
    )
    error_count += _check_point_type(
        cdf_dst, col_index, "PointType_ID",
        point_types=[
            0b000, # Equatorward edge of SSFAC boundary
            0b001, # Poleward edge of SSFAC boundary
        ]
    )
    error_count += _check_time_extent(cdf_src, cdf_dst, mask_src)
    return error_count

TEST_FUNCTION["PPIxFAC_2F"] = test_converted_ppi_fac


def _load_masks(cdf_src, cdf_dst):

    # extract reference data mask
    try:
        # NOTE: the Position_Quality_ID is not reliable to filter out invalid records
        #mask_src = cdf_src.raw_var("Position_Quality_ID")[...] != PQ_NOT_DEFINED
        mask_src = ~(
            isnan(cdf_src.raw_var("Latitude_ID")[...]) |
            isnan(cdf_src.raw_var("Longitude_ID")[...]) |
            isnan(cdf_src.raw_var("Radius_ID")[...])
        )
    except KeyError as variable:
        LOGGER.error("Missing %s source CDF variable!", variable)
        raise TestError

    # extract tested data mask
    try:
        row_index = cdf_dst.raw_var("SourceRowIndex_ID")[...]
        col_index = cdf_dst.raw_var("SourceColIndex_ID")[...]
    except KeyError as variable:
        LOGGER.error("Missing %s tested CDF variable!", variable)
        raise TestError

    if _check_data_mapping(mask_src, row_index, col_index):
        raise TestError

    return mask_src, row_index, col_index


def _compare_file_type(cdf_src, cdf_dst, file_type_attr='File_Type',
                       file_name_attr='File_Name'):
    ft_src = '%s:VirES' % (
        cdf_src.attrs[file_type_attr][0]
        if file_type_attr in cdf_src.attrs else
        basename(str(cdf_src.attrs[file_name_attr][0]))[8:18]
    )
    ft_dst = cdf_dst.attrs[file_type_attr][0]
    if ft_src != ft_dst:
        LOGGER.error("Incorrect file type! %s != %s", ft_src, ft_dst)
        return 1
    return 0


def _compare_variables(cdf_src, cdf_dst, variables):
    error_count = 0
    for variable in variables:
        if variable not in cdf_src:
            error_count += 1
            LOGGER.error("Missing %s source CDF variable!", variable)
            continue
        if variable not in cdf_dst:
            error_count += 1
            LOGGER.error("Missing %s CDF variable!", variable)
            continue
        error_count += compare_variable(
            variable, cdf_src.raw_var(variable), cdf_dst.raw_var(variable),
        )
    return error_count


def _compare_packed_variables(cdf_src, cdf_dst, mask_src, row_index, col_index,
                              variables):
    error_count = 0
    # compare variables
    for variable in variables:
        if variable not in cdf_src:
            error_count += 1
            LOGGER.error("Missing %s source CDF variable!", variable)
            continue
        if variable not in cdf_dst:
            error_count += 1
            LOGGER.error("Missing %s CDF variable!", variable)
            continue
        error_count += _compare_packed_variable(
            variable, cdf_src.raw_var(variable), cdf_dst.raw_var(variable),
            mask_src, row_index, col_index
        )
    return error_count


def _compare_mapped_variables(cdf_dst, row_index, variables):
    error_count = 0
    for variable_dst, variable_src in variables.items():
        if variable_dst not in cdf_dst:
            error_count += 1
            LOGGER.error("Missing %s CDF variable!", variable_dst)
            continue
        error_count += _compare_mapped_variable(
            variable_dst,
            cdf_dst.raw_var(variable_src),
            cdf_dst.raw_var(variable_dst),
            row_index
        )
    return error_count


def _check_time_extent(cdf_src, cdf_dst, mask_src):
    min_time, max_time = +inf, -inf
    times = cdf_src.raw_var("Timestamp")[...]
    try:
        min_time = min(min_time, times.min())
        max_time = max(max_time, times.max())
    except ValueError:
        pass
    times = cdf_src.raw_var("Timestamp_ID")[...][mask_src]
    try:
        min_time = min(min_time, times.min())
        max_time = max(max_time, times.max())
    except ValueError:
        pass

    attr_name = "TIME_EXTENT"
    if min_time <= max_time:
        try:
            attr = cdf_dst.attrs[attr_name]
        except KeyError:
            LOGGER.error("Missing %s attribute!", attr_name)
            return 1
        attr._raw = True # pylint: disable=protected-access
        try:
            assert_equal(asarray([min_time, max_time]), asarray(attr[0]))
        except AssertionError:
            LOGGER.error("Wrong %s values!", attr_name)
            return 1

    return 0


def _check_data_mapping(mask_src, row_index, col_index):
    mask_dst = zeros(mask_src.shape, 'bool')
    mask_dst[row_index, col_index] = asarray(True)
    try:
        assert_equal(mask_src, mask_dst)
    except AssertionError:
        LOGGER.error("Wrong data mapping!")
        return True
    return False


def _check_point_type(cdf_dst, col_index, name, point_types):
    try:
        var_dst = cdf_dst.raw_var(name)
    except KeyError:
        LOGGER.error("Missing %s tested CDF variable!", name)
        return 1
    data_src = asarray(point_types)[col_index]
    data_dst = var_dst[...]
    try:
        assert_equal(data_src, data_dst)
    except AssertionError:
        LOGGER.error("Wrong %s values!", name)
        return 1
    return 0


def _compare_mapped_variable(name, var_src, var_dst, row_index):

    error_count = compare_attributes(
        var_src.attrs, var_dst.attrs, "%s variable" % name
    )

    if var_src.type() != var_dst.type():
        LOGGER.error(
            "%s data type mismatch! %s != %s", name,
            CDF_TYPE_LABEL[var_src.type()], CDF_TYPE_LABEL[var_dst.type()],
        )
        return error_count + 1

    try:
        assert_equal(var_src[...][row_index], var_dst[...])
    except AssertionError:
        error_count += 1
        LOGGER.error("%s values differ!", name)

    return error_count


def _compare_packed_variable(name, var_src, var_dst, mask_src,
                             row_index, col_index):

    error_count = compare_attributes(
        var_src.attrs, var_dst.attrs, "%s variable" % name
    )

    if var_src.type() != var_dst.type():
        LOGGER.error(
            "%s data type mismatch! %s != %s", name,
            CDF_TYPE_LABEL[var_src.type()], CDF_TYPE_LABEL[var_dst.type()],
        )
        return error_count + 1

    data_src = var_src[...]

    data_dst = empty(data_src.shape, dtype=data_src.dtype)
    data_dst[row_index, col_index] = var_dst[...]

    try:
        assert_equal(data_src[mask_src], data_dst[mask_src])
    except AssertionError:
        error_count += 1
        LOGGER.error("%s values differ!", name)

    return error_count


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
