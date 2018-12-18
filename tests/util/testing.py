#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Testing utilities.
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

from __future__ import print_function
from numpy import abs, nan, isnan, any
from numpy.testing import assert_allclose


def test_variables(data, reference, tested_variables):
    """ Test a dataset. """
    tests_count = 0
    tests_failed = 0

    for key, prm in tested_variables.items():
        if key in data:
            print("Testing %s ... " % key, end='')
            tests_failed += test_variable(data[key], reference[key], **prm)
            tests_count += 1

    print("%d of %d tests passed successfully." % (
        tests_count - tests_failed, tests_count
    ))
    if tests_failed:
        print("%d of %d tests failed!" % (tests_failed, tests_count))


def test_variable(data, reference, atol, uom, sanitize=None):
    """ Test single variable. """
    if sanitize is None:
        sanitize = lambda v, r: v

    data = sanitize(data, reference)
    reference = sanitize(reference, reference)
    mask = ~isnan(reference)

    if any(mask):
        max_deviation = abs(data[mask] - reference[mask]).max()
    else:
        max_deviation = nan

    try:
        assert_allclose(data, reference, atol=atol)
    except AssertionError as error:
        print(
            "FAILED: The result maximum deviation %.3g%s is not within the "
            "required %s%s absolute tolerance!" % (max_deviation, uom, atol, uom)
        )
        print(error)
        return True
    else:
        print(
            "PASSED: The result maximum deviation %.3g%s is within the required "
            "%s%s absolute tolerance." % (max_deviation, uom, atol, uom)
        )
        return False
