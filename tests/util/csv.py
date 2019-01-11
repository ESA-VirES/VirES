#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# VirES CVS parser
#
# Author: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
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

import json
from numpy import asarray
from io import open
try:
    # Python 2.7 compatibility
    from string import maketrans
except ImportError:
    maketrans = str.maketrans

PARSE_ARRAY_TRANS = maketrans("{;}", "[,]")


def parse_array(value):
    """ Parse float array object. """
    return json.loads(
        str(value).translate(maketrans("{;}", "[,]")).replace("nan", "NaN")
    )


def load_csv(filename, value_parsers=None, default_value_parser=None):
    """ Load CVS file from a file. """
    with open(filename, encoding="ascii") as source:
        return parse_csv(source, value_parsers, default_value_parser)


def parse_csv(source, value_parsers=None, default_value_parser=None):
    """ Parse CVS file from a file object. """

    if not default_value_parser:
        default_value_parser = parse_array

    if not value_parsers:
        value_parsers = {}

    def _wrap_parser(parser):
        def _wrap(variable, value):
            try:
                return parser(value)
            except ValueError as exc:
                raise ValueError(
                    "%s: %s\n%s" % (variable, value, exc)
                )
        return _wrap

    def _parse_csv(source):
        header = next(source)
        types = [
            _wrap_parser(value_parsers.get(variable, default_value_parser))
            for variable in header
        ]
        data = {variable: [] for variable in header}
        for record in source:
            for variable, value, type_ in zip(header, record, types):
                data[variable].append(type_(variable, value))
        return data

    def _split_records(lines):
        for line in lines:
            yield line.rstrip().split(",")

    def _to_arrays(data):
        return dict((key, asarray(value)) for key, value in data.items())

    return _to_arrays(_parse_csv(_split_records(source)))
