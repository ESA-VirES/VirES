#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Text converted AEJxPBL and AEJxPBS products with the original file.
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
from numpy import full, nan
from numpy.testing import assert_equal
from common import (
    setup_logging, CommandError, CDF_TYPE_LABEL, CDF_EPOCH, cdf_open
)
from compare_cdf import compare_attributes
LOGGER = getLogger(__name__)


PRODUCT_TYPES = {
    "AEJxPBL_2F": re.compile("^SW_OPER_AEJ[ABC]PBL_2F_"),
    "AEJxPBS_2F": re.compile("^SW_OPER_AEJ[ABC]PBS_2F_"),
}

# point types - bit flags
#
#  bit   | False (0)           | True (1)       | Note
#  -----------------------------------------------------------
#  bit 0 | WEJ                 | EEJ            |
#  bit 1 | Peak                | Boundary       |
#  bit 2 | Equatorial boundary | Polar boundary | if bit 1 set
#  bit 3 | Segment start       | Segment end    | if bit 1 set
#

PEAK_MIN = 0x0         # 0000 WEJ Peak - Minimum of J (WEJ)
PEAK_MAX = 0x1         # 0001 EEJ Peak - Maximum of J (EEJ
WEJ_EB = 0x2           # 0010 WEJ Equatorial Boundary 0 (WEJ)
EEJ_EB = 0x3           # 0011 EEJ Equatorial Boundary 1 (EEJ)
WEJ_PB = 0x6           # 0110 WEJ Polar Boundary 0 (WEJ)
EEJ_PB = 0x7           # 0111 EEJ Polar Boundary 1 (EEJ)
EJ_TYPE_MASK = 0x1     # 0001
BOUNDARY_MASK = 0x2    # 0010
SEGMENT_END_MASK = 0x8 # 1000 segment end bit mask

POINT_TYPE = {
    PEAK_MIN: "PEAK_MIN",
    PEAK_MAX: "PEAK_MAX",
    WEJ_EB: "WEJ_EB",
    EEJ_EB: "EEJ_EB",
    WEJ_PB: "WEJ_PB",
    EEJ_PB: "EEJ_PB",
}

def detect_product_type(product_name):
    """ Detect product type from the given product name. """
    for product_type, pattern in PRODUCT_TYPES.items():
        if pattern.match(product_name):
            return product_type
    return None


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <source-CDF> <converted-CDF>" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Test a converted AEJxLP*_2F product against its source.",
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
    result = test_converted_aej_pb(filename_source, filename_tested)
    if result:
        LOGGER.error("%s failed the test!", filename_tested)
    else:
        LOGGER.info("%s is correct.", filename_tested)


def test_converted_aej_pb(filename_source, filename_tested):
    """ Test converted AEJxPB(L|S)_2F product. """
    with cdf_open(filename_source) as cdf_src:
        source_product_type = detect_product_type(
            basename(str(cdf_src.attrs.get("File_Name", "")))
        )
        if source_product_type not in PRODUCT_TYPES:
            LOGGER.error("The reference file is not a AEJxPB*_2F product!")
            return True

        with cdf_open(filename_tested) as cdf_dst:
            product_type = detect_product_type(
                basename(str(cdf_dst.attrs.get("File_Name", "")))
            )
            if product_type not in PRODUCT_TYPES:
                LOGGER.error("The tested file is not a AEJxPB*_2F product!")
                return True

            if source_product_type != product_type:
                LOGGER.error(
                    "The reference and tested file are not of the same product "
                    "type! %s != %s", source_product_type, product_type
                )
                return True

            return PRODUCT_TEST[product_type](cdf_src, cdf_dst)

def test_converted_aej_pbl(cdf_src, cdf_dst):
    """ Test converted AEJxPBS_2F product. """

    # test peaks and boundaries
    error_count = _test_converted_aej_pbl_common(
        cdf_src, cdf_dst, 'J', 'J_QD'
    )

    return error_count > 0

