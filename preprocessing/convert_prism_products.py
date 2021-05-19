#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Convert PRISM (MITx_LP, MITxTEC and PPIxFAC) products to a simple time-series
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

import re
import sys
from logging import getLogger
from datetime import datetime
from os import rename, remove
from os.path import basename, exists
from numpy import asarray, argsort, arange
from numpy.lib.stride_tricks import as_strided
from common import (
    setup_logging, cdf_open, CommandError,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
    CDF_UINT1, CDF_UINT4, CDF_EPOCH,
)

LOGGER = getLogger(__name__)

VERSION = "1.0.0"
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
CONVERT_FUNCTION = {}

CDF_CREATOR = "EOX:convert_prism_products-%s [%s-%s, libcdf-%s]" % (
    VERSION, SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION
)

# save variables
COMMON_PARAM = dict(
    compress=GZIP_COMPRESSION,
    compress_param=GZIP_COMPRESSION_LEVEL4
)

PQ_NOT_DEFINED = -2 # Position_Quality flag - position not defined


CDF_VARIABLE_ATTRIBUTES = {
    "SourceRowIndex_ID": {
        "DESCRIPTION": "Mapping to the original product rows.",
        "UNITS": " ",
        "FORMAT": "I6",
    },
    "SourceColIndex_ID": {
        "DESCRIPTION": "Mapping to the original product columns.",
        "UNITS": " ",
        "FORMAT": "I1",
    },
}

CDF_POINT_TYPE_ATTRIBUTES = {
    "MITx_LP_2F": {
        "DESCRIPTION": (
            "Point type: "
            "0 - LP MIT equatorward edge of the equatorward wall, "
            "1 - LP MIT poleward edge of the equatorward wall, "
            "2 - LP MIT equatorward edge of poleward wall, "
            "3 - LP MIT poleward edge of the poleward boundary, "
            "4 - LP SETE equatorward bounding position, "
            "5 - LP SETE poleward bounding position, "
            "6 - LP Te peak position."
        ),
        "UNITS": " ",
        "FORMAT": "Z01",
    },
    "MITxTEC_2F": {
        "DESCRIPTION": (
            "Point type: "
            "0 - LP MIT equatorward edge of the equatorward wall, "
            "1 - LP MIT poleward edge of the equatorward wall, "
            "2 - LP MIT equatorward edge of poleward wall, "
            "3 - LP MIT poleward edge of the poleward boundary, "
        ),
        "UNITS": " ",
        "FORMAT": "Z01",
    },
    "PPIxFAC_2F": {
        "DESCRIPTION": (
            "Point type: "
            "0 - Equatorward edge of SSFAC boundary, "
            "1 - Poleward edge of SSFAC boundary."
        ),
        "UNITS": " ",
        "FORMAT": "Z01",
    },
}


