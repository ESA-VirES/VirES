#!/usr/bin/env python3
#-------------------------------------------------------------------------------
#
# Download Kp index values from GFZ API and convert them one or more CDF files.
#
# For more details on the Kp_ap data format see
#   https://kp.gfz-potsdam.de/app/format/Kp_ap.txt
#
# Author: Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2023 EOX IT Services GmbH
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
# pylint: disable=missing-docstring, superfluous-parens, bare-except

import sys
import re
from os import rename, remove, scandir, makedirs
from os.path import dirname, basename, exists, join
from collections import namedtuple
from itertools import chain
from io import TextIOWrapper
from logging import getLogger
from urllib.request import urlopen, HTTPError
from email.utils import parsedate_to_datetime
from datetime import datetime, date, time, timedelta
from numpy import array, unique, array_equal
from common import (
    setup_logging, cdf_open, CommandError,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
    CDF_UINT1, CDF_UINT2, CDF_INT2, CDF_EPOCH, CDF_DOUBLE, CdfTypeEpoch,
)

VERSION = "1.0.0"

CDF_CREATOR = (
    f"EOX:download_kp-{VERSION} [{SPACEPY_NAME}-{SPACEPY_VERSION}, "
    f"libcdf-{LIBCDF_VERSION}]"
)

CDF_VARIABLE_PARAMETERS = {
    "compress": GZIP_COMPRESSION,
    "compress_param": GZIP_COMPRESSION_LEVEL4
}

CDF_VARIABLE_ATTRIBUTES = {
    "Timestamp": {
        "DESCRIPTION": (
            "UTC timestamp - start time of interval for which the Kp and ap"
            " values are given"
        ),
        "UNITS": "-",
        "FORMAT": " ",
    },
    "Interval": {
        "DESCRIPTION": (
            "Duration of interval in seconds for which the Kp and ap values "
            "are given"
        ),
        "UNITS": "s",
        "FORMAT": "I5",
    },
    "Kp": {
        "DESCRIPTION": (
            "Planetary three-hour index Kp for the interval"
        ),
        "UNITS": "-",
        "FORMAT": "F6.3",
    },
    "ap": {
        "DESCRIPTION": (
            "Three-hourly equivalent planetary amplitude ap for the interval"
        ),
        "UNITS": "-",
        "FORMAT": "I4",
    },
    "Kp_Flag": {
        "DESCRIPTION": (
            "Kp status flag: 0 - definitive value, 1 - preliminary value"
        ),
        "UNITS": "-",
        "FORMAT": "I1",
    },
}

CDF_GLOBAL_ATTRIBUTES = {
    "DATASET_DESCRIPTION": (
        "Kp and ap values produced by GFZ German Research Centre for "
        "Geosciences, Potsdam, Germany"
    ),
    "DATASET_DOCUMENTATION": "https://kp.gfz-potsdam.de/app/format/Kp_ap.txt",
    "CITATION": "https://doi.org/10.1029/2020SW002641",
    "LICENCE": "CC BY 4.0",
}

SOURCE_API_URL_TEMPLATE = (
    "https://kp.gfz-potsdam.de/kpdata?"
    "startdate={start:%Y-%m-%d}&enddate={end:%Y-%m-%d}&format=kp2"
)

FILENAME_TEMPLATE = (
    "GFZ_KP_{start:%Y%m%dT%H%M%S}_{end:%Y%m%dT%H%M%S}_"
    "{timestamp:%Y%m%dT%H%M%S}"
)

FILENAME_PATTERN = re.compile(
    r"^GFZ_KP_(?P<start>\d{8,8}T\d{6,6})"
    r"_(?P<end>\d{8,8}T\d{6,6})"
    r"_(?P<timestamp>\d{8,8}T\d{6,6})\.cdf$"
)

TIMESTAP_PATTERN = re.compile(
    r"^(?P<year>\d{4,4})(?P<daytime>\d{4,4}T\d{6,6})$"
)

DEFAULT_OUTPUT_DIRECTORY = "."
ONE_DAY = timedelta(days=1)
ONE_SECOND = timedelta(seconds=1)
ONE_MICROSECOND = timedelta(microseconds=1)
DT_1970 = datetime(1970, 1, 1)

LOGGER = getLogger(__name__)


class DataChunk(namedtuple("DataChunk", ["data", "metadata"])):
    """ Data chunk object. """


def utctoday():
    """ Get current UTC date. """
    return datetime.utcnow().date()