def test_converted_aej_pbs(cdf_src, cdf_dst):
    """ Test converted AEJxPBL_2F product. """

    # test peaks and boundaries
    error_count = _test_converted_aej_pbl_common(
        cdf_src, cdf_dst, 'J_DF', 'J_DF_SemiQD'
    )

    # test ground magnetic disturbances
    error_count += _compare_variable_b_set(
        cdf_src, cdf_dst, "ground magnetic disturbance",
        variables=[
            ('t_Peak', 'Timestamp_B'),
            ('Latitude_B', 'Latitude_B'),
            ('Longitude_B', 'Longitude_B'),
            ('B', 'B'),
        ],
        row_index_variable="SourceRowIndex_B",
        col_index_variable="SourceColIndex_B",
    )

    return error_count > 0


def _test_converted_aej_pbl_common(cdf_src, cdf_dst, j_var_src, j_var_dst):
    """ Test converted AEJxPBL_2F product. """
    error_count = 0

    error_count += compare_attributes(
        cdf_src.attrs, cdf_dst.attrs,
        excluded=['Creator', 'File_Type']
    )

    error_count += _compare_file_type(cdf_src, cdf_dst)

    flags_variable = 'Flags'
    error_count += _compare_data_types(
        flags_variable,
        cdf_src[flags_variable].type(),
        cdf_dst[flags_variable].type(),
    )

    point_types = cdf_dst['PointType'][...]

    # peaks
    error_count += _compare_variable_set(
        cdf_src, cdf_dst,
        label='Peak',
        mask_dst=(point_types & 0x6 == 0x0),
        point_types=point_types,
        variables=[
            ('t_Peak', 'Timestamp'),
            ('Latitude_Peak', 'Latitude'),
            ('Longitude_Peak', 'Longitude'),
            ('Latitude_Peak_QD', 'Latitude_QD'),
            ('Longitude_Peak_QD', 'Longitude_QD'),
            ('MLT_Peak', 'MLT'),
            (j_var_src, j_var_dst),
        ],
        flags_variable=flags_variable,
        index_variable="SourceIndex",
    )

    # equatorial boundaries
    error_count += _compare_variable_set(
        cdf_src, cdf_dst,
        label='EB',
        mask_dst=(point_types & 0x6 == 0x2),
        point_types=point_types,
        variables=[
            ('t_EB', 'Timestamp'),
            ('Latitude_EB', 'Latitude'),
            ('Longitude_EB', 'Longitude'),
            ('Latitude_EB_QD', 'Latitude_QD'),
            ('Longitude_EB_QD', 'Longitude_QD'),
            ('MLT_EB', 'MLT'),
            (None, j_var_dst),
        ],
        flags_variable=flags_variable,
        index_variable="SourceIndex",
    )

    # polar boundaries
    error_count += _compare_variable_set(
        cdf_src, cdf_dst,
        label='PB',
        mask_dst=(point_types & 0x6 == 0x6),
        point_types=point_types,
        variables=[
            ('t_PB', 'Timestamp'),
            ('Latitude_PB', 'Latitude'),
            ('Longitude_PB', 'Longitude'),
            ('Latitude_PB_QD', 'Latitude_QD'),
            ('Longitude_PB_QD', 'Longitude_QD'),
            ('MLT_PB', 'MLT'),
            (None, j_var_dst),
        ],
        flags_variable=flags_variable,
        index_variable="SourceIndex",
    )

    return error_count


PRODUCT_TEST = {
    "AEJxPBL_2F": test_converted_aej_pbl,
    "AEJxPBS_2F": test_converted_aej_pbs,
}


