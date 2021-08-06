#!/usr/bin/env python3
#-------------------------------------------------------------------------------
#
# SP3c file-format reader
#
# This script contains a subroutine reading and parsing SP3 files.
# The data are read as they are. No conversions are applied.
#
# Known limitations:
# - the reader not parse the SP3 PE and VE records
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

import re
import sys
from decimal import Decimal
import warnings

GPS_TO_TAI_OFFSET = 19 # seconds (1980-01-06T00:00:00Z)


class SP3Error(ValueError):
    """ SP3 format parse exception. """


def main():
    """ Read SP3 file from standard input and print the parsed header and records.
    """
    header, records = read_sp3(sys.stdin)

    for key, value in header.items():
        padding = max(1, 18 - len(key))
        print(f"{key}:{' '*padding}{value}")

    for record in records:
        print(record)


RE_BLANKS = re.compile(r"^\s*$")

RE_SP3_HEADER = [
    re.compile(
        r"^(?P<version>#[a-c])(?P<flag>[PV])"
        r"(?P<year>\d\d\d\d) (?P<month> [1-9]|1[012]) (?P<day> [1-9]|[12][0-9]|3[01])"
        r" (?P<hour>[ 1][0-9]|2[0-3]) (?P<minute>[ 1-5][0-9]) (?P<second>(?:[ 1-5][0-9]|60)\.\d{8,8})"
        r" (?P<n_epoch>[ 0-9]{6,6}[0-9]) (?P<data>.{5,5}) (?P<crs>.{5,5})"
        r" (?P<orb_type>.{3,3}) (?P<agency>.{4,4})"
        r"\s*$"
    ),
    re.compile(
        r"^## (?P<gps_week>[ \d]{3,3}\d) (?P<week_seconds>[ \d]{5,5}\d\.\d{8,8})"
        r" (?P<epoch_interval>[ \d]{4,4}\d\.\d{8,8})"
        r" (?P<mjd>[ \d]{4,4}\d) (?P<dfrac>\d\.\d{13,13})"
        r"\s*$"
    ),
    re.compile(
        r"\+   (?P<n_sat>[ 1-7][0-9]|8[0-5])   "
        r"(?P<sat_01_id>.[ \d]\d)(?P<sat_02_id>.[ \d]\d)(?P<sat_03_id>.[ \d]\d)"
        r"(?P<sat_04_id>.[ \d]\d)(?P<sat_05_id>.[ \d]\d)(?P<sat_06_id>.[ \d]\d)"
        r"(?P<sat_07_id>.[ \d]\d)(?P<sat_08_id>.[ \d]\d)(?P<sat_09_id>.[ \d]\d)"
        r"(?P<sat_10_id>.[ \d]\d)(?P<sat_11_id>.[ \d]\d)(?P<sat_12_id>.[ \d]\d)"
        r"(?P<sat_13_id>.[ \d]\d)(?P<sat_14_id>.[ \d]\d)(?P<sat_15_id>.[ \d]\d)"
        r"(?P<sat_16_id>.[ \d]\d)(?P<sat_17_id>.[ \d]\d)\s*$"
    ),
    re.compile(
        r"\+        "
        r"(?P<sat_18_id>.[ \d]\d)(?P<sat_19_id>.[ \d]\d)(?P<sat_20_id>.[ \d]\d)"
        r"(?P<sat_21_id>.[ \d]\d)(?P<sat_22_id>.[ \d]\d)(?P<sat_23_id>.[ \d]\d)"
        r"(?P<sat_24_id>.[ \d]\d)(?P<sat_25_id>.[ \d]\d)(?P<sat_26_id>.[ \d]\d)"
        r"(?P<sat_27_id>.[ \d]\d)(?P<sat_28_id>.[ \d]\d)(?P<sat_29_id>.[ \d]\d)"
        r"(?P<sat_30_id>.[ \d]\d)(?P<sat_31_id>.[ \d]\d)(?P<sat_32_id>.[ \d]\d)"
        r"(?P<sat_33_id>.[ \d]\d)(?P<sat_34_id>.[ \d]\d)\s*$"
    ),
    re.compile(
        r"\+        "
        r"(?P<sat_35_id>.[ \d]\d)(?P<sat_36_id>.[ \d]\d)(?P<sat_37_id>.[ \d]\d)"
        r"(?P<sat_38_id>.[ \d]\d)(?P<sat_39_id>.[ \d]\d)(?P<sat_40_id>.[ \d]\d)"
        r"(?P<sat_41_id>.[ \d]\d)(?P<sat_42_id>.[ \d]\d)(?P<sat_43_id>.[ \d]\d)"
        r"(?P<sat_44_id>.[ \d]\d)(?P<sat_45_id>.[ \d]\d)(?P<sat_46_id>.[ \d]\d)"
        r"(?P<sat_47_id>.[ \d]\d)(?P<sat_48_id>.[ \d]\d)(?P<sat_49_id>.[ \d]\d)"
        r"(?P<sat_50_id>.[ \d]\d)(?P<sat_51_id>.[ \d]\d)\s*$"
    ),
    re.compile(
        r"\+        "
        r"(?P<sat_52_id>.[ \d]\d)(?P<sat_53_id>.[ \d]\d)(?P<sat_54_id>.[ \d]\d)"
        r"(?P<sat_55_id>.[ \d]\d)(?P<sat_56_id>.[ \d]\d)(?P<sat_57_id>.[ \d]\d)"
        r"(?P<sat_58_id>.[ \d]\d)(?P<sat_59_id>.[ \d]\d)(?P<sat_60_id>.[ \d]\d)"
        r"(?P<sat_61_id>.[ \d]\d)(?P<sat_62_id>.[ \d]\d)(?P<sat_63_id>.[ \d]\d)"
        r"(?P<sat_64_id>.[ \d]\d)(?P<sat_65_id>.[ \d]\d)(?P<sat_66_id>.[ \d]\d)"
        r"(?P<sat_67_id>.[ \d]\d)(?P<sat_68_id>.[ \d]\d)\s*$"
    ),
    re.compile(
        r"\+        "
        r"(?P<sat_69_id>.[ \d]\d)(?P<sat_70_id>.[ \d]\d)(?P<sat_71_id>.[ \d]\d)"
        r"(?P<sat_72_id>.[ \d]\d)(?P<sat_73_id>.[ \d]\d)(?P<sat_74_id>.[ \d]\d)"
        r"(?P<sat_75_id>.[ \d]\d)(?P<sat_76_id>.[ \d]\d)(?P<sat_77_id>.[ \d]\d)"
        r"(?P<sat_78_id>.[ \d]\d)(?P<sat_79_id>.[ \d]\d)(?P<sat_80_id>.[ \d]\d)"
        r"(?P<sat_81_id>.[ \d]\d)(?P<sat_82_id>.[ \d]\d)(?P<sat_83_id>.[ \d]\d)"
        r"(?P<sat_84_id>.[ \d]\d)(?P<sat_85_id>.[ \d]\d)\s*$"
    ),
    re.compile(
        r"\+\+       "
        r"(?P<sat_01_accuracy>[ \d][ \d]\d)(?P<sat_02_accuracy>[ \d][ \d]\d)(?P<sat_03_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_04_accuracy>[ \d][ \d]\d)(?P<sat_05_accuracy>[ \d][ \d]\d)(?P<sat_06_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_07_accuracy>[ \d][ \d]\d)(?P<sat_08_accuracy>[ \d][ \d]\d)(?P<sat_09_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_10_accuracy>[ \d][ \d]\d)(?P<sat_11_accuracy>[ \d][ \d]\d)(?P<sat_12_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_13_accuracy>[ \d][ \d]\d)(?P<sat_14_accuracy>[ \d][ \d]\d)(?P<sat_15_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_16_accuracy>[ \d][ \d]\d)(?P<sat_17_accuracy>[ \d][ \d]\d)\s*$"
    ),
    re.compile(
        r"\+\+       "
        r"(?P<sat_18_accuracy>[ \d][ \d]\d)(?P<sat_19_accuracy>[ \d][ \d]\d)(?P<sat_20_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_21_accuracy>[ \d][ \d]\d)(?P<sat_22_accuracy>[ \d][ \d]\d)(?P<sat_23_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_24_accuracy>[ \d][ \d]\d)(?P<sat_25_accuracy>[ \d][ \d]\d)(?P<sat_26_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_27_accuracy>[ \d][ \d]\d)(?P<sat_28_accuracy>[ \d][ \d]\d)(?P<sat_29_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_30_accuracy>[ \d][ \d]\d)(?P<sat_31_accuracy>[ \d][ \d]\d)(?P<sat_32_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_33_accuracy>[ \d][ \d]\d)(?P<sat_34_accuracy>[ \d][ \d]\d)\s*$"
    ),
    re.compile(
        r"\+\+       "
        r"(?P<sat_35_accuracy>[ \d][ \d]\d)(?P<sat_36_accuracy>[ \d][ \d]\d)(?P<sat_37_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_38_accuracy>[ \d][ \d]\d)(?P<sat_39_accuracy>[ \d][ \d]\d)(?P<sat_40_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_41_accuracy>[ \d][ \d]\d)(?P<sat_42_accuracy>[ \d][ \d]\d)(?P<sat_43_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_44_accuracy>[ \d][ \d]\d)(?P<sat_45_accuracy>[ \d][ \d]\d)(?P<sat_46_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_47_accuracy>[ \d][ \d]\d)(?P<sat_48_accuracy>[ \d][ \d]\d)(?P<sat_49_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_50_accuracy>[ \d][ \d]\d)(?P<sat_51_accuracy>[ \d][ \d]\d)\s*$"
    ),
    re.compile(
        r"\+\+       "
        r"(?P<sat_52_accuracy>[ \d][ \d]\d)(?P<sat_53_accuracy>[ \d][ \d]\d)(?P<sat_54_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_55_accuracy>[ \d][ \d]\d)(?P<sat_56_accuracy>[ \d][ \d]\d)(?P<sat_57_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_58_accuracy>[ \d][ \d]\d)(?P<sat_59_accuracy>[ \d][ \d]\d)(?P<sat_60_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_61_accuracy>[ \d][ \d]\d)(?P<sat_62_accuracy>[ \d][ \d]\d)(?P<sat_63_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_64_accuracy>[ \d][ \d]\d)(?P<sat_65_accuracy>[ \d][ \d]\d)(?P<sat_66_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_67_accuracy>[ \d][ \d]\d)(?P<sat_68_accuracy>[ \d][ \d]\d)\s*$"
    ),
    re.compile(
        r"\+\+       "
        r"(?P<sat_69_accuracy>[ \d][ \d]\d)(?P<sat_70_accuracy>[ \d][ \d]\d)(?P<sat_71_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_72_accuracy>[ \d][ \d]\d)(?P<sat_73_accuracy>[ \d][ \d]\d)(?P<sat_74_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_75_accuracy>[ \d][ \d]\d)(?P<sat_76_accuracy>[ \d][ \d]\d)(?P<sat_77_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_78_accuracy>[ \d][ \d]\d)(?P<sat_79_accuracy>[ \d][ \d]\d)(?P<sat_80_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_81_accuracy>[ \d][ \d]\d)(?P<sat_82_accuracy>[ \d][ \d]\d)(?P<sat_83_accuracy>[ \d][ \d]\d)"
        r"(?P<sat_84_accuracy>[ \d][ \d]\d)(?P<sat_85_accuracy>[ \d][ \d]\d)\s*$"
    ),
    re.compile(
        r"%c (?P<file_type>..) .. (?P<time_system>...) ... .... .... .... .... ..... ..... ..... .....\s*$"
    ),
    re.compile(
        r"%c .. .. ... ... .... .... .... .... ..... ..... ..... .....\s*$"
    ),
    re.compile(
        r"%f (?P<base_pv>[ \d]\d\.\d{7,7}) (?P<base_cr>[ \d]\d\.\d{9,9})"
        r" [ \d]\d\.\d{11,11} [ \d]\d\.\d{15,15}\s*$"
    ),
    re.compile(
        r"%f [ \d]\d\.\d{7,7} [ \d]\d\.\d{9,9} [ \d]\d\.\d{11,11} [ \d]\d\.\d{15,15}\s*$"
    ),
    re.compile(
        r"%i [ \d]{3,3}\d [ \d]{3,3}\d [ \d]{3,3}\d [ \d]{3,3}\d [ \d]{5,5}\d"
        r" [ \d]{5,5}\d [ \d]{5,5}\d [ \d]{5,5}\d [ \d]{8,8}\d\s*$"
    ),
    re.compile(
        r"%i [ \d]{3,3}\d [ \d]{3,3}\d [ \d]{3,3}\d [ \d]{3,3}\d [ \d]{5,5}\d"
        r" [ \d]{5,5}\d [ \d]{5,5}\d [ \d]{5,5}\d [ \d]{8,8}\d\s*$"
    ),
    re.compile(r"/\* (?P<comment_01>.{57,57})\s*$"),
    re.compile(r"/\* (?P<comment_02>.{57,57})\s*$"),
    re.compile(r"/\* (?P<comment_03>.{57,57})\s*$"),
    re.compile(r"/\* (?P<comment_04>.{57,57})\s*$"),
]