class ConversionSkipped(Exception):
    """ Exception raised when the processing is skipped."""


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print("USAGE: %s <input> [<output>]" % basename(exename), file=file)
    print("\n".join([
        "DESCRIPTION:",
        "  Convert MITx_LP, MITxTEC and PPIxFAC (PRISM project) products to a "
        "simple time-series.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """
    argv = argv + [None]
    try:
        input_ = argv[1]
        output = argv[2]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return input_, output


def main(filename_input, filename_output=None):
    """ main subroutine """
    if filename_output is None:
        filename_output = filename_input

    filename_tmp = filename_output + ".tmp.cdf"

    if exists(filename_tmp):
        remove(filename_tmp)

    try:
        convert_prism_products(filename_input, filename_tmp)
        LOGGER.info("%s -> %s", filename_input, filename_output)
        rename(filename_tmp, filename_output)
    except ConversionSkipped as exc:
        LOGGER.warning("%s skipped - %s", filename_input, exc)
    finally:
        if exists(filename_tmp):
            remove(filename_tmp)


def convert_prism_products(filename_input, filename_output):
    """ Convert MITx_LP, MITxTEC and PPIxFAC products. """

    def _get_product_type(file_type, file_name):
        for product_type, (type_filter, name_filter) in PRODUCT_TYPES.items():
            if type_filter.match(file_type) and name_filter.match(file_name):
                if file_type.endswith(":VirES"):
                    raise ConversionSkipped("already converted product")
                return product_type
        raise ConversionSkipped("not a supported product")

    with cdf_open(filename_input) as cdf_src:
        product_type = _get_product_type(
            str(cdf_src.attrs.get("File_Type", "")),
            str(cdf_src.attrs.get("File_Name", "")),
        )
        with cdf_open(filename_output, "w") as cdf_dst:
            CONVERT_FUNCTION[product_type](cdf_dst, cdf_src)


def convert_mit_lp(cdf_dst, cdf_src):
    """ Convert MITx_LP_2F product. """
    _copy_attributes(cdf_dst, cdf_src)
    _update_creator(cdf_dst)
    _set_file_type(cdf_dst)
    _copy_variables(cdf_dst, cdf_src, variables=[
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
    ])
    index, row_mapping, col_mapping = _get_unpacked_index(cdf_src)
    _copy_packed_variables(cdf_dst, cdf_src, index=index, variables=[
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
    ])
    _save_point_type(cdf_dst, col_mapping, point_types=[
        0b000, # LP MIT equatorward edge of the equatorward wall
        0b001, # LP MIT poleward edge of the equatorward wall
        0b010, # LP MIT equatorward edge of poleward wall
        0b011, # LP MIT poleward edge of the poleward boundary
        0b100, # LP SETE equatorward bounding position
        0b101, # LP SETE poleward bounding position
        0b110, # LP Te peak position
    ], product_type="MITxTEC_2F")
    _save_row_col_mapping(cdf_dst, row_mapping, col_mapping)
    _add_time_extent_attribute(cdf_dst, ["Timestamp", "Timestamp_ID"])

CONVERT_FUNCTION["MITx_LP_2F"] = convert_mit_lp


def convert_mit_tec(cdf_dst, cdf_src):
    """ Convert MITxTEC_2F product. """
    _copy_attributes(cdf_dst, cdf_src)
    _update_creator(cdf_dst)
    _set_file_type(cdf_dst)
    _copy_variables(cdf_dst, cdf_src, variables=[
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
    ])
    index, row_mapping, col_mapping = _get_unpacked_index(cdf_src)
    _copy_packed_variables(cdf_dst, cdf_src, index=index, variables=[
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
    ])
    _save_point_type(cdf_dst, col_mapping, point_types=[
        0b000, # TEC MIT equatorward edge of the equatorward wall
        0b001, # TEC MIT poleward edge of the equatorward wall
        0b010, # TEC MIT equatorward edge of poleward wall
        0b011, # TEC MIT poleward edge of the poleward boundary
    ], product_type="MITxTEC_2F")
    _save_row_col_mapping(cdf_dst, row_mapping, col_mapping)
    _add_time_extent_attribute(cdf_dst, ["Timestamp", "Timestamp_ID"])

CONVERT_FUNCTION["MITxTEC_2F"] = convert_mit_tec


def convert_ppi_fac(cdf_dst, cdf_src):
    """ Convert PPIxFAC_2F product. """
    _copy_attributes(cdf_dst, cdf_src)
    _update_creator(cdf_dst)
    _set_file_type(cdf_dst)
    _copy_variables(cdf_dst, cdf_src, variables=[
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
    ])
    index, row_mapping, col_mapping = _get_unpacked_index(cdf_src)
    _copy_packed_variables(cdf_dst, cdf_src, index=index, variables=[
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
    ])
    _save_point_type(cdf_dst, col_mapping, point_types=[
        0b000, # Equatorward edge of SSFAC boundary
        0b001, # Poleward edge of SSFAC boundary
    ], product_type="PPIxFAC_2F")
    _save_row_col_mapping(cdf_dst, row_mapping, col_mapping)
    _add_time_extent_attribute(cdf_dst, ["Timestamp", "Timestamp_ID"])

CONVERT_FUNCTION["PPIxFAC_2F"] = convert_ppi_fac


def _add_time_extent_attribute(cdf, time_variables):
    min_time, max_time = None, None
    for time_variable in time_variables:
        times = cdf.raw_var(time_variable)[...]
        try:
            min_time = (
                times.min() if min_time is None else min(min_time, times.min())
            )
            max_time = (
                times.max() if max_time is None else max(max_time, times.max())
            )
        except ValueError:
            pass # ignore the empty time-array

    if min_time is not None or max_time is not None:
        attr_name = "TIME_EXTENT"
        cdf.attrs.new(attr_name)
        cdf.attrs[attr_name].new(
            data=[min_time, max_time],
            type=CDF_EPOCH,
            number=0,
        )

def _save_row_col_mapping(cdf_dst, row_mapping, col_mapping):
    _save_variable(
        cdf_dst, "SourceRowIndex_ID", CDF_UINT4, row_mapping,
        CDF_VARIABLE_ATTRIBUTES["SourceRowIndex_ID"],
    )
    _save_variable(
        cdf_dst, "SourceColIndex_ID", CDF_UINT1, col_mapping,
        CDF_VARIABLE_ATTRIBUTES["SourceColIndex_ID"],
    )


def _save_point_type(cdf_dst, col_mapping, point_types, product_type):
    _save_variable(
        cdf_dst, "PointType_ID", CDF_UINT1, asarray(point_types)[col_mapping],
        CDF_POINT_TYPE_ATTRIBUTES[product_type]
    )


def _get_unpacked_index(cdf_src):
    nrow, ncol = cdf_src.raw_var("Timestamp_ID").shape
    times = cdf_src.raw_var("Timestamp_ID")[...].flatten()
    quality = cdf_src.raw_var("Position_Quality_ID")[...].flatten()
    row_mapping, col_mapping = _get_row_col_mapping(nrow, ncol)
    index = argsort(times)
    index = index[quality[index] != PQ_NOT_DEFINED]
    return index, row_mapping[index], col_mapping[index]


def _get_row_col_mapping(nrow, ncol):
    rows, cols = arange(nrow), arange(ncol)
    return (
        as_strided(
            rows, (nrow, ncol), rows.strides + (0,), writeable=False
        ).flatten(),
        as_strided(
            cols, (nrow, ncol), (0,) + cols.strides, writeable=False
        ).flatten(),
    )


def _copy_variables(cdf_dst, cdf_src, variables):
    for variable in variables:
        _copy_variable(cdf_dst, cdf_src, variable)


def _copy_variable(cdf_dst, cdf_src, variable):
    raw_var = cdf_src.raw_var(variable)
    _save_variable(
        cdf_dst, variable, raw_var.type(), raw_var[...], raw_var.attrs,
    )


def _copy_packed_variables(cdf_dst, cdf_src, variables, index):
    for variable in variables:
        _copy_packed_variable(cdf_dst, cdf_src, variable, index)


def _copy_packed_variable(cdf_dst, cdf_src, variable, index):
    raw_var = cdf_src.raw_var(variable)
    _save_variable(
        cdf_dst, variable, raw_var.type(),
        raw_var[...].flatten()[index], raw_var.attrs,
    )


def _save_variable(cdf, variable, cdf_type, data, attrs):
    cdf.new(
        variable, data, cdf_type, dims=data.shape[1:], **COMMON_PARAM,
    )
    cdf[variable].attrs.update(attrs)


def _set_file_type(cdf_dst):
    cdf_dst.attrs["File_Type"] = (
        str(cdf_dst.attrs.get("File_Type", "")) or
        basename(str(cdf_dst.attrs["File_Name"]))[8:18]
    ) + ":VirES"


def _update_creator(cdf):
    for key in ["Creator", "Creation_Date"]:
        if key in cdf.attrs:
            del cdf.attrs[key]

    cdf.attrs.update({
        "CREATOR": CDF_CREATOR,
        "CREATED": (
            datetime.utcnow().replace(microsecond=0)
        ).isoformat() + "Z",
    })


def _copy_attributes(cdf_dst, cdf_src):
    cdf_dst.attrs.update(cdf_src.attrs)


if __name__ == "__main__":
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)
        usage(sys.argv[0])