def parse_date(value):
    """ Parse ISO date. """
    return datetime.strptime(value, "%Y-%m-%d").date()


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print(
        f"USAGE: {basename(exename)} [--delete-old] <start-date> [<output dir>]"
        " [--previous-outputs=<directory>][--temp-dir=<directory>]", file=file
    )
    print("\n".join([
        "DESCRIPTION:",
        "  Download time series Kp values from source GFZ web API,",
        "  starting from the given start date until the latest available"
        "  date, and store them in one or more yearly CDF files.",
        "  The outputs are stored in the optional output directory",
        "  (current directory by default).",
        "  The program is able to incrementally update already downloaded",
        "  values if CDF files from the previous runs are available.",
        "  By default, the existing files are searched in the output",
        "  or other location if given.",
        "  When requested, the old replaced indices are removed.",
        "  Optionally, a custom directory to hold intermediate temporary",
        "  files can be specified. By default, all temporary files",
        "  are held in the output directory.",
    ]), file=file)


def parse_inputs(argv):
    """ Parse input arguments. """

    delete_old = False
    start_date = None
    output_dir = None
    previous_output_dir = None
    temp_dir = None

    it_args = iter(argv[1:])
    context=None
    ignore_options = False
    try:
        for arg in it_args:
            if arg.startswith("-") and not ignore_options:
                if arg in ("-h", "--help"):
                    usage(argv[0])
                    sys.exit()
                if arg.startswith("--previous-outputs="):
                    context = "previous output directory"
                    previous_output_dir = arg.partition("=")[2]
                elif arg == "-p":
                    context = "previous output directory"
                    previous_output_dir = next(it_args)
                elif arg.startswith("--temp-dir="):
                    context = "temporary file directory"
                    temp_dir = arg.partition("=")[2]
                elif arg in ("-d", "--delete-old"):
                    delete_old = True
                elif arg in ("+d", "--preserve-old"):
                    delete_old = False
                elif arg == "--":
                    ignore_options = True
                    continue
                else:
                    raise CommandError(f"Invalid option {arg}")
            elif start_date is None:
                context = "start date"
                start_date = parse_date(arg)
            elif output_dir is None:
                output_dir = arg
        if start_date is None:
            context = "start date"
            start_date = next(it_args)
    except StopIteration:
        raise CommandError(
            "Not enough input arguments!"
            f" Missing {context} value."
        ) from None
    except ValueError:
        raise CommandError(f"Invalid {context} value!") from None

    return start_date, output_dir, previous_output_dir, temp_dir, delete_old


def main(start_date, output_dir=None, previous_output_dir=None, temp_dir=None,
         delete_old=False):
    """ Main subroutine. """

    if not output_dir:
        output_dir = DEFAULT_OUTPUT_DIRECTORY

    if not previous_output_dir:
        previous_output_dir = output_dir

    makedirs(output_dir, exist_ok=True)

    products = list_existing_products(previous_output_dir)
    products = collect_applicable_products(products)

    ranges = yield_request_ranges(start_date)
    ranges = reversed(list(ranges))
    chunks = (request_data(start, end) for start, end in ranges)
    chunks = split_chunks_by_year(chunks)
    chunks = compare_chunks_with_previous_products(chunks, products)

    for chunk in chunks:
        chunk.metadata["identifier"] = get_id(chunk.metadata)
        filename = join(output_dir, chunk.metadata["identifier"] + ".cdf")
        save_chunk_to_cdf(filename, chunk, temp_dir)

    if delete_old:
        products = list_existing_products(output_dir)
        if output_dir != previous_output_dir:
            products = chain(
                products, list_existing_products(previous_output_dir)
            )
        remove_products(collect_removable_products(products))


def list_existing_products(path):
    """ Yield existing Kp products in the given directory. """
    with scandir(path) as items:
        for item in items:
            if item.is_file:
                match = FILENAME_PATTERN.match(item.name)
                if match:
                    yield {
                        "name": item.name,
                        "path": item.path,
                        **match.groupdict(),
                    }


def collect_applicable_products(products):
    """ Filter products and get a dictionary of applicable yearly products. """

    def _match_timestamp(value):
        match = TIMESTAP_PATTERN.match(value)
        return match.groupdict() if match else None

    def _collect_applicable(products):
        for item in sorted(products, key=lambda v: v["timestamp"]):
            start = _match_timestamp(item["start"])
            end = _match_timestamp(item["end"])
            if (
                start and end and
                start["daytime"] <= end["daytime"] and # start not after end
                start["year"] == end["year"] # both are in the same year
            ):
                yield int(start["year"]), item["path"]

    return dict(_collect_applicable(products))


def collect_removable_products(products):
    """ Yield path to old product which can be removed. """
    products = list(products)
    applicable_products = set(
        basename(product) for product
        in collect_applicable_products(products).values()
    )
    for product in products:
        if product["name"] not in applicable_products:
            yield product["path"]


def remove_products(paths):
    """ Remove listed products. """
    for path in paths:
        LOGGER.info("Removing Kp data file %s ...", path)
        try:
            remove(path)
        except Exception as error:
            LOGGER.error("Failed to remove Kp data file %s. %s", path, error)


