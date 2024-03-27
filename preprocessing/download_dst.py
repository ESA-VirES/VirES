#!/usr/bin/env python3
#-------------------------------------------------------------------------------
#
# Download Dst index values from WDC server and convert them one or more CDF
# files.
#
# For more details on the Dst data see
#   https://wdc.kugi.kyoto-u.ac.jp/wdc/Sec3.html
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
# pylint: disable=missing-module-docstring
# pylint: disable=broad-exception-caught,bare-except,superfluous-parens
# pylint: disable=too-many-branches,too-many-statements,too-many-arguments
# pylint: disable=too-many-locals,too-few-public-methods,too-many-lines

import sys
import re
import os
import os.path
import io
import json
import collections
import logging
import datetime
import http.client
import urllib.parse
import email.utils
import numpy
from common import (
    LOG_LEVELS, init_console_logging, init_file_logging,
    cdf_open, CommandError,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
    CDF_UINT1, CDF_INT2, CDF_EPOCH, CDF_DOUBLE, CdfTypeEpoch,
)

ONE_DAY = datetime.timedelta(days=1)


class App:
    """ The app. """
    NAME = "download_dst"
    VERSION = "1.1.0"

    @classmethod
    def run(cls, *argv):
        """ Run the app. """
        logging_is_on = False
        try:
            inputs = cls.parse_inputs(argv)
            init_console_logging(
                log_level=inputs.pop("verbosity"),
            )
            init_file_logging(
                log_level=inputs.pop("log_level"),
                log_file=inputs.pop("log_file"),
            )
            logging_is_on = True
            sys.exit(cls.main(**inputs))
        except CommandError as error:
            if not logging_is_on:
                init_console_logging()
            logging.getLogger(__name__).error("%s", error)
            sys.exit(1)

    @staticmethod
    def usage(exename, file=sys.stderr):
        """ Print usage. """
        print(
            f"USAGE: {os.path.basename(exename)} [--delete-old] <start-date> [<output dir>]"
            "[--temp-dir=<directory>][--cache-dir=<directory>]"
            "[--verbosity=<level>][--log-file=<path>][--log-level=<level>]"
            "[--force-write][--no-update-check]", file=file
        )
        print("\n".join([
            "DESCRIPTION:",
            "  Download time series Dst values from source WDC Kyoto server,",
            "  starting from the given start date until the latest available"
            "  date, and store them in one or more yearly CDF files.",
            "  The outputs are stored in the optional output directory",
            "  (current directory by default).",
            "  When requested, the old replaced indices are removed.",
            "  Optionally, a custom directory to hold intermediate temporary",
            "  files can be specified. By default, all temporary files",
            "  are held in the output directory. "
            "  The program caches the source monthly files in the cache",
            "  directory (<temp.dir>/cache/)`",
        ]), file=file)

    @classmethod
    def parse_inputs(cls, argv):
        """ Parse input arguments. """

        check_for_updates = True
        force_write = False
        verbosity = logging.INFO
        log_file = None
        log_level = logging.INFO
        delete_old = False
        start_date = None
        output_dir = None
        temp_dir = None
        cache_dir = None

        it_args = iter(argv[1:])
        context=None
        ignore_options = False
        try:
            for arg in it_args:
                if arg.startswith("-") and not ignore_options:
                    if arg in ("-h", "--help"):
                        cls.usage(argv[0])
                        sys.exit()
                    elif arg.startswith("--verbosity="):
                        try:
                            verbosity = LOG_LEVELS[arg.partition("=")[2]]
                        except KeyError:
                            raise CommandError(
                                f"Invalid verbosity {arg.partition('=')[2]}!"
                            ) from None
                    elif arg.startswith("--log-level="):
                        try:
                            log_level = LOG_LEVELS[arg.partition("=")[2]]
                        except KeyError:
                            raise CommandError(
                                f"Invalid log level {arg.partition('=')[2]}!"
                            ) from None
                    elif arg.startswith("--log-file="):
                        log_file = arg.partition("=")[2]
                    elif arg.startswith("--temp-dir="):
                        context = "temporary file directory"
                        temp_dir = arg.partition("=")[2]
                    elif arg.startswith("--cache-dir="):
                        context = "cache directory"
                        cache_dir = arg.partition("=")[2]
                    elif arg in ("-d", "--delete-old"):
                        delete_old = True
                    elif arg in ("+d", "--preserve-old"):
                        delete_old = False
                    elif arg == "--force-write":
                        force_write = True
                    elif arg == "--no-update-check":
                        check_for_updates = False
                    elif arg == "--":
                        ignore_options = True
                        continue
                    else:
                        raise CommandError(f"Invalid option {arg}")
                elif start_date is None:
                    context = "start date"
                    start_date = Date.parse(arg)
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

        if not output_dir:
            output_dir = "."

        if not temp_dir:
            temp_dir = output_dir

        if not cache_dir:
            cache_dir = os.path.join(temp_dir, "cache")

        return {
            "start_date": start_date,
            "output_dir": output_dir,
            "temp_dir": temp_dir,
            "cache_dir": cache_dir,
            "delete_old": delete_old,
            "verbosity": verbosity,
            "log_file": log_file,
            "log_level": log_level,
            "force_write": force_write,
            "check_for_updates": check_for_updates,
        }

    @classmethod
    def main(cls, start_date, output_dir=None, temp_dir=None, cache_dir=None,
             delete_old=False, force_write=False, check_for_updates=True, **_):
        """ Main subroutine. """

        dst_store = DstProductStore(
            output_dir=output_dir,
            temp_dir=temp_dir,
        )
        dst_source = DstDataSource(
            cache_dir=(cache_dir or temp_dir),
        )

        ranges = cls.yield_request_ranges(start_date)

        with dst_source:
            chunks = dst_source.retrieve_request_ranges(
                ranges, check_for_updates=check_for_updates
            )

        if not force_write:
            chunks = dst_store.filter_unchanged_chunks(chunks)

        for chunk in chunks:
            dst_store.save_chunk(chunk)

        if delete_old:
            dst_store.delete_old()

    @staticmethod
    def yield_request_ranges(start_date):
        """ Yield yearly request ranges.  """
        end_date = Date.today() + ONE_DAY
        for year in reversed(range(start_date.year, (end_date - ONE_DAY).year + 1)):
            yield Date.create(year, 1, 1), min(Date.create(year + 1, 1, 1), end_date)