RE_SP3_RECORD = {
    "*": re.compile(
        r"\*  "
        r"(?P<year>\d\d\d\d) (?P<month> [1-9]|1[012]) (?P<day> [1-9]|[12][0-9]|3[01])"
        r" (?P<hour>[ 1][0-9]|2[0-3]) (?P<minute>[ 1-5][0-9]) (?P<second>(?:[ 1-5][0-9]|60)\.\d{8,8})"
        r"\s*$"
    ),
    "P": re.compile(
        r"P(?P<id>...)"
        r"(?P<px>[ \d-]{6,6}\d\.\d{6,6})(?P<py>[ \d-]{6,6}\d\.\d{6,6})(?P<pz>[ \d-]{6,6}\d\.\d{6,6})"
        r"(?P<clock>[ \d-]{6,6}\d\.\d{6,6})"
        r" (?P<px_sdev>[ \d]{2,2}) (?P<py_sdev>[ \d]{2,2}) (?P<pz_sdev>[ \d]{2,2})"
        r" (?P<clock_sdev>[ \d]{3,3})"
        r" (?P<clock_event_flag>.)(?P<clock_pred_flag>.)"
        r"  (?P<maneuver_flag>.)(?P<orbi_pred_flag>.)"
        r"\s*$"
    ),
    "V": re.compile(
        r"V(?P<id>...)"
        r"(?P<vx>[ \d-]{6,6}\d\.\d{6,6})(?P<vy>[ \d-]{6,6}\d\.\d{6,6})(?P<vz>[ \d-]{6,6}\d\.\d{6,6})"
        r"(?P<clock_roc>[ \d-]{6,6}\d\.\d{6,6})"
        r" (?P<vx_sdev>[ \d]{2,2}) (?P<vy_sdev>[ \d]{2,2}) (?P<vz_sdev>[ \d]{2,2})"
        r" (?P<clock_roc_sdev>[ \d]{3,3})"
        r"\s*$"
    ),
    "EO": re.compile(r"^EOF\s*$")
}