def yield_request_ranges(start_date, last_request_days=90):
    """ Yield request ranges. Yearly request ranges are made except for the
    last 90 days to get all non-definitive values in one request.
    """

    def _yield_year_request_ranges(start_date, end_date):
        """ Generate request aligned with year boundaries. """
        for year in range(start_date.year, (end_date - ONE_DAY).year + 1):
            yield date(year, 1, 1), min(date(year + 1, 1, 1), end_date)

    end_date = utctoday() + timedelta(days=1)
    last_start = end_date - timedelta(days=last_request_days)
    last_start = max(last_start, start_date)
    last_start = date(last_start.year, 1, 1)

    yield from _yield_year_request_ranges(start_date, last_start)

    if last_start < end_date:
        yield last_start, end_date


def request_data(start, end):
    """ Make request to the server and return the parsed and sanitized data.
    """
    LOGGER.info("Retrieving Kp data from %s to %s ...", start, end - ONE_DAY)
    url = SOURCE_API_URL_TEMPLATE.format(start=start, end=(end - ONE_DAY))
    metadata = {
        "url": url,
        "start": datetime.combine(start, time()),
        "end": datetime.combine(end, time()),
    }
    try:
        metadata["timestamp"] = datetime.utcnow()
        with urlopen(url) as response:
            if "Last-Modified" in response.headers:
                metadata["timestamp"] = parsedate_to_datetime(
                    response.headers["Last-Modified"]
                )
            elif "Date" in response.headers:
                metadata["timestamp"] = parsedate_to_datetime(
                    response.headers["Date"]
                )
            data = parse_kp_data(TextIOWrapper(response, encoding="utf8"))
            data = sanitize_source_kp_data(data)
            metadata["data_start"], metadata["data_end"] = get_data_extent(data)
            return DataChunk(data=data, metadata=metadata)

    except HTTPError as error:
        LOGGER.error(
            "Failed to retrieve Kp data from %s, reason: %s", url, error
        )
        raise

    except Exception:
        LOGGER.error("Failed to read Kp data from %s", url, exc_info=True)
        raise


def split_chunks_by_year(chunks):
    """ Split data to chunks aligned and not exceeding calendar years. """
    for chunk in chunks:
        years = chunk.data["Timestamp"].astype("datetime64[Y]")
        unique_years = unique(years)
        if len(unique_years) == 1:
            yield chunk
        else:
            for year in unique_years:
                mask = years == year
                start = datetime64_to_datetime(year)
                data = {
                    key: values[mask]
                    for key, values in chunk.data.items()
                }
                metadata = {
                    **chunk.metadata,
                    "start": start,
                    "end": min(
                        datetime(start.year + 1, 1, 1),
                        chunk.metadata["end"]
                    ),
                }
                metadata["data_start"], metadata["data_end"] = get_data_extent(data)
                yield DataChunk(data=data, metadata=metadata)


def compare_chunks_with_previous_products(chunks, products):
    """ Compare data chunks to previous downloads. In case of no difference
    the chunks are dropped.
    """
    def _differs_form_old_data(chunk):
        year = chunk.metadata["start"].year

        filename = products.get(year)
        if not filename:
            return True # no previous data found -> save new data

        LOGGER.info("Found existing data in %s", filename)
        try:
            old_data = load_kp_data(filename)
        except:
            LOGGER.error("Failed to read Kp data from %s!", filename, exc_info=True)
            return True # previous data cannot be loaded -> save new data

        if not compare_kp_data(chunk.data, old_data):
            LOGGER.info("Kp data have changed")
            return True # previous are not equal -> save new data

        LOGGER.info("Kp data have not changed")
        return False # previous data have not changed -> do not save new data

    for chunk in chunks:
        # drop chunks which do not differ from the already saved data
        if _differs_form_old_data(chunk):
            yield chunk


def get_id(metadata):
    """ Get product identifier. """
    return FILENAME_TEMPLATE.format(
        start=metadata["data_start"],
        end=metadata["data_end"],
        timestamp=metadata["timestamp"],
    )


def save_chunk_to_cdf(filename, chunk, temp_dir=None):
    """ Save data chunk to a new CDF file. """
    LOGGER.info("Saving Kp data to %s ...", filename)

    if not temp_dir:
        temp_dir = dirname(filename)

    filename_tmp = join(temp_dir, basename(filename) + ".tmp.cdf")

    if exists(filename_tmp):
        remove(filename_tmp)

    try:
        save_kp_data(filename_tmp, chunk.data, chunk.metadata)
        rename(filename_tmp, filename)

    finally:
        if exists(filename_tmp):
            remove(filename_tmp)


