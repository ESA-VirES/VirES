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

from os import rename, remove
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


class IntergityError(LeapSecondError):
    pass


class ParsingError(LeapSecondError):
    pass


def load_leap_seconds(local_path=LOCAL_PATH, source_url=SOURCE_URL):
    """ Load leap seconds table. """

    def _load_table(path):
        with open(path, "rb") as file_:
            return LeapSeconds(file_, source_url=source_url)

    def _download_new_table(path):
        tmp_path = Path(path.parent, path.name + ".tmp")
        try:
            download(source_url, tmp_path)
            leap_seconds = _load_table(tmp_path)
        except:
            if tmp_path.exists():
                LOGGER.debug("Removing %s ...", tmp_path)
                remove(tmp_path)
            raise
        else:
            LOGGER.debug("Moving %s -> %s ... ", tmp_path, path)
            rename(tmp_path, path)
            return leap_seconds

        return leap_seconds

    leap_seconds = None

    try:
        leap_seconds = _load_table(local_path)
    except FileNotFoundError:
        LOGGER.debug("The cached leap second table %s not found.", local_path)
    except LeapSecondError as error:
        LOGGER.warning("%s", error)
    else:
        if not leap_seconds.is_expired:
            return leap_seconds
        LOGGER.warning("The cached leap seconds table is expired.")

    try:
        leap_seconds = _download_new_table(local_path)
    except Exception as error:
        LOGGER.error("%s", error)
        if not leap_seconds:
            raise
        LOGGER.warning("Defaulting to the expired cached leap seconds table.")

    return leap_seconds


class LeapSeconds():
    """ Leap-seconds table class. """

    def __init__(self, source, **extra_attrs):
        """ Load leap seconds from a file-like object. """

        self.__dict__.update(extra_attrs)

        records, info = parse_leap_seconds_table(source)

        self.expires = info.get('expires')
        self.last_update = info.get('last_update')
        self.sha1_digest = info.get('sha1_digest')
        self.timestamps = [value for value, _ in records]
        self.tai_offsets = [value for _, value in records]

    def find_utc_to_tai_offset(self, timestamp):
        """ Find UTC to TAI offset for the given timestamp. """
        idx = bisect_right(self.timestamps, timestamp) - 1
        if idx < 0:
            raise ValueError(
                f"Invalid timestamp! {timestamp} < {self.timestamps[0]}"
            )
        return self.tai_offsets[idx]

    @property
    def is_expired(self):
        return (
            self.expires and datetime.utcnow().isoformat("T") > self.expires
        )


def parse_leap_seconds_table(source):

    hash_ = sha1()
    records = []
    info = {}

    try:
        for line_no, tag, record in _read_records(source):
            if not tag:
                _update_digest(hash_, record)
                timestamp, tai_offset = _decode_record(record)
                records.append((
                    convert_timestamp(timestamp),
                    int(tai_offset),
                ))
            elif tag == b"$":
                _update_digest(hash_, record)
                timestamp, = _decode_record(record)
                info['last_update'] = convert_timestamp(timestamp)
            elif tag == b"@":
                _update_digest(hash_, record)
                timestamp, = _decode_record(record)
                info['expires'] = convert_timestamp(timestamp)
            elif tag == b"h":
                info['sha1_digest'] = "".join(
                    f"{int(item, 16):08x}" for item in _decode_record(record)
                )
    except (ValueError, TypeError):
        raise ParsingError(
            "line %d: Failed to parse the leap-second table!" % line_no
        ) from None

    sha1_digest = info.get('sha1_digest')

    if not sha1_digest:
        raise IntergityError("Failed to parse the SHA1 checksum.")

    if hash_.hexdigest() != sha1_digest:
        raise IntergityError(
            "The leap-second table has been corrupted. "
            "The content does not match the expected SHA1 "
            "checksum."
        )

    return records, info


def _read_records(source):
    for line_no, line in enumerate(source, 1):
        if line[:1] == b"#":
            tag = line[1:2].rstrip()
            if tag: # metadata
                yield line_no, tag, line[2:].strip().split()
            continue
        line = line.partition(b"#")[0] # strip remaining comment
        line = line.rstrip() # strip trailing white-spaces
        if not line:
            continue # skip blank lines
        yield line_no, None, line.strip().split()


def _update_digest(digest, record):
    for item in record:
        digest.update(item)


def _decode_record(record):
    return [item.decode('ascii') for item in record]


def convert_timestamp(timestamp):
    return (EPOCH_1900 + timedelta(seconds=int(timestamp))).isoformat("T")


def download(source_url, target_path):
    """ Simple URL download. """
    LOGGER.info("Downloading %s -> %s ...", source_url, target_path)
    with urlopen(source_url) as source:
        with open(target_path, "xb") as target:
            copyfileobj(source, target)


def main():
    try:
        leap_seconds = load_leap_seconds()
    except Exception:
        LOGGER.error("Failed to read the leap-second table.", exc_info=True)
        return 1

    for key in ["expires", "last_update", "sha1_digest"]:
        value = getattr(leap_seconds, key)
        padding = max(1, 18 - len(key))
        print(f"{key}:{' '*padding}{value}")

    print("  Timestamp            TAI offset")
    for timestamp, tai_offset in zip(leap_seconds.timestamps, leap_seconds.tai_offsets):
        print(f"  {timestamp}  {tai_offset}")

    return 0


if __name__ == "__main__":
    import sys
    from common import setup_logging
    setup_logging()
    sys.exit(main())
