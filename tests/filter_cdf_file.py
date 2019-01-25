#!/usr/bin/env python

#
# Allows the filtering of Swarm products in CDF file format
#  - remove single/multiple parameters
#  - filter values of a single parameter as defined by range provided by the user
#    (this can be performed multiple times using the previous file as new input)
#

from __future__ import print_function
import sys
from os import remove
from os.path import basename, exists
from shutil import move
from tempfile import NamedTemporaryFile
from numpy import isin, lexsort, unique
from spacepy.pycdf import CDF
from util.time_util import parse_datetime, datetime


try:
    #pylint: disable=redefined-builtin,invalid-name
    # Python 2 compatibility
    input = raw_input
    range = xrange
except NameError:
    pass # Python 3 - do nothing


class AbortAction(Exception):
    """ Terminate current action. """
    pass

def usage(exename):
    """ print help
    """
    print("USAGE: %s <input> <output>" % basename(exename))
    print("\n".join([
        "DESCRIPTION:",
        "  This program filters content of an input CDF file and writes",
        "  the filtered output to a new CDF file.",
        "",
        "  This program is able to:",
        "    - remove one or more variables from the CDF file",
        "    - subset field values by user defined filer criteria",
        "    - sort records by one or more field values",
    ]))
    print()


def main(argv):
    """ main subroutine
    """
    if '-h' in argv[1:] or '--help' in argv[1:]:
        usage(argv[0])
        sys.exit()

    try:
        input_filename, output_filename = argv[1:3]
    except ValueError:
        print("ERROR: ")
        usage(argv[0])
        sys.exit(1)

    temp_filename = get_temporary_filename()
    try:
        remove(temp_filename)
        # copy input to a temporary file so that the inputs is preserved
        # open writeable temporary copy of the input file
        with CDF(temp_filename, input_filename) as cdf:
            filter_cdf(cdf)
        # move the temporary file to the desired output
        print("Writing output to %s" % output_filename)
        move(temp_filename, output_filename)
    finally:
        if exists(temp_filename):
            remove(temp_filename)


def filter_cdf(cdf_data):
    """ Filter the CDF file. """

    def _remove_fields(cdf_data):
        if not has_fields(cdf_data):
            print("Dataset is empty. No fields to be removed.")
            return cdf_data

        fields = ask_removed_fields(cdf_data)
        cdf_data = remove_fields(cdf_data, fields)

        print("Removed fields: ", ", ".join(fields))
        print("Remaining fields: ", ", ".join(cdf_data))

        cdf_data.attrs['REMOVED_VARIABLES'] = (
            list(cdf_data.attrs.get('REMOVED_VARIABLES', [])) + list(fields)
        )

        return cdf_data

    def _filter_values(cdf_data):
        if is_empty(cdf_data):
            print("Dataset is empty. No values to be filtered.")
            return cdf_data

        field, index, filter_ = ask_filter(cdf_data)
        cdf_data = subset_values(
            cdf_data, apply_filter(cdf_data, field, index, filter_)
        )

        formatted_field = field if index is None else "%s[%d]" % (field, index+1)
        formatted_filter = filter_.to_string(formatted_field)

        print("Applied filter: ", formatted_filter)

        cdf_data.attrs['APPLIED_FILTERS'] = (
            list(cdf_data.attrs.get('APPLIED_FILTERS', [])) + [formatted_filter]
        )

        return cdf_data

    def _sort_values(cdf_data):
        if is_empty(cdf_data):
            print("Dataset is empty. No values to be sorted.")
            return cdf_data

        sort_keys = ask_sort_keys(cdf_data)
        cdf_data = subset_values(cdf_data, sort_records(cdf_data, sort_keys))

        formatted_keys = [
            field if index is None else "%s[%d]" % (field, index+1)
            for field, index in sort_keys
        ]

        print("Sorted by: ", ", ".join(formatted_keys))

        cdf_data.attrs['SORTED_BY'] = formatted_keys + [
            key for key in cdf_data.attrs.get('SORTED_BY', [])
            if key not in formatted_keys
        ]

        return cdf_data

    assert_sane_data(cdf_data)
    while True:
        while True:
            answer = ask_choice(
                "Select an action to be performed:\n"
                "  f - remove fields Fields\n"
                "  v - filter records by field Values\n"
                "  s - sort records by field Values \n"
                "  w - write and exit\n"
                "  q - quit without saving\n"
                "[f/v/s/w/q]:"
            )
            if answer in ('q', 'f', 'v', 'w', 's'):
                break

        if answer == 'q':
            sys.exit()
        if answer == 'w':
            break
        elif answer == 'f':
            action = _remove_fields
        elif answer == 'v':
            action = _filter_values
        elif answer == 's':
            action = _sort_values
        else:
            continue

        try:
            cdf_data = action(cdf_data)
        except AbortAction:
            pass


