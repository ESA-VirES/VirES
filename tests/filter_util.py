#-------------------------------------------------------------------------------
#
#  Filter utilities
#
# Authors:  Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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

from itertools import izip
from numpy import array, empty, diff, concatenate, floor


class FilterInterface(object):
    """ Abstract filter interface. """

    def filter(self, data):
        """ Apply filter to the data. """
        raise NotImplementedError


class OrderBy(FilterInterface):
    """ Filter ordering records by the given variables. """

    @staticmethod
    def index(*var_data):
        """ Get get the permutation index. """
        return array([
            idx for _, idx
            in sorted((key, idx) for idx, key in enumerate(izip(*var_data)))
        ], dtype='int32')

    def filter(self, data):
        if self.variables:
            index = self.index(*[data[variable] for variable in self.variables])
            data = {key: var_data[index] for key, var_data  in data.items()}
        return data

    def __init__(self, *variables):
        self.variables = variables


class Filter(FilterInterface):
    """ Filter base class. """

    def predicate(self, var_data):
        """ Filter predicate. """
        raise NotImplementedError

    def filter(self, data):
        mask = self.predicate(data[self.variable])
        return {key: var_data[mask] for key, var_data  in data.items()}

    def __init__(self, variable):
        self.variable = variable


class EqualityFilter(Filter):
    """ Equality filter. """

    def predicate(self, var_data):
        return var_data == self.value

    def __init__(self, variable, value):
        Filter.__init__(self, variable)
        self.value = value


class RangeFilter(Filter):
    """ Closed scalar range filter. """

    def predicate(self, var_data):
        return (var_data >= self.min_value) & (var_data <= self.max_value)

    def __init__(self, variable, min_value, max_value):
        Filter.__init__(self, variable)
        self.min_value = min_value
        self.max_value = max_value

    def __str__(self):
        return "%s:%.12g,%.12g" % (self.variable, self.min_value, self.max_value)


class ComponentRangeFilter(RangeFilter):
    """ Vector component closed range filter. """

    def predicate(self, var_data):
        return RangeFilter.predicate(self, var_data[:, self.component])

    def __init__(self, variable, component, min_value, max_value):
        RangeFilter.__init__(self, variable, min_value, max_value)
        self.component = component

    def __str__(self):
        return "%s[%d]:%.12g,%.12g" % (
            self.variable, self.component, self.min_value, self.max_value
        )


class RangeFilterCO(RangeFilter):
    """ Half-open scalar range filter. """

    def predicate(self, var_data):
        """ Filter predicate. """
        return (var_data >= self.min_value) & (var_data < self.max_value)


class Subsampling(Filter):
    """ Simple sub-sampling filter. """

    @staticmethod
    def _quantize(data, step, offset, atol):
        return floor((data - offset + atol)/step).astype('int')

    @staticmethod
    def _find_steps(data, include_first=True):
        if len(data) > 0:
            return concatenate(
                ([bool(include_first)], diff(data).astype('bool'))
            )
        else:
            return empty(0, 'bool')

    def _predicate(self, data, offset):
        if offset is None:
            offset = data[0] if len(data) > 0 else 0.0
        return self._find_steps(
            self._quantize(data, self.step, offset, self.atol),
            include_first=True
        )

    def predicate(self, data):
        return self._predicate(data, self.offset)

    def filter(self, data):
        if self.step and self.step > 0:
            data = Filter.filter(self, data)
        return data

    def __init__(self, variable, step, offset=None, atol=0):
        Filter.__init__(self, variable)
        self.step = step
        self.offset = offset
        self.atol = atol # compensates truncation errors


class DailySubsampling(Subsampling):
    """ Daily sub-sampling filter emulating sub-sampling of the daily products.
    Note: MJD time is expected.
    """

    @classmethod
    def _split_by_days(cls, data):
        ranges = concatenate(
            ([1], diff(floor(data).astype('int')), [1])
        ).nonzero()[0]
        for i in xrange(len(ranges) - 1):
            yield data[ranges[i]:ranges[i+1]]

    def predicate(self, data):
        offset = self.offset
        segments = []
        for subset in self._split_by_days(data):
            segments.append(self._predicate(subset, offset))
            offset = None
        return concatenate(segments)