def load_kp_data(filename):
    """ Load Kp data from a CDF file. """

    def _load_cdf_data(cdf, variable, parser=None):
        data = cdf.raw_var(variable)[...]
        if parser:
            data = parser(data)
        return data

    with cdf_open(filename) as cdf:
        return {
            "Timestamp": _load_cdf_data(cdf, "Timestamp", CdfTypeEpoch.decode),
            "Interval": _load_cdf_data(cdf, "Interval"),
            "Kp": _load_cdf_data(cdf, "Kp"),
            "ap": _load_cdf_data(cdf, "ap"),
            "Kp_Flag": _load_cdf_data(cdf, "Kp_Flag"),
        }


def compare_kp_data(data1, data2):
    """ Compare Kp data. """
    if set(data1) != set(data2):
        raise ValueError("Dictionary keys must the same!")
    for key in data1:
        if not array_equal(data1[key], data2[key], equal_nan=True):
            return False
    return True


def save_kp_data(filename, data, metadata):
    """ Save Kp data to a CDF file. """

    def _format_datetime(value):
        return value.replace(microsecond=0, tzinfo=None).isoformat() + "Z"

    def _save_cdf_variable(cdf, variable, cdf_type, data, attrs=None):
        cdf.new(
            variable, data, cdf_type, dims=data.shape[1:],
            **CDF_VARIABLE_PARAMETERS,
        )
        cdf[variable].attrs.update(
            attrs or CDF_VARIABLE_ATTRIBUTES.get(variable) or {}
        )

    with cdf_open(filename, "w") as cdf:
        cdf.attrs.update({
            "TITLE": metadata["identifier"],
            "REQUEST_URL": metadata["url"],
            "REQUESTED": _format_datetime(metadata["timestamp"]),
            **CDF_GLOBAL_ATTRIBUTES,
            "CREATED": _format_datetime(datetime.utcnow()),
            "CREATOR": CDF_CREATOR,
        })
        _save_cdf_variable(
            cdf, "Timestamp", CDF_EPOCH, CdfTypeEpoch.encode(data["Timestamp"])
        )
        _save_cdf_variable(cdf, "Interval", CDF_UINT2, data["Interval"])
        _save_cdf_variable(cdf, "Kp", CDF_DOUBLE, data["Kp"])
        _save_cdf_variable(cdf, "ap", CDF_INT2, data["ap"])
        _save_cdf_variable(cdf, "Kp_Flag", CDF_UINT1, data["Kp_Flag"])


def parse_kp_data(lines, comment="#"):
    """ Parse Kp data text file. """

    kp_fields = (
        "date", "hour_start", "hour_centre", "mjd1932_start", "mjd1932_centre",
        "kp", "ap", "definitive",
    )
    kp_dtypes = (
        "datetime64", "float64", "float64", "float64", "float64",
        "float64", "int16", "int8",
    )
    kp_field_types = (
        str, str, str, float, float, float, float, float, int, int,
    )

    def _parse_kp_record(line):
        year, month, day, *fields = (
            type_(value) for type_, value in zip(kp_field_types, line.split())
        )
        return (f"{year}-{month}-{day}", *fields)

    data = {field: [] for field in kp_fields}
    for line in lines:
        # strip commends and leading and trailing white-spaces
        line = line.partition(comment)[0].strip()
        if not line: # skip empty lines
            continue
        record = _parse_kp_record(line)
        for values, value in zip(data.values(), record):
            values.append(value)

    return {
        key: array(values, dtype=dtype)
        for dtype, (key, values) in zip(kp_dtypes, data.items())
    }


def sanitize_source_kp_data(source_data):
    """ Sanitize the source Kp data. """
    # start of the interval in seconds from the day start
    interval_start = (
        source_data["hour_centre"] * 3600
    ).round().astype("timedelta64[s]")

    # length of the time-interval in seconds
    interval_duration = 2 * (
        source_data["hour_centre"] - source_data["hour_start"]
    )
    interval_duration[interval_duration < 0] += 24
    interval_duration = (interval_duration * 3600).round().astype("uint16")

    return {
        "Timestamp": source_data['date'] + interval_start,
        "Interval": interval_duration,
        "Kp": source_data["kp"],
        "ap": source_data["ap"],
        "Kp_Flag": (source_data["definitive"] == 0).astype("uint8"),
    }


def get_data_extent(data):
    if data["Timestamp"].size == 0:
        return None, None
    return (
        datetime64_to_datetime(data["Timestamp"][0]),
        datetime64_to_datetime(data["Timestamp"][-1])
    )


def datetime64_to_datetime(value):
    """ Convert numpy.datetime64 value to datetime.datetime object."""
    us1970 = int(value.astype("datetime64[us]").astype("int64"))
    return DT_1970 + timedelta(microseconds=us1970)


def _run():
    setup_logging()
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        LOGGER.error("%s", error)


if __name__ == "__main__":
    _run()
