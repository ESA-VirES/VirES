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
# Copyright (C) 2023-2024 EOX IT Services GmbH
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
# pylint: disable=missing-docstring
# pylint: disable=broad-exception-caught,bare-except,superfluous-parens
# pylint: disable=too-many-branches,too-many-statements

import sys
import re
import os
import os.path
import io
import collections
import logging
import datetime
import urllib.request
import email.utils
import numpy
from common import (
    LOG_LEVELS, init_console_logging, init_file_logging,
    cdf_open, CommandError,
    SPACEPY_NAME, SPACEPY_VERSION, LIBCDF_VERSION,
    GZIP_COMPRESSION, GZIP_COMPRESSION_LEVEL4,
    CDF_UINT1, CDF_UINT2, CDF_INT2, CDF_EPOCH, CDF_DOUBLE, CdfTypeEpoch,
)

ONE_DAY = datetime.timedelta(days=1)


class App:
    """ The app. """
    NAME = "download_kp"
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
            "[--temp-dir=<directory>]"
            "[--verbosity=<level>][--log-file=<path>][--log-level=<level>]", file=file
        )
        print("\n".join([
            "DESCRIPTION:",
            "  Download time series Kp values from source GFZ web API,",
            "  starting from the given start date until the latest available"
            "  date, and store them in one or more yearly CDF files.",
            "  The outputs are stored in the optional output directory",
            "  (current directory by default).",
            "  When requested, the old replaced indices are removed.",
            "  Optionally, a custom directory to hold intermediate temporary",
            "  files can be specified. By default, all temporary files",
            "  are held in the output directory. "
        ]), file=file)

    @classmethod
    def parse_inputs(cls, argv):
        """ Parse input arguments. """

        verbosity = logging.INFO
        log_file = None
        log_level = logging.INFO
        delete_old = False
        start_date = None
        output_dir = None
        temp_dir = None

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

        return {
            "start_date": start_date,
            "output_dir": output_dir,
            "temp_dir": temp_dir,
            "delete_old": delete_old,
            "verbosity": verbosity,
            "log_file": log_file,
            "log_level": log_level,
        }

    @classmethod
    def main(cls, start_date, output_dir=None, temp_dir=None, delete_old=False, **_):
        """ Main subroutine. """

        kp_store = KpProductStore(
            output_dir=output_dir,
            temp_dir=temp_dir,
        )
        kp_source = KpDataSource()

        ranges = cls.yield_request_ranges(start_date)

        chunks = KpDataSource.split_chunks_by_year(
            kp_source.retrieve_request_ranges(ranges)
        )

        chunks = kp_store.filter_unchanged_chunks(chunks)

        for chunk in chunks:
            kp_store.save_chunk(chunk)

        if delete_old:
            kp_store.delete_old()

    @staticmethod
    def yield_request_ranges(start_date, last_request_days=90):
        """ Yield request ranges. Yearly request ranges are made except for the
        last 90 days to get all non-definitive values in one request.
        """
        def _yield_year_request_ranges(start_date, end_date):
            """ Generate request aligned with year boundaries. """
            for year in reversed(range(start_date.year, (end_date - ONE_DAY).year + 1)):
                yield Date.create(year, 1, 1), min(Date.create(year + 1, 1, 1), end_date)

        end_date = Date.today() + ONE_DAY
        last_start = end_date - datetime.timedelta(days=last_request_days)
        last_start = max(last_start, start_date)
        last_start = Date.create(last_start.year, 1, 1)

        if last_start < end_date:
            yield last_start, end_date

        yield from _yield_year_request_ranges(start_date, last_start)