def ask_filter(cdf_data):
    """ ask user for the filter and its parameters. """

    options = []
    for variable in cdf_data:
        data = cdf_data[variable][...]

        if data.ndim == 1:
            if variable == 'Spacecraft':
                filter_ = ChoiceFilter(unique(data))
            else:
                min_, max_ = data.min(), data.max()
                filter_ = RangeFilter(min_, max_)

            options.append((variable, None, filter_))
            print("%d : %-16s\t%s" % (
                len(options), variable, filter_.to_string(variable)
            ))

        elif data.ndim == 2:
            for index in range(data.shape[1]):
                formatted_variable = "%s[%s]" % (variable, index+1)
                min_, max_ = data[:, index].min(), data[:, index].max()
                filter_ = RangeFilter(min_, max_)
                options.append((variable, index, filter_))
                print("%d : %-16s\t%s" % (
                    len(options), formatted_variable,
                    filter_.to_string(formatted_variable)
                ))
        else:
            continue # ignore other dimensionality

    def _parse_value(value):
        value = int(value)
        if not 0 < value < len(options):
            raise ValueError
        return options[value - 1]

    def _parse_selection(choice):
        for value in choice.split()[:1]:
            return _parse_value(value)
        raise ValueError

    variable, index, filter_ = ask_selection((
        "Please choose one or more space separated numbers of the fields "
        "to be used as sort keys. (q to quit.): "
    ), _parse_selection)

    formatted_variable = (
        variable if index is None else "%s[%s]" % (variable, index+1)
    )

    if isinstance(filter_, RangeFilter):
        filter_ = ask_range_values(formatted_variable, filter_)
    elif isinstance(filter_, ChoiceFilter):
        filter_ = ask_choice_values(formatted_variable, filter_)
    else:
        raise RuntimeError

    return variable, index, filter_


def ask_range_values(variable, filter_):
    """ Ask user to insert range bounds. """
    def _parse_value(value):
        if not value.strip():
            return None
        return filter_.parse(value.upper())

    minimum = ask_selection((
        "Please enter minimum of the filter interval (%s, q to quit.): [%s]\n"
        % (filter_.to_string('value'), filter_.format_(filter_.minimum))
    ), _parse_value)

    if minimum is None:
        minimum = filter_.minimum

    maximum = ask_selection((
        "Please enter maximum of the filter interval (%s, q to quit.): [%s]\n"
        % (filter_.to_string('value'), filter_.format_(filter_.maximum))
    ), _parse_value)

    if maximum is None:
        maximum = filter_.maximum

    return RangeFilter(minimum, maximum)


def ask_choice_values(variable, filter_):
    """ Ask user to choose values. """
    options = sorted(filter_.values)

    def _parse_value(value):
        value = int(value)
        if not 0 < value <= len(options):
            raise ValueError
        return options[value - 1]

    def _parse_selection(choice):
        selection = [_parse_value(value) for value in set(choice.split())]
        if not selection:
            raise ValueError
        return selection

    for idx, value in enumerate(options, 1):
        print("%s : %s" % (idx, filter_.format_(value)))

    selection = ask_selection((
        "Please choose one or more space separated numbers of the %s values"
        "to be selected. (q to quit.): " % variable
    ), _parse_selection)

    return ChoiceFilter(selection)


def ask_sort_keys(cdf_data):
    """ ask user which keys should be used to sort the records. """
    options = []
    for variable in cdf_data:
        data = cdf_data[variable]
        ndim = len(data.shape)
        if ndim == 1:
            options.append((variable, None))
            print("%d : %s" % (len(options), variable))
        elif ndim == 2:
            for index in range(data.shape[1]):
                options.append((variable, index))
                print("%d : %s[%d]" % (len(options), variable, index+1))
        else:
            continue # ignore other dimensionality

    def _parse_value(value):
        value = int(value)
        if not 0 < value <= len(options):
            raise ValueError
        return options[value - 1]

    def _parse_selection(choice):
        selection = []
        for value in choice.split():
            parsed_value = _parse_value(value)
            if parsed_value not in selection:
                selection.append(parsed_value)
        return selection

    return ask_selection((
        "Please choose one or more space separated numbers of the fields "
        "to be used as sort keys. (q to quit.): "
    ), _parse_selection)


def ask_removed_fields(cdf_data):
    """ ask user which field should be removed
    """
    variables = sorted(cdf_data)

    for idx, variable in enumerate(variables, 1):
        print(idx, ':', variable)

    def _parse_value(value):
        value = int(value)
        if not 0 < value <= len(variables):
            raise ValueError
        return variables[value - 1]

    def _parse_selection(choice):
        return [_parse_value(value) for value in set(choice.split())]

    return ask_selection((
        "Please choose one or more space separated numbers of the fields "
        "to be removed and press enter. (q to quit.): "
    ), _parse_selection)


