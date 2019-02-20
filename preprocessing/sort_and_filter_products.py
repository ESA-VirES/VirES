#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Sort and filter products passed from standard input.
#
# Author: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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
#pylint: disable=missing-docstring

from __future__ import print_function
import sys
import re
from os.path import basename
from collections import namedtuple
from bisect import bisect_left


Product = namedtuple('Product', ['start', 'end', 'baseline', 'version', 'path'])


RE_PRODUCT_NAME = re.compile(
    r"^([A-Z][A-Z_0-9]*)_(\d{8,8}T\d{6,6})_(\d{8,8}T\d{6,6})_(\d{2,2})(\d{2,2})"
    r"(?:_([A-Z][A-Z_0-9]*))?\.([A-Za-z0-9]{3,3})"
)


class CommandError(Exception):
    pass


def check_inputs(argv):
    invert_filter = False
    filename_pattern = ".+"
    ignore_extension = False
    allow_overlaps = False
    latest_baseline = False

    it_argv = iter(argv)
    for arg in it_argv:
        if arg in ('-v', '--invert'):
            invert_filter = True
        elif arg in ('-i', '--ignore-extension'):
            ignore_extension = True
        elif arg in ('-a', '--allow-overlaps'):
            allow_overlaps = True
        elif arg in ('-l', '--latest-baseline'):
            latest_baseline = True
        elif arg == '--':
            break
        else:
            filename_pattern = arg

    for arg in it_argv:
        filename_pattern = arg

    return {
        "invert_filter": invert_filter,
        "filename_pattern": re.compile(filename_pattern),
        "ignore_extension": ignore_extension,
        "allow_overlaps": allow_overlaps,
        "latest_baseline": latest_baseline,
    }


def main(invert_filter, filename_pattern, ignore_extension, allow_overlaps,
         latest_baseline):
    filtered_products = filter_products(
        read_products(sys.stdin, filename_pattern, ignore_extension),
        invert_filter, allow_overlaps, latest_baseline,
    )

    for path in filtered_products:
        print(path)


def filter_products(items, invert_filter, allow_overlaps, latest_baseline):
    filters = []

    if latest_baseline:
        filters.append(filter_latest_baseline_only)

    if not allow_overlaps:
        filters.append(filter_latest_nonoverlapping)

    accepted, rejected = list(items), []

    for filter_ in filters:
        accepted, rejected_tmp = filter_(accepted)
        rejected += rejected_tmp

    key = lambda v: (v.start, v.end, v.baseline, v.version)
    for item in sorted(rejected if invert_filter else accepted, key=key):
        yield item.path


def read_products(source, filename_pattern, ignore_extension=False):
    expected_signature = None

    for path in (item.strip() for item in source):
        filename = basename(path)
        if filename_pattern.match(filename) is None:
            continue
        match = RE_PRODUCT_NAME.match(filename)
        if match is None:
            continue
        (
            product_type, start_time, end_time, baseline, version, suffix,
            extension,
        ) = match.groups()

        # assert constant file signature
        signature = (product_type, suffix or "", extension)
        if not expected_signature:
            expected_signature = signature
        else:
            signature_differs = (
                expected_signature[:2] != signature[:2]
            ) if ignore_extension else (
                expected_signature != signature
            )
            if signature_differs:
                raise CommandError(
                    "Mixed file signature! Probably mixed product types. "
                    "%s*%s.%s != %s*%s.%s" % (expected_signature + signature)
                )

        yield Product(start_time, end_time, baseline, version, path)


def filter_latest_baseline_only(items):
    """ Filter latest baseline only products. """
    if not items:
        return [], [] # early exit for an empty items list
    latest_baseline = max(item.baseline for item in items)
    accepted, rejected = [], []
    for item in items:
        (
            accepted if item.baseline == latest_baseline else rejected
        ).append(item)
    return accepted, rejected


def filter_latest_nonoverlapping(items):
    """ Filter latest non-overlapping products. """
    sorted_intervals = SortedItervals()
    rejected = []
    key = lambda v: (v.baseline, v.version, v.start, v.end)
    for item in sorted(items, key=key, reverse=True):
        rejected.extend(sorted_intervals.fill_in(item.start, item.end, item))
    return list(sorted_intervals), list(reversed(rejected))


class SortedItervals(object):

    def __init__(self):
        self.ranges = []

    def __iter__(self):
        return (payload for _, _, payload in self.ranges)

    def __getitem__(self, slice_):
        if isinstance(slice_, int):
            _, _, payload = self.ranges[slice_]
            return payload
        return [payload for _, _, payload in self.ranges[slice_]]

    def select(self, start, end):
        """ Select registered items intersected by the given time range. """
        idx_start, idx_stop = self._select_range(start, end)
        return self[idx_start:idx_stop]

    def replace(self, start, end, payload):
        """ Insert an item into the list replacing any overlapping items
        and return a list of the removed items.
        """
        idx_start, idx_stop = self._select_range(start, end)
        removed = self[idx_start:idx_stop]
        if removed:
            self.ranges = (
                self.ranges[:idx_start] + [
                    (start, end, payload)
                ] + self.ranges[idx_stop:]
            )
        else:
            self.ranges.insert(idx_start, (start, end, payload))
        return removed

    def fill_in(self, start, end, payload):
        """ Insert an item into the list filling in a gap
        and return a list which is either empty (item inserted)
        or it contains the inserted item (item not inserted).
        """
        idx_start, idx_stop = self._select_range(start, end)
        if idx_stop > idx_start:
            removed = [payload]
        else:
            self.ranges.insert(idx_start, (start, end, payload))
            removed = []

        return removed

    def _select_range(self, start, end):
        idx_start = max(bisect_left(self.ranges, (start,)) - 1, 0)
        idx_stop = min(bisect_left(self.ranges, (end,)) + 2, len(self.ranges))

        while idx_start < idx_stop:
            if self.ranges[idx_start][1] >= start:
                break
            idx_start += 1

        while idx_start < idx_stop:
            if self.ranges[idx_stop-1][0] <= end:
                break
            idx_stop -= 1

        return (idx_start, idx_stop)


if __name__ == "__main__":
    try:
        sys.exit(main(**check_inputs(sys.argv[1:])))
    except CommandError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        sys.exit(1)