class DstProductStore:
    """ Product storage. """

    DEFAULT_OUTPUT_DIRECTORY = "."

    ID_TEMPLATE = (
        "WDC_DST_{start:%Y%m%dT%H%M%S}_{end:%Y%m%dT%H%M%S}_"
        "{timestamp:%Y%m%dT%H%M%S}"
    )

    FILENAME_PATTERN = re.compile(
        r"^WDC_DST_(?P<start>\d{8,8}T\d{6,6})"
        r"_(?P<end>\d{8,8}T\d{6,6})"
        r"_(?P<timestamp>\d{8,8}T\d{6,6})\.cdf$"
    )

    TIMESTAP_PATTERN = re.compile(
        r"^(?P<year>\d{4,4})(?P<day>\d{4,4})T\d{6,6}$"
    )

    def __init__(self, output_dir=None, temp_dir=None, logger=None):

        if not output_dir:
            output_dir = self.DEFAULT_OUTPUT_DIRECTORY

        if not temp_dir:
            temp_dir = output_dir

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)

        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.logger = logger or logging.getLogger(__name__)

    def delete_old(self):
        """ Remove old superseded products. """

        def _remove_product(path):
            self.logger.info("Removing Dst data file %s ...", path)
            try:
                os.remove(path)
            except Exception as error:
                self.logger.error(
                    "Failed to remove Dst data file %s. %s", path, error
                )

        for path in self.list_removable_products():
            _remove_product(path)

    def filter_unchanged_chunks(self, chunks):
        """ Compare chunks to the existing products and drop chunks
        identical to the existing data.
        """
        products = self.get_applicable_products()

        def _data_has_changed(chunk):
            year = chunk.metadata["start"].year

            filename = products.get(year)
            if not filename:
                return True # no previous data found

            self.logger.debug("Found existing data in %s", filename)
            try:
                old_data = DstProduct.load(filename)
            except:
                self.logger.error("Failed to read Dst data from %s!", filename, exc_info=True)
                return True # previous data cannot be loaded

            if not self._compare_data(chunk.data, old_data):
                self.logger.debug("Dst data has changed.")
                return True # previous are not equal

            self.logger.debug("Dst data has not changed.")
            return False # previous data are equal

        for chunk in chunks:
            if _data_has_changed(chunk):
                yield chunk

    def get_applicable_products(self):
        """ Get year/filename dictionary of applicable yearly products. """
        return self.collect_applicable(self.list_existing(self.output_dir))

    def save_chunk(self, chunk):
        """ Save chunk to file to CDF file"""
        product_id = self.get_id(chunk.metadata)
        chunk.metadata["identifier"] = product_id

        filename = os.path.join(self.output_dir, f"{product_id}.cdf")
        filename_tmp = os.path.join(
            self.temp_dir or self.output_dir, f"{product_id}.tmp.cdf"
        )

        self.logger.info("Saving Dst data to %s ...", filename)

        if os.path.exists(filename_tmp):
            os.remove(filename_tmp)

        try:
            DstProduct.save(filename_tmp, chunk.data, chunk.metadata)
            os.rename(filename_tmp, filename)

        finally:
            if os.path.exists(filename_tmp):
                os.remove(filename_tmp)

    @classmethod
    def get_id(cls, metadata):
        """ Get product identifier. """
        return cls.ID_TEMPLATE.format(
            start=metadata["data_start"],
            end=metadata["data_end"],
            timestamp=metadata["timestamp"],
        )

    @classmethod
    def list_existing(cls, path):
        """ Yield existing Dst products in the given directory. """
        with os.scandir(path) as items:
            for item in items:
                if item.is_file:
                    match = cls.FILENAME_PATTERN.match(item.name)
                    if match:
                        yield {
                            "name": item.name,
                            "path": item.path,
                            **match.groupdict(),
                        }

    @classmethod
    def collect_applicable(cls, products):
        """ Filter listed products and get a dictionary of applicable
        yearly products.

        Applicable products start on 1 January, do not exceed one calendar year.
        """

        def _match_timestamp(value):
            match = cls.TIMESTAP_PATTERN.match(value)
            return match.groupdict() if match else None

        def _collect_applicable(products):
            for item in products:
                start = _match_timestamp(item["start"])
                end = _match_timestamp(item["end"])
                if (
                    start and end and
                    item["start"] < item["end"] and # start is before end
                    start["day"] == "0101" and # starts on 1 January
                    start["year"] == end["year"] # both are in the same year
                ):
                    yield int(start["year"]), item["path"]

        return dict(_collect_applicable(sorted(products, key=lambda v: v["name"])))

    def list_removable_products(self):
        """ Yield path to old product which can be removed. """
        products = list(self.list_existing(self.output_dir))
        applicable_products = set(
            os.path.basename(product) for product
            in self.collect_applicable(products).values()
        )
        for product in products:
            if product["name"] not in applicable_products:
                yield product["path"]

    @staticmethod
    def _compare_data(data1, data2):
        """ Compare Dst data. """
        if set(data1) != set(data2):
            return False
        for key in data1:
            if not numpy.array_equal(data1[key], data2[key], equal_nan=True):
                return False
        return True


