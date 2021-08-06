#!/usr/bin/env python3
#-------------------------------------------------------------------------------
#
# leap second table
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
# pylint: disable=line-too-long,missing-docstring,too-many-arguments

from logging import getLogger
from pathlib import Path
from urllib.request import urlopen
from shutil import copyfileobj
from hashlib import sha1
from datetime import datetime, timedelta
from bisect import bisect_right

EPOCH_1900 = datetime(1900, 1, 1)
LOGGER = getLogger(__name__)
SOURCE_URL = 'https://www.ietf.org/timezones/data/leap-seconds.list'
LOCAL_PATH = Path(Path.home(), 'leap-seconds.list')


class LeapSecondError(Exception):
    pass


class ExpiredTable(LeapSecondError):
    pass


class IntergityError(LeapSecondError):
    pass


class ParsingError(LeapSecondError):
    pass


def main():
    try:
        leap_seconds = LeapSeconds()
    except Exception:
        LOGGER.error("Failed to read the leap-second table.", exc_info=True)
        return 1

    for key, value in leap_seconds.__dict__.items():
        padding = max(1, 18 - len(key))
        print(f"{key}:{' '*padding}{value}")

    print("leap_seconds:")
    print("  Timestamp            TAI offset")
    for timestamp, tai_offset in zip(leap_seconds.timestamps, leap_seconds.tai_offsets):
        print(f"  {timestamp}  {tai_offset}")

    return 0


class LeapSeconds():
    """ Leap seconds table class. """

    def __init__(self, local_path=LOCAL_PATH, source_url=SOURCE_URL):
        self.source_url = source_url
        self.local_path = Path(local_path)
        self.last_update = None
        self.expires = None
        self.sha1_digest = None
        self.timestamps = []
        self.tai_offsets = []
        self._read_leap_seconds()

    def find_utc_to_tai_offset(self, timestamp):
        """ Find UTC to TAI offset for the given timestamp. """
        idx = bisect_right(self.timestamps, timestamp) - 1
        if idx < 0:
            raise ValueError(
                f"Invalid timestamp! {timestamp} < {self.timestamps[0]}"
            )
        return self.tai_offsets[idx]

    def _read_leap_seconds(self):
        local_path = Path(self.local_path)
        file_already_exists = local_path.is_file()
        if not file_already_exists:
            LOGGER.info("Leap second table %s not found.", local_path)
            download(self.source_url, local_path)

        # read table and catch possible issues
        try:
            with open(local_path) as source:
                return self._parse_leap_seconds(source)
        except LeapSecondError as error:
            if not file_already_exists:
                # skip new download for a freshly downloaded table.
                raise
            LOGGER.warning("%s", error)

        # re-download the table in case of an issue
        download(self.source_url, local_path)
        with open(local_path) as source:
            return self._parse_leap_seconds(source)


    def _parse_leap_seconds(self, source):
        sha1_digest = ''
        expires = ''
        last_update = ''
        timestamps = []
        tai_offsets = []
        hash_ = sha1()
        line_no = 0
        try:
            for line_no, line in enumerate(source, 1):
                tag = line[:2].rstrip()
                if tag[:1] == "#":
                    if len(tag) > 1:
                        line = line[2:].strip()
                        if tag == "#$":
                            last_update = convert_timestamp(line)
                            hash_.update(line.encode('ascii'))
                        elif tag == "#@":
                            expires = convert_timestamp(line)
                            hash_.update(line.encode('ascii'))
                        elif tag == "#h":
                            sha1_digest = "".join(line.split())
                    continue
                line = line.partition("#")[0] # strip remaining comment
                line = line.rstrip() # strip trailing white-spaces
                if not line:
                    continue # skip blank lines
                timestamp, tai_offset = line.split()
                hash_.update(timestamp.encode('ascii'))
                hash_.update(tai_offset.encode('ascii'))
                timestamps.append(convert_timestamp(timestamp))
                tai_offsets.append(int(tai_offset))
        except (ValueError, TypeError):
            raise ParsingError(
                "line %d: Failed to parse the leap-second table!" % line_no
            ) from None

        if hash_.hexdigest() != sha1_digest:
            raise IntergityError(
                "The leap-second table has been corrupted. "
                "The content does not match the expected SHA1 "
                "checksum."
            )

        if datetime.utcnow().isoformat("T") > expires:
            raise ExpiredTable("The leap-second table is expired.")

        self.last_update = last_update or None
        self.expires = expires
        self.sha1_digest = sha1_digest
        self.timestamps = timestamps
        self.tai_offsets = tai_offsets


def convert_timestamp(timestamp):
    return (EPOCH_1900 + timedelta(seconds=int(timestamp))).isoformat("T")


def download(source_url, target_path):
    """ Simple URL download. """
    LOGGER.info("Downloading %s -> %s ...", source_url, target_path)
    with urlopen(source_url) as source:
        with open(target_path, "wb") as target:
            copyfileobj(source, target)


if __name__ == "__main__":
    import sys
    from common import setup_logging
    setup_logging()
    sys.exit(main())