def _compare_variable_set(cdf_src, cdf_dst, mask_dst, point_types, variables,
                          label, flags_variable, index_variable):
    error_count = 0

    # WEJ and EEJ columns masks
    mask_wej = point_types[mask_dst] & 0x1 == 0x0 # WEJ values
    mask_eej = point_types[mask_dst] & 0x1 == 0x1 # EEJ values

    # index mapping from the source to the converted records
    index_src = cdf_dst.raw_var(index_variable)[...][mask_dst]
    index_src_wej = index_src[mask_wej]
    index_src_eej = index_src[mask_eej]

    flags_src = cdf_src.raw_var(flags_variable)[...]
    flags_dst = cdf_dst.raw_var(flags_variable)[...][mask_dst]

    # mask of the missing source values - must be invalid points
    mask_missing_wej = full(flags_src.shape, True)
    mask_missing_wej[index_src_wej] = False
    mask_missing_eej = full(flags_src.shape, True)
    mask_missing_eej[index_src_eej] = False

    nans = full((flags_src.size, 2), nan)

    if not arrays_equal(flags_src[index_src_wej], flags_dst[mask_wej]):
        LOGGER.error("%s@%s WEJ values differ!", flags_variable, label)
        error_count += 1

    if not arrays_equal(flags_src[index_src_eej], flags_dst[mask_eej]):
        LOGGER.error("%s@%s EEJ values differ!", flags_variable, label)
        error_count += 1

    for variable_src, variable_dst in variables:
        # compare variable values

        label = (
            "%s/%s" % (variable_src, variable_dst) if variable_src else
            "%s@%s" % (variable_dst, label)
        )

        if variable_src:
            error_count += _compare_data_types(
                label,
                cdf_src[variable_src].type(),
                cdf_dst[variable_dst].type(),
            )

        data_src = cdf_src.raw_var(variable_src)[...] if variable_src else nans
        data_dst = cdf_dst.raw_var(variable_dst)[...][mask_dst]

        if not arrays_equal(data_src[index_src_wej, 0], data_dst[mask_wej]):
            LOGGER.error("%s WEJ values differ!", label)
            error_count += 1

        if not arrays_equal(data_src[index_src_eej, 1], data_dst[mask_eej]):
            LOGGER.error("%s EEJ values differ!", label)
            error_count += 1

        if variable_src and cdf_src.raw_var(variable_src).type() != CDF_EPOCH:
            # Only NaN-filled source records can be excluded from the converted
            # product. The rejected records must not contain valid values.
            _src = data_src[mask_missing_wej, 0]
            _nan = nans[mask_missing_wej, 0]
            if not arrays_equal(_src, _nan):
                LOGGER.error("Missing valid %s WEJ values!", variable_src)
                error_count += 1

            _src = data_src[mask_missing_eej, 1]
            _nan = nans[mask_missing_wej, 0]
            if not arrays_equal(_src, _nan):
                LOGGER.error("Missing valid %s EEJ values!", variable_src)
                error_count += 1

    return error_count


def _compare_variable_b_set(cdf_src, cdf_dst, label, variables,
                            row_index_variable, col_index_variable):
    error_count = 0

    # index mapping from the source to the converted records
    row_index_src = cdf_dst.raw_var(row_index_variable)[...]
    col_index_src = cdf_dst.raw_var(col_index_variable)[...]

    col_mask = (col_index_src == 0)

    for variable_src, variable_dst in variables:
        # compare variable values
        data_src = cdf_src.raw_var(variable_src)[...]
        data_dst = cdf_dst.raw_var(variable_dst)[...]

        data_equal = (
            arrays_equal(
                data_src[row_index_src[col_mask], 0], data_dst[col_mask]
            )
            and arrays_equal(
                data_src[row_index_src[~col_mask], 1], data_dst[~col_mask]
            )
        )

        if not data_equal:
            LOGGER.error(
                "%s/%s %s values differ!", variable_src, variable_dst, label
            )
            error_count += 1

    return error_count


def _compare_file_type(cdf_src, cdf_dst, file_type_variable='File_Type',
                       file_name_variable='File_Name'):
    ft_src = '%s:VirES' % (
        cdf_src.attrs[file_type_variable][0]
        if file_type_variable in cdf_src.attrs else
        basename(str(cdf_src.attrs[file_name_variable][0]))[8:18]
    )
    ft_dst = cdf_dst.attrs[file_type_variable][0]
    if ft_src != ft_dst:
        LOGGER.error("Incorrect file type! %s != %s", ft_src, ft_dst)
        return 1
    return 0


def _compare_data_types(label, cdf_type_src, cdf_type_dst):
    if cdf_type_src != cdf_type_dst:
        LOGGER.error(
            "%s data-types mismatch! %s != %s", label,
            CDF_TYPE_LABEL[cdf_type_src], CDF_TYPE_LABEL[cdf_type_dst]
        )
        return 1
    return 0


def arrays_equal(data_src, data_dst):
    """ Compare two arrays and return True is they are equal. """
    try:
        assert_equal(data_src, data_dst)
    except AssertionError as error:
        print(error)
        return False
    return True


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