class DstProduct:
    """ Dst CDF file operations. """

    CDF_CREATOR = (
        f"EOX:{App.NAME}-{App.VERSION} [{SPACEPY_NAME}-{SPACEPY_VERSION}, "
        f"libcdf-{LIBCDF_VERSION}]"
    )

    CDF_VARIABLE_PARAMETERS = {
        "compress": GZIP_COMPRESSION,
        "compress_param": GZIP_COMPRESSION_LEVEL4
    }

    CDF_VARIABLE_ATTRIBUTES = {
        "Timestamp": {
            "DESCRIPTION": (
                "UTC timestamp - middle of the interval for which the Dst"
                " values are given"
            ),
            "UNITS": "-",
            "FORMAT": " ",
        },
        "Dst": {
            "DESCRIPTION": (
                "Hourly geomagnetic equatorial Dst index"
            ),
            "UNITS": "nT",
            "FORMAT": "F6.3",
        },
        "dDst": {
            "DESCRIPTION": (
                "Absolute rate of change of the hourly Dst index"
                " (calculated as an absolute value of the difference between"
                " two consecutive hourly Dst values)"
            ),
            "UNITS": "nT/h",
            "FORMAT": "F6.3",
        },
        "Dst_Flag": {
            "DESCRIPTION": (
                "Dst status flag: 0 - definitive value, 1 - provisional value,"
                " 2 - real-time value"
            ),
            "UNITS": "-",
            "FORMAT": "I1",
        },
        "Dst_Version": {
            "DESCRIPTION": (
                "Version of the sample as a number of applied corrections"
            ),
            "UNITS": "-",
            "FORMAT": "I1",
        },
    }

    CDF_GLOBAL_ATTRIBUTES = {
        "DATASET_DESCRIPTION": (
            "Dst produced by World Data Center for Geomagnetism, Kyoto, Japan"
        ),
        "DATASET_DOCUMENTATION": "https://wdc.kugi.kyoto-u.ac.jp/wdc/Sec3.html",
        "LICENCE": "Free for non-commercial use.",
    }

    @classmethod
    def save(cls, filename, data, metadata):
        """ Save Dst data to a CDF file. """

        def _format_datetime(value):
            return Timestamp.format(value.replace(microsecond=0))

        def _save_cdf_variable(cdf, variable, cdf_type, data, attrs=None):
            cdf.new(
                variable, data, cdf_type, dims=data.shape[1:],
                **cls.CDF_VARIABLE_PARAMETERS,
            )
            cdf[variable].attrs.update(
                attrs or cls.CDF_VARIABLE_ATTRIBUTES.get(variable) or {}
            )

        with cdf_open(filename, "w") as cdf:
            cdf.attrs.update({
                "TITLE": metadata["identifier"],
                "SOURCE_URL": metadata["urls"],
                "SOURCE_TIMESTAMP": [
                    _format_datetime(timestamp)
                    for timestamp in metadata["timestamps"]
                ],
                "LAST_MODIFIED": _format_datetime(metadata["timestamp"]),
                **cls.CDF_GLOBAL_ATTRIBUTES,
                "CREATED": Timestamp.format(Timestamp.now()),
                "CREATOR": cls.CDF_CREATOR,
            })
            _save_cdf_variable(
                cdf, "Timestamp", CDF_EPOCH, CdfTypeEpoch.encode(data["Timestamp"])
            )
            _save_cdf_variable(cdf, "Dst", CDF_DOUBLE, data["Dst"])
            _save_cdf_variable(cdf, "dDst", CDF_DOUBLE, data["dDst"])
            _save_cdf_variable(cdf, "Dst_Version", CDF_INT2, data["Dst_Version"])
            _save_cdf_variable(cdf, "Dst_Flag", CDF_UINT1, data["Dst_Flag"])

    @staticmethod
    def load(filename):
        """ Load Dst data from a CDF file. """

        def _load_cdf_data(cdf, variable, parser=None):
            data = cdf.raw_var(variable)[...]
            if parser:
                data = parser(data)
            return data

        with cdf_open(filename) as cdf:
            return {
                "Timestamp": _load_cdf_data(cdf, "Timestamp", CdfTypeEpoch.decode),
                "Dst": _load_cdf_data(cdf, "Dst"),
                "dDst": _load_cdf_data(cdf, "dDst"),
                "Dst_Version": _load_cdf_data(cdf, "Dst_Version"),
                "Dst_Flag": _load_cdf_data(cdf, "Dst_Flag"),
            }