class KpProductStore:
    """ Product storage. """

    DEFAULT_OUTPUT_DIRECTORY = "."

    ID_TEMPLATE = (
        "GFZ_KP_{start:%Y%m%dT%H%M%S}_{end:%Y%m%dT%H%M%S}_"
        "{timestamp:%Y%m%dT%H%M%S}"
    )

    FILENAME_PATTERN = re.compile(
        r"^GFZ_KP_(?P<start>\d{8,8}T\d{6,6})"
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
            self.logger.info("Removing Kp data file %s ...", path)
            try:
                os.remove(path)
            except Exception as error:
                self.logger.error(
                    "Failed to remove Kp data file %s. %s", path, error
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
                old_data = KpProduct.load(filename)
            except:
                self.logger.error("Failed to read Kp data from %s!", filename, exc_info=True)
                return True # previous data cannot be loaded

            if not self._compare_data(chunk.data, old_data):
                self.logger.debug("Kp data has changed.")
                return True # previous are not equal

            self.logger.debug("Kp data has not changed.")
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

        self.logger.info("Saving Kp data to %s ...", filename)

        if os.path.exists(filename_tmp):
            os.remove(filename_tmp)

        try:
            KpProduct.save(filename_tmp, chunk.data, chunk.metadata)
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
        """ Yield existing Kp products in the given directory. """
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
        """ Compare Kp data. """
        if set(data1) != set(data2):
            raise ValueError("Dictionary keys must be the same!")
        for key in data1:
            if not numpy.array_equal(data1[key], data2[key], equal_nan=True):
                return False
        return True


class KpProduct:
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

    @classmethod
    def save(cls, filename, data, metadata):
        """ Save Kp data to a CDF file. """

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
                "REQUEST_URL": metadata["url"],
                "REQUESTED": _format_datetime(metadata["timestamp"]),
                **cls.CDF_GLOBAL_ATTRIBUTES,
                "CREATED": _format_datetime(Timestamp.now()),
                "CREATOR": cls.CDF_CREATOR,
            })
            _save_cdf_variable(
                cdf, "Timestamp", CDF_EPOCH, CdfTypeEpoch.encode(data["Timestamp"])
            )
            _save_cdf_variable(cdf, "Interval", CDF_UINT2, data["Interval"])
            _save_cdf_variable(cdf, "Kp", CDF_DOUBLE, data["Kp"])
            _save_cdf_variable(cdf, "ap", CDF_INT2, data["ap"])
            _save_cdf_variable(cdf, "Kp_Flag", CDF_UINT1, data["Kp_Flag"])

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
                "Interval": _load_cdf_data(cdf, "Interval"),
                "Kp": _load_cdf_data(cdf, "Kp"),
                "ap": _load_cdf_data(cdf, "ap"),
                "Kp_Flag": _load_cdf_data(cdf, "Kp_Flag"),
            }