SP3_RECORD_TYPES = {
    'px': Decimal,
    'py': Decimal,
    'pz': Decimal,
    'vx': Decimal,
    'vy': Decimal,
    'vz': Decimal,
    'clock': Decimal,
    'clock_roc': Decimal,
    'px_sdev': int,
    'py_sdev': int,
    'pz_sdev': int,
    'vx_sdev': int,
    'vy_sdev': int,
    'vz_sdev': int,
    'clock_sdev': int,
    'clock_roc_sdev': int,
}


def read_sp3(source):
    source = _LineReader(source)
    header = read_sp3_header(source)
    records = read_sp3_records(source)
    return header, records


def read_sp3_records(source):
    """ Generator reading and parsing SP3 records from
    the input file stream.
    """
    try:
        yield from _read_sp3_records(source)
    except (ValueError, TypeError):
        raise SP3Error(
            "line %d: Failed to parse the SP3 record!" % source.line
        ) from None


def read_sp3_header(source):
    """ Read and parse SP3 header from the input file
    stream.
    """
    try:
        return _read_sp3_header(source)
    except (ValueError, TypeError):
        raise SP3Error(
            "line %d: Failed to parse the SP3 header!" % source.line
        ) from None


def _read_sp3_records(source):
    """ Generator reading and parsing SP3 records from
    the input file stream.
    """
    def _refine_record(data):
        return {
            key: SP3_RECORD_TYPES.get(key, str)(value)
            for key, value in data.items()
            if not RE_BLANKS.match(value)
        }

    def _break_spacecrafts(timestamp, data):
        for record in data.values():
            yield {"timestamp": timestamp, **record}

    eof = False
    timestamp = None
    data = {}

    for line in source:
        record_type = line[:2]
        if record_type[0] in ("P", "V", "*"):
            record_type = record_type[0]
        try:
            record = _match(RE_SP3_RECORD[record_type], line)
        except KeyError:
            warnings.warn(f"Unsupported {record_type} record ignored.")
            continue
        if record_type == '*': # timestamp
            if timestamp:
                yield from _break_spacecrafts(timestamp, data)
            timestamp = _build_timestamp(**record)
            data = {}
        elif record_type == "EO":
            eof = True
            break
        else:
            record = _refine_record(record)
            tmp = data.get(record['id'])
            if tmp:
                tmp.update(record)
            else:
                data[record['id']] = record

    if timestamp:
        yield from _break_spacecrafts(timestamp, data)

    if not eof:
        warnings.warn("EOF file terminator not found!")