class DstDataSource:
    """ Object representing Dst data source. """

    class DataChunk(collections.namedtuple("DataChunk", ["data", "metadata"])):
        """ Data chunk object. """

    class NotFoundError(Exception):
        """ Exception raised when the requested Dst file is not found. """

    SOURCE_BASE_URL =  "https://wdc.kugi.kyoto-u.ac.jp"
    SOURCE_PATH_TEMPLATE = {
        "realtime": (
            "/dst_realtime/{start:%Y%m}/dst{start:%y%m}.for.request"
        ),
        "provisional": (
            "/dst_provisional/{start:%Y%m}/dst{start:%y%m}.for.request"
        ),
        "final": (
            "/dst_final/{start:%Y%m}/dst{start:%y%m}.for.request"
        )
    }

    @classmethod
    def _get_fresh_sources(cls):
        return DstSources(cls.SOURCE_PATH_TEMPLATE)

    @classmethod
    def _get_data_path(cls, source, year, month):
        return cls.SOURCE_PATH_TEMPLATE[source].format(start=Date.create(year, month, 1))

    def __init__(self, cache_dir=None, logger=None):
        self._connection = HttpConnectionFactory.from_url(self.SOURCE_BASE_URL)()
        self._data_cache = JsonCache(cache_dir=(cache_dir or "."))
        self._tested_sources = self._get_fresh_sources()
        self.logger = logger or logging.getLogger(__name__)

    def __del__(self):
        if hasattr(self, "_connection"):
            self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._connection.close()

    def reset_sources(self):
        """ Reset tried Dst sources """
        self._tested_sources = self._get_fresh_sources()

    def retrieve_request_ranges(self, ranges, check_for_updates=True):
        """ Handle sequence of request time ranges. """

        def _yield_request_range_chunks(start, end):
            for year in reversed(range(start.year, (end - ONE_DAY).year + 1)):
                yield from _yield_one_year_request_range_chunks(
                    start=max(Date.create(year, 1, 1), start),
                    end=min(Date.create(year + 1, 1, 1), end),
                )

        def _yield_one_year_request_range_chunks(start, end):
            if start.year != (end - ONE_DAY).year:
                raise ValueError("Time selection crosses calendar year boundary!")
            for month in reversed(range(start.month, (end - ONE_DAY).month + 1)):
                yield self.retrieve_monthly_data(
                    start.year, month, check_for_updates=check_for_updates
                )

        def _calculate_ddst(chunks):
            """ Calculate dDst from a stream of time-ordered yearly chunks. """
            last_chunk = None
            for chunk in chunks:
                if (
                    last_chunk and
                    last_chunk.metadata["start"] != chunk.metadata["end"]
                ):
                    self.logger.warning(
                        "Disconnected data chunks! %s != %s",
                        Timestamp.format(last_chunk.metadata["start"]),
                        Timestamp.format(chunk.metadata["end"]),
                    )
                    last_chunk = None
                yield self.calculate_ddst(chunk, last_chunk)
                last_chunk = chunk

        def _ranges_to_yearly_chunks(ranges):
            for start, end in ranges:
                if end >= start:
                    yield self.concatenate_chunks(
                        _yield_request_range_chunks(start, end)
                    )

        yield from _calculate_ddst(_ranges_to_yearly_chunks(ranges))

    def retrieve_monthly_data(self, year, month, check_for_updates=True):
        """ Retrieve monthly Dst data for the give year and month.
        Set check_for_updates flag to False if the check for updates is not
        desired for cached data.
        """

        def datetime64_to_datetime(value):
            """ Convert numpy.datetime64 value to datetime.datetime object."""
            us1970 = int(value.astype("datetime64[us]").astype("int64"))
            return Timestamp.DT_1970 + datetime.timedelta(microseconds=us1970)

        def get_data_extent(data):
            if data["Timestamp"].size == 0:
                return None, None
            return (
                datetime64_to_datetime(data["Timestamp"][0]),
                datetime64_to_datetime(data["Timestamp"][-1])
            )

        raw_data = self.retrieve_monthly_file(
            year=year, month=month, check_for_updates=check_for_updates
        )
        data, timestamp = DstFile.parse(
            year, month, io.StringIO(raw_data["body"])
        )
        data = DstFile.sanitize(data, raw_data["source"])

        metadata = {
            "url": urllib.parse.urljoin(self._connection.url, raw_data["path"]),
            "source": raw_data["source"],
            "timestamp": timestamp or Timestamp.parse(raw_data["timestamp"]),
            "start": Timestamp.create(year, month, 1),
            "end": Timestamp.create(year + month // 12, 1 + month % 12, 1),
        }

        metadata["data_start"], metadata["data_end"] = get_data_extent(data)

        return self.DataChunk(data=data, metadata=metadata)

    def retrieve_monthly_file(self, year, month, check_for_updates=True):
        """ Retrieve monthly Dst file for the give year and month.
        Set check_for_updates flag to False if the check for updates is not
        desired for cached data.
        """
        label = f"dst-{year:04d}-{month:02d}"

        # retrieve cached data if existing
        data = self._data_cache.read_data(label)

        if data:
            # cached data found
            self.logger.debug("Cached %04d-%02d Dst file found.", year, month)

            if not check_for_updates:
                # use cached data without checking for updates
                return data

            # check if cached data is up-to-date (HEAD request)
            head = self._request_monthly_file(HttpHeadRequest, year, month)
            if (
                data["path"] == head["path"] and
                data["entity_tag"] == head["entity_tag"] and
                Timestamp.parse(data["timestamp"]) >=
                Timestamp.parse(head["timestamp"])
            ):
                self.logger.debug("Cached %04d-%02d Dst file is up-to-date.", year, month)
                # cached data is up-to-date
                return data

            self.logger.debug("Cached %04d-%02d Dst file is outdated.", year, month)

        # retrieve new data (GET request)
        data = self._request_monthly_file(HttpGetRequest, year, month)

        # save new data to cache
        self._data_cache.write_data(label, data)
        self.logger.debug("Stored %04d-%02d Dst file to cache.", year, month)

        return data

    def _request_monthly_file(self, request_factory, year, month):
        while self._tested_sources:
            source = self._tested_sources.current
            request = request_factory(self._get_data_path(source, year, month))
            try:
                return {
                    "source": source,
                    **self._connection.request(request),
                }
            except HttpError as error:
                if error.status not in (404, 403):
                    self.logger.error(
                        "Failed to access %s. Reason: %s",
                        request.selector, error,
                    )
                    raise
                self.logger.info(
                    "Failed to access %s. Trying next source ...",
                    request.selector
                )
                self._tested_sources.set_next()
                continue
            except Exception as error:
                self.logger.error(
                    "Failed to access %s. Reason: %s",
                    request.selector, error,
                )
                raise

        self.logger.error(
            "%04d-%02d Dst file not found on the server.", year, month
        )
        raise self.NotFoundError(f"{year:04d}-{month:02d} Dst file not found!")

    @classmethod
    def concatenate_chunks(cls, chunks):
        """ Concatenate multiple chunks into one in the given order.
        This function requires at least one data chunk to be provided.
        """
        chunks = sorted(chunks, key=lambda item: item.metadata["start"])
        if not chunks:
            raise ValueError("No chunk to be concatenated!")

        result = cls.DataChunk(
            data={
                field: numpy.concatenate([item[field] for item, _ in chunks])
                for field in chunks[0].data
            },
            metadata={
                "urls": [item.metadata["url"] for item in chunks],
                "sources": {item.metadata["source"] for item in chunks},
                "start": min(item.metadata["start"] for item in chunks),
                "end": max(item.metadata["end"] for item in chunks),
                "data_start": min(item.metadata["data_start"] for item in chunks),
                "data_end": max(item.metadata["data_end"] for item in chunks),
                "timestamp": max(item.metadata["timestamp"] for item in chunks),
                "timestamps": [item.metadata["timestamp"] for item in chunks],
            }
        )

        # assuming the time-stamp is the first field
        time = result.data[list(result.data)[0]]
        time_delta = time[1:] - time[:-1]

        # assert strictly ascending time sampling
        if time_delta.min() <= datetime.timedelta(0):
            raise ValueError("Time is not strictly ascending!")

        # assert uniform time sampling
        if time_delta.max() > time_delta.min():
            raise ValueError("Time is not uniformly sampled!")

        return result

    @classmethod
    def calculate_ddst(cls, chunk, next_chunk):
        """ Calculate the dDst as absolute value of the rate of the Dst.
        The rate of change is calculated from the difference of two consecutive
        values.
        """
        # check the equidistant time sampling
        times = chunk.data["Timestamp"]
        time_tail = next_chunk.data["Timestamp"][0] if next_chunk else None

        if (
            ((times[1:] - times[:-1]) != DstFile.SAMPLING).any() or
            (next_chunk and (time_tail - times[-1]) != DstFile.SAMPLING)
        ):
            raise ValueError("Irregular time sampling!")

        # calculate dDst
        dst = chunk.data["Dst"]
        dst_tail = next_chunk.data["Dst"][0] if next_chunk else numpy.nan

        chunk.data["dDst"] = numpy.abs(
            numpy.concatenate((dst[1:], [dst_tail])) - dst
        ) / DstFile.SAMPLING_H

        # update metadata
        if next_chunk:
            chunk.metadata["urls"].append(next_chunk.metadata["urls"][0])
            chunk.metadata["timestamps"].append(next_chunk.metadata["timestamps"][0])
            chunk.metadata["timestamp"] = max(chunk.metadata["timestamps"])

        return chunk


class DstFile:
    """ Dst file parser. """

    class ParsingError(Exception):
        """ Exception raised when the requested Dst file cannot be parsed. """

    SAMPLING_H = 1 # sapling rate in hours
    SAMPLING = numpy.timedelta64(60, "m") # sapling rate as numpy.timedelta64

    DST_FLAG = {"realtime": 2, "provisional": 1, "final": 0}

    MONTH = {name: idx + 1 for idx, name in enumerate([
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ])}

    WDC_DST_RECORD_PATTERN = re.compile(
        r"^DST(?P<year_short>\d{2,2})(?P<month>\d{2,2})\*(?P<day>\d{2,2})"
        r"(?P<type>(RR|PP|  ))X(?P<version>(\d| ))(?P<year_prefix>(\d\d|  ))"
        r"(?P<base_value>.{4,4})(?P<hourly_values>.{96,96})(?P<mean_value>.{4,4})"
    )

    WDC_DST_TIMESTAMP_PATTERN = re.compile(
        r"^\[Created at (?P<week_day>(Mon|Tue|Wed|Thu|Fri|Sat|Sun))"
        r" (?P<month>(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))"
        r" (?P<day>\d{1,2}) (?P<hour>\d{2,2}):(?P<minute>\d{2,2})"
        r":(?P<second>\d{2,2}) UTC (?P<year>\d{4,4})\]$"
    )

    @classmethod
    def sanitize(cls, data, source):
        """ Sanitize the source Dst data. """
        return {
            "Timestamp": data["timestamp"],
            "Dst": data["dst"],
            "Dst_Version": data["version"],
            "Dst_Flag": numpy.full(
                data["timestamp"].shape, cls.DST_FLAG[source], "uint8"
            ),
        }

    @classmethod
    def parse(cls, year, month, lines):
        """ Parse DST data from the WDC-like text file.
        See https://wdc.kugi.kyoto-u.ac.jp/dstae/format/dstformat.html
        """
        nodata_value = 9999
        dst_fields = ("timestamp", "dst", "version")
        dst_dtypes = ("datetime64", "float64", "int8")

        def _parse_line(year_short, year_prefix, month, day, version,
                        base_value, hourly_values, mean_value, **_):
            if year_prefix == "  ":
                year_prefix = "19"

            # check the date
            Date.create(int(f"{year_prefix}{year_short}"), int(month), int(day))

            date_ = f"{year_prefix}{year_short}-{month}-{day}"
            version = -1 if version == " " else int(version)
            base_value = int(base_value) * 100
            hourly_values = [
                int(hourly_values[idx*4:(idx + 1)*4])
                for idx in range(24)
            ]
            mean_value = int(mean_value)

            return {
                "date": date_,
                "version": version,
                "base_value": base_value,
                "hourly_values": hourly_values,
                "mean_value": mean_value,
            }

        def _expand_hourly_values(date, hourly_values, base_value, version, **_):
            for hour, value in enumerate(hourly_values):
                if value != nodata_value:
                    yield f"{date}T{hour:02d}:30", value + base_value, version

        def _get_timestamp(year, month, day, hour, minute, second, **_):
            return Timestamp.create(
                int(year), cls.MONTH[month], int(day),
                int(hour), int(minute), int(second),
            )

        timestamp = None
        data = {key: [] for key in dst_fields}

        for line_no, line in enumerate(lines, 1):
            line = line.rstrip() # strip trailing white-spaces
            if not line: # skip empty lines
                continue
            if line.startswith("DST"):
                match = cls.WDC_DST_RECORD_PATTERN.match(line)
                try:
                    if not match:
                        raise ValueError
                    parsed_line = _parse_line(**match.groupdict())
                    for record in _expand_hourly_values(**parsed_line):
                        for key, value in zip(dst_fields, record):
                            data[key].append(value)
                except ValueError:
                    raise cls.ParsingError(
                        f"Failed to parse the {year:04d}-{month:02d} Dst "
                        f"WDC file! line {line_no}: {line}"
                    ) from None
                continue
            match = cls.WDC_DST_TIMESTAMP_PATTERN.match(line)
            if match:
                timestamp = _get_timestamp(**match.groupdict())

        return {
            key: numpy.array(values, dtype)
            for (key, values), dtype in zip(data.items(), dst_dtypes)
        }, timestamp


class DstSources:
    """ Object holding tried sources. """

    def __init__(self, sources):
        self.sources = list(sources)

    def __bool__(self):
        return bool(self.sources)

    @property
    def current(self):
        """ Get current source. """
        return self.sources[0]

    def set_next(self):
        """ Set current source to the next available. """
        self.sources.pop(0)


class JsonCache:
    """ Simple JSON file-based data cache. """

    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or "."
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_file_path(self, name):
        return os.path.join(self.cache_dir, f"{name}.json")

    def read_data(self, name):
        """ Read data from the JSON cache. """
        try:
            with open(self._get_file_path(name), encoding="utf8") as file:
                return json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return None

    def write_data(self, name, data):
        """ Read data from the JSON cache. """
        with open(self._get_file_path(name), "w", encoding="utf8") as file:
            json.dump(data, file)


class HttpError(Exception):
    """ Data request error. """
    def __init__(self, status, reason, body):
        self.status = status
        self.reason = reason
        self.body = body


class HttpRequest:
    """ Base HTTP request class. """
    RE_ETAG = re.compile(r'^(?:W/)?"(.*)"$')
    method = None

    def __init__(self, selector, headers=None):
        self.selector = selector
        self.headers = headers or {}

    def handle_response(self, response):
        """ Handle HTTP response. """
        now = Timestamp.now()
        body = io.TextIOWrapper(response, encoding="utf8").read()
        if response.status != 200:
            raise HttpError(response.status, response.reason, body)
        return {
            "path": self.selector,
            "requested": Timestamp.format(now),
            "timestamp": Timestamp.format(
                self._extract_timestamp(response, now)
            ),
            "entity_tag": self._extract_etag(response),
            "body": body,
        }

    @staticmethod
    def _extract_timestamp(response, now):
        def _parse_timestamp(value):
            return (
                None if value is None else
                email.utils.parsedate_to_datetime(value)
            )
        return (
            _parse_timestamp(response.getheader("Last-Modified")) or
            _parse_timestamp(response.getheader("Date")) or
            now
        )

    @classmethod
    def _extract_etag(cls, response):
        def _parse_etag(value):
            match = cls.RE_ETAG.match(value or "")
            return match.group(1) if match else None
        return _parse_etag(response.getheader("ETag"))


class HttpHeadRequest(HttpRequest):
    """ HTTP/HEAD request class. """
    method = "HEAD"


class HttpGetRequest(HttpRequest):
    """ HTTP/GET request class. """
    method = "GET"


class HttpConnection:
    """ HTTP connection wrapper. """
    def __init__(self, url, connection, logger=None):
        self.url = url
        self.connection = connection
        self.logger = logger or logging.getLogger(__name__)

    def request(self, request):
        """ Make HTTP request. """
        if not self.connection.sock:
            self.logger.info("Connecting to %s", self.url)
        self.logger.info("%s %s", request.method, request.selector)
        self.connection.request(
            request.method, request.selector, headers=request.headers
        )
        return request.handle_response(self.connection.getresponse())

    def close(self):
        """ Close wrapped connection. """
        if  self.connection.sock:
            self.logger.info("Disconnecting from %s", self.url)
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class HttpConnectionFactory:
    """ HTTPConnection factory class. """

    DEFAULT_PORT = {
        "http": http.client.HTTP_PORT,
        "https": http.client.HTTPS_PORT,
    }

    CONNECTION_CLASS = {
        "http": http.client.HTTPConnection,
        "https": http.client.HTTPSConnection,
    }

    @classmethod
    def from_url(cls, url, **options):
        """ Create HttpConnectionFactory object from the given URL,
        parsinf the scheme (protocol) and netloc (host, port) parts.
        """
        parsed_url = urllib.parse.urlsplit(url)
        return cls(
            protocol=parsed_url.scheme,
            host=parsed_url.hostname,
            port=parsed_url.port,
            **options
        )

    def __init__(self, protocol, host, port=None, **options):
        # For the possible options see http.client.HTTP(S)Connection documentation.
        if protocol not in self.CONNECTION_CLASS:
            raise ValueError(f"Invalid protocol {protocol!r}!")
        self.protocol = protocol
        self.connection_class = self.CONNECTION_CLASS[protocol]
        self.host = host
        self.port = self.DEFAULT_PORT[protocol] if port is None else port
        self.options = options

    @property
    def url(self):
        """ Get URL string. """
        is_default_port = self.port == self.DEFAULT_PORT[self.protocol]
        netloc = self.host if is_default_port else f"{self.host}:{self.port}"
        return f"{self.protocol}://{netloc}"

    def __call__(self):
        return HttpConnection(self.url, self.connection_class(
            host=self.host, port=self.port, **self.options
        ))


class Timestamp:
    """ Timestamp formatter and parser. """

    RE_ISO_8601_DATETIME_LONG = re.compile(
        r"^(\d{4,4})-(\d{2,2})-(\d{2,2})(?:"
        r"T(\d{2,2}):(\d{2,2})"
        r"(?::(\d{2,2})(?:[.,](\d{0,6})\d*)?)?"
        r"(Z|([+-]\d{2,2})(?::(\d{2,2}))?)?"
        r")?$"
    )

    @staticmethod
    def create(*args, **kwargs):
        """ Create new timestamp. """
        return datetime.datetime(*args, **kwargs, tzinfo=datetime.timezone.utc)

    @staticmethod
    def now():
        """ Get current timestamp. """
        return datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    def format(value):
        """ Format a tz-aware ISO 8601 date-time value. """
        return (
            value
            .astimezone(datetime.timezone.utc)
            .replace(tzinfo=None)
            .isoformat()
        ) + "Z"

    @classmethod
    def parse(cls, value):
        """Parse an ISO 8601 date-time value. The parser supports time-zones.
        """
        match = cls.RE_ISO_8601_DATETIME_LONG.match(value)
        if not match:
            raise ValueError("Invalid date-time input!")

        (
            year,
            month,
            day,
            hour,
            minute,
            sec,
            usec,
            tzone,
            tz_hour,
            tz_min,
        ) = match.groups()

        if tzone:
            if tzone == "Z":
                tz_obj = datetime.timezone.utc
            else:
                tz_obj = datetime.timezone(
                    offset=datetime.timedelta(
                        hours=int(tz_hour or 0),
                        minutes=int(tz_hour[0] + (tz_min or "0")),
                    ),
                    name=f"{tz_hour}:{tz_min or '00'}"
                )
        else:
            tz_obj = datetime.timezone.utc

        return datetime.datetime(
            int(year),
            int(month),
            int(day or 0),
            int(hour or 0),
            int(minute or 0),
            int(sec or 0),
            int(((usec or "") + "000000")[:6]),
            tz_obj,
        ).astimezone(datetime.timezone.utc)

Timestamp.DT_1970 = Timestamp.create(1970, 1, 1)


class Date:
    """ Date helpers. """

    @staticmethod
    def create(*args, **kwargs):
        """ Create new date. """
        return datetime.date(*args, **kwargs)

    @staticmethod
    def today():
        """ Get current UTC date. """
        return datetime.datetime.utcnow().date()

    @staticmethod
    def parse(value):
        """ Parse ISO date. """
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()


if __name__ == "__main__":
    App.run(*sys.argv)