class KpDataSource:
    """ Object representing Kp data source. """

    SOURCE_API_URL_TEMPLATE = (
        "https://kp.gfz-potsdam.de/kpdata?"
        "startdate={start:%Y-%m-%d}&enddate={end:%Y-%m-%d}&format=kp2"
    )

    class DataChunk(collections.namedtuple("DataChunk", ["data", "metadata"])):
        """ Data chunk object. """

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    @classmethod
    def _get_request_url(cls, start, end):
        return cls.SOURCE_API_URL_TEMPLATE.format(start=start, end=(end - ONE_DAY))

    def retrieve_request_ranges(self, ranges):
        """ Handle sequence of request time ranges. """
        for start, end in ranges:
            yield self.retrieve_data_range(start, end)

    def retrieve_data_range(self, start, end):
        """ Make request to the server and return the parsed and sanitized data
        for the given time range.
        """
        self.logger.info("Retrieving Kp data from %s to %s ...", start, end - ONE_DAY)

        url = self._get_request_url(start, end)
        metadata = {
            "url": url,
            "start": Timestamp.from_date(start),
            "end": Timestamp.from_date(end),
        }
        try:
            metadata["timestamp"] = Timestamp.now()
            with urllib.request.urlopen(url) as response:
                if "Last-Modified" in response.headers:
                    metadata["timestamp"] = email.utils.parsedate_to_datetime(
                        response.headers["Last-Modified"]
                    )
                elif "Date" in response.headers:
                    metadata["timestamp"] = email.utils.parsedate_to_datetime(
                        response.headers["Date"]
                    )
                data = KpData.sanitize(KpData.parse(
                    io.TextIOWrapper(response, encoding="utf8")
                ))
                metadata["data_start"], metadata["data_end"] = self.get_data_extent(data)
                return self.DataChunk(data=data, metadata=metadata)

        except urllib.request.HTTPError as error:
            self.logger.error(
                "Failed to retrieve Kp data from %s, reason: %s", url, error
            )
            raise

        except Exception:
            self.logger.error("Failed to read Kp data from %s", url, exc_info=True)
            raise

    @classmethod
    def split_chunks_by_year(cls, chunks):
        """ Split data to chunks aligned and not exceeding calendar years. """
        for chunk in chunks:
            years = chunk.data["Timestamp"].astype("datetime64[Y]")
            unique_years = numpy.unique(years)
            if len(unique_years) == 1:
                yield chunk
            else:
                for year in unique_years:
                    mask = years == year
                    start = cls.datetime64_to_datetime(year)
                    data = {
                        key: values[mask]
                        for key, values in chunk.data.items()
                    }
                    metadata = {
                        **chunk.metadata,
                        "start": start,
                        "end": min(
                            Timestamp.create(start.year + 1, 1, 1),
                            chunk.metadata["end"]
                        ),
                    }
                    metadata["data_start"], metadata["data_end"] = cls.get_data_extent(data)
                    yield cls.DataChunk(data=data, metadata=metadata)

    @classmethod
    def get_data_extent(cls, data):
        if data["Timestamp"].size == 0:
            return None, None
        return (
            cls.datetime64_to_datetime(data["Timestamp"][0]),
            cls.datetime64_to_datetime(data["Timestamp"][-1])
        )

    @staticmethod
    def datetime64_to_datetime(value):
        """ Convert numpy.datetime64 value to datetime.datetime object."""
        us1970 = int(value.astype("datetime64[us]").astype("int64"))
        return Timestamp.DT_1970 + datetime.timedelta(microseconds=us1970)


class KpData:
    """ Kp data parser. """

    KP_FIELDS = (
        "date", "hour_start", "hour_centre", "mjd1932_start", "mjd1932_centre",
        "kp", "ap", "definitive",
    )
    KP_DTYPES = (
        "datetime64", "float64", "float64", "float64", "float64",
        "float64", "int16", "int8",
    )
    KP_FIELD_TYPES = (
        str, str, str, float, float, float, float, float, int, int,
    )

    @classmethod
    def sanitize(cls, data):
        """ Sanitize the source Kp data. """
        # start of the interval in seconds from the day start
        interval_start = (
            data["hour_centre"] * 3600
        ).round().astype("timedelta64[s]")

        # length of the time-interval in seconds
        interval_duration = 2 * (
            data["hour_centre"] - data["hour_start"]
        )
        interval_duration[interval_duration < 0] += 24
        interval_duration = (interval_duration * 3600).round().astype("uint16")

        return {
            "Timestamp": data['date'] + interval_start,
            "Interval": interval_duration,
            "Kp": data["kp"],
            "ap": data["ap"],
            "Kp_Flag": (data["definitive"] == 0).astype("uint8"),
        }

    @classmethod
    def parse(cls, lines, comment="#"):
        """ Parse Kp API text response . """

        def _parse_kp_record(line):
            year, month, day, *fields = (
                type_(value) for type_, value in zip(cls.KP_FIELD_TYPES, line.split())
            )
            return (f"{year}-{month}-{day}", *fields)

        data = {field: [] for field in cls.KP_FIELDS}

        for line in lines:
            # strip commends and leading and trailing white-spaces
            line = line.partition(comment)[0].strip()
            if not line: # skip empty lines
                continue
            record = _parse_kp_record(line)
            for values, value in zip(data.values(), record):
                values.append(value)

        return {
            key: numpy.array(values, dtype=dtype)
            for dtype, (key, values) in zip(cls.KP_DTYPES, data.items())
        }


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
    def from_date(date, time=None):
        """ Create new timestamp from datetime.date and datetime.time objects.
        """
        return datetime.datetime.combine(
            date, time or datetime.time(), tzinfo=datetime.timezone.utc
        )

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