def _read_sp3_header(source):
    """ Read and parse SP3 header from the input file
    stream.
    """
    header = {}
    for pattern in RE_SP3_HEADER:
        header.update(_match(pattern, next(source)))

    n_sat = int(header.pop('n_sat'))

    header.update({
        'start_time': _build_timestamp(
            year=header.pop('year'),
            month=header.pop('month'),
            day=header.pop('day'),
            hour=header.pop('hour'),
            minute=header.pop('minute'),
            second=header.pop('second'),
        ),
        'n_epoch': int(header.pop('n_epoch')),
        'gps_week': int(header.pop('gps_week')),
        'week_seconds': Decimal(header.pop('week_seconds')),
        'epoch_interval': Decimal(header.pop('epoch_interval')),
        'mjd': int(header.pop('mjd')),
        'dfrac': Decimal(header.pop('dfrac')),
        'base_pv': Decimal(header.pop('base_pv')),
        'base_cr': Decimal(header.pop('base_cr')),
        'n_sat': n_sat,
        'sat_id': [
            header.pop(f'sat_{i:02d}_id')
            for i in range(1, 86)
        ][:n_sat],
        'sat_accuracy': [
            int(header.pop(f'sat_{i:02d}_accuracy'))
            for i in range(1, 86)
        ][:n_sat],
        'comments': [
            header.pop(f'comment_{i:02d}')
            for i in range(1, 5)
        ],
    })
    return header


def _match(pattern, value):
    match = pattern.match(value)
    if match:
        return match.groupdict()
    raise ValueError("Input value not matched!")


def _build_timestamp(year, month, day, hour, minute, second):
    def _zero_pad(value):
        return value.replace(' ', '0')
    return (
        f"{_zero_pad(year)}-{_zero_pad(month)}-{_zero_pad(day)}"
        f"T{_zero_pad(hour)}:{_zero_pad(minute)}:{_zero_pad(second)}"
    )


class _LineReader():
    def __init__(self, file):
        self._iter = enumerate(file, 1)
        self._line = 0

    def __iter__(self):
        return self

    def __next__(self):
        self._line, value = next(self._iter)
        return value

    @property
    def line(self):
        """ Get line number of the last read record. """
        return self._line


if __name__ == "__main__":
    main()