def sort_records(cdf_data, sort_keys):
    """ Get indices sorting the records by the given keys. """
    return lexsort([
        cdf_data[field][:] if index is None else cdf_data[field][:, index]
        for field, index in reversed(sort_keys)
    ])


def apply_filter(cdf_data, variable, index, filter_):
    """ Apply filter to the selected data and get indices of the matched
    elements.
    """
    data = cdf_data[variable][...]

    if data.ndim == 2:
        data = data[:, index]
    elif data.ndim != 1:
        raise ValueError("Unsupported number of data dimensions %d!" % data.ndim)

    selection = filter_(data).nonzero()[0]

    print("Number of samples matched by the filter:", selection.size)
    print("Number of samples removed by the filter:", data.size - selection.size)

    return selection


class Filter(object):
    """ Filter abstract base class. """

    def __init__(self, format_=None, parse=None):
        self.format_ = format_ or (lambda v: "%s" % v)
        self.parse = parse or (lambda v: v)

    @staticmethod
    def _get_formatter(value):
        if isinstance(value, datetime):
            return format_datetime
        if isinstance(value, float):
            return lambda v: "%.4g" % v
        return lambda v: "%s" % v

    @staticmethod
    def _get_parser(value):
        if isinstance(value, datetime):
            return parse_datetime
        if isinstance(value, int):
            return int
        if isinstance(value, float):
            return float
        return lambda v: v

    def __call__(self, data):
        raise NotImplementedError

    def to_string(self, variable):
        raise NotImplementedError

    def __str__(self):
        return self.to_string("?")


class ChoiceFilter(Filter):
    """ Range filter. """

    def __init__(self, values, format_=None):
        Filter.__init__(self)
        self.values = set(values)

    def __call__(self, data):
        return isin(data, list(self.values))

    def to_string(self, variable):
        return "%s IN (%s) " % (
            variable, ", ".join(self.format_(v) for v in self.values)
        )

class RangeFilter(Filter):
    """ Range filter. """

    def __init__(self, minimum, maximum, format_=None):
        Filter.__init__(
            self,
            format_=self._get_formatter(minimum),
            parse=self._get_parser(minimum)
        )
        self.minimum = minimum
        self.maximum = maximum

    def __call__(self, data):
        return (data >= self.minimum) & (data <= self.maximum)

    def to_string(self, variable):
        return "%s <= %s <= %s " % (
            self.format_(self.minimum), variable, self.format_(self.maximum)
        )


def subset_values(cdf_data, index):
    """ Subset the variables by keeping only the index values.
    """
    for variable in cdf_data:
        cdf_data[variable] = cdf_data[variable][...][index]
    return cdf_data


def remove_fields(cdf_data, variables):
    """ removes the chosen field(s) from the array
    """
    for variable in variables:
        try:
            cdf_data.pop(variable)
        except KeyError:
            print("ERROR - Failed to remove the %s field!", variable)

    return cdf_data


def ask_selection(message, choice_parser):
    """ Get parsed user selection. """
    while True:
        choice = ask_choice(message)

        if 'q' in choice:
            raise AbortAction

        try:
            selection = choice_parser(choice)
        except ValueError:
            print("Invalid selection. Try again ...")
            continue
        break
    return selection


def ask_choice(message):
    """ get input from user
    """
    return input(message).lower()


def has_fields(cdf_data):
    """ True if the dataset has no records. """
    return bool(list(cdf_data))


def is_empty(cdf_data):
    """ True if the dataset has no records. """
    for variable in cdf_data:
        return cdf_data[variable].shape[0] == 0
    return True


def assert_sane_data(cdf_data):
    """ Assert that the data are sane. """
    size = None
    for variable in cdf_data:
        shape = cdf_data[variable].shape
        if not shape:
            print(
                "ERROR: Cannot process a dataset with an empty field %s!"
                % variable
            )
            sys.exit(1)
        if size is None:
            size = shape[0]
            print("Number of records: %d" % size)
        elif size != shape[0]:
            print(
                "ERROR: Cannot process a dataset with varying number of records!"
            )
            sys.exit(1)


def get_temporary_filename():
    """ Get temporary filename. """
    prefix = basename(sys.argv[0])
    with NamedTemporaryFile(prefix=prefix, suffix='.cdf', delete=False) as ftmp:
        filename = ftmp.name
    return filename


def format_datetime(value):
    """ Forma datetime object to ISO-8601 date/time string.
    """
    return value.isoformat('T') + 'Z'


if __name__ == "__main__":
    sys.exit(main(sys.argv))
