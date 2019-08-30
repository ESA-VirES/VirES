#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Compare an original Swarm product in the CDF format with a CDF files produced
# by VirES.
#
# Author: Christian Schiller
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

from __future__ import print_function
import sys
import datetime
from numpy.testing import assert_equal
from spacepy import pycdf

LINE = '-------------------------------------------------------------'


def usage(argv):
    """ print help and usage info.
    """
    print(
        "Compare two CDF files, e.g., an original Swarm 1B product and "
        "a file downloaded from VirES"
    )
    print("Usage: ", argv[0], " <CDF-file>  <CDF-file>  [options]")
    print("    Options:")
    print("          -G|-g  --  also compare and show global CDF attributes.")
    print()
    exit()


def main(argv):
    """ Main routine
    """
    general_attrib = False
    first_fname = argv[1]
    second_fname = argv[2]

    if len(argv) == 4 and str.upper(argv[3]) == '-G':
        general_attrib = True
    try:
        first_file = pycdf.CDF(first_fname)
    except pycdf.CDFError: # as c:
        print("Sorry the input file is NOT a CDF-file:  ", first_fname, '\n')
        exit()
    try:
        second_file = pycdf.CDF(second_fname)
    except pycdf.CDFError: # as c:
        print("Sorry the input file is NOT a CDF-file:  ", second_fname, '\n')
        exit()

    # put the longer list first
    one, one_f, one_k, two, two_f, two_k = get_longer_list(
        first_file, first_fname, second_file, second_fname
    )

    msg = '['+now()+']\n'
    msg = msg+"Comparing the following CDF-Datasets ... \n"
    msg = msg+one_f+' <==> '+two_f+'\n'
    msg = msg+"Using as Baseline: "+one_f
    print_headline(msg)

    if general_attrib is True:
            # compare the basic attributes (dataset -> one)
        msg = "Comparing Basic Attributes ..."
        print_headline(msg)

        template = "{0:<24} | {1:^21} |  {2:<}"
        for key, value in one.attrs.items():
            try:
                is_equal = (str(value) == str(two.attrs[key])).all()
                print(template.format(key, "is equal --> ", str(is_equal)))
            except AttributeError:
                is_equal = (str(value) == str(two.attrs[key]))
                print(template.format(key, "is equal --> ", str(is_equal)))
            except KeyError:
                print(template.format(key, "only present in -->", one_f))

        print()
        print(LINE)

        for key, value in two.attrs.items():
            try:
                is_equal = (str(value) == str(one.attrs[key])).all()
                print(template.format(key, "is equal --> ", str(is_equal)))
            except AttributeError:
                is_equal = (str(value) == str(one.attrs[key]))
                print(template.format(key, "is equal --> ", str(is_equal)))
            except KeyError:
                print(template.format(key, "only present in -->", two_f))

    msg = "Analysing Keys ..."
    print_headline(msg)

    # get the common & uniq keys
    common, uniq_1, uniq_2 = get_com_uniq(one_k, two_k)
    print()
    print("Common Keys: \n", common)
    print("\nUnique Keys in: ", one_f, "\n", uniq_1)
    print("\nUnique Keys in: ", two_f, "\n", uniq_2)

    msg = "Comparing Datasets Names ... "
    print_headline(msg)

    # compare the keys
    template = "{0:<20} | {1:^21} |  {2:<}"
    for key in sorted(one.keys()):
        try:
            is_equal = arrays_are_equal(one[key][:], two[key][:])
            print(template.format(key, "is equal -->", str(is_equal)))
        except AttributeError:
            is_equal = (one[key][:] == two[key][:])
            print(template.format(key, "is equal -->", str(is_equal)))
        except ValueError:
            print(one[key], two[key], "-- has a PROBLEM")

        except KeyError:
            print(template.format(key, "only present in -->", one_f))

    msg = "Comparing Dataset Dimensions ..."
    print_headline(msg)

    template = "{0:<20} | {1:<15} | {2:^20} | {3:<15} |  {4:<} "
        # take the shorter list as the comparison basis
    for key, value in two.items():
        try:
            is_equal = (two[key].shape == one[key].shape).all()
            print(template.format(
                key, str(value.shape), "is equal -->", str(one[key].shape),
                str(is_equal)
            ))
        except AttributeError:
            is_equal = (two[key].shape == one[key].shape)
            print(template.format(
                key, str(value.shape), "is equal -->", str(one[key].shape),
                str(is_equal)
            ))
        except KeyError:
            print(template.format(key, "only present in -->", two_f, '', ''))

    msg = "Comparing Dataset Content ..."
    print_headline(msg)

    template = "{0:<20} | {1:^21} |  {2:<}"
    for key, value in two.items():
        try:
            two_dat = two[key][:]
            one_dat = one[key][:]
            is_equal = arrays_are_equal(two_dat, one_dat)
            print(template.format(key, "is equal -->", str(is_equal)))
        except AttributeError:
            is_equal = (two_dat == one_dat)
            print(template.format(key, "is equal -->", str(is_equal)))
        except KeyError:
            print(template.format(key, "only present in -->", two_f))

    first_file.close()
    second_file.close()

    print()
    print(" **** D O N E **** ")
    print()


def arrays_are_equal(array1, array2):
    """ Comparing arrays. NaNs are treated as equal. """
    try:
        assert_equal(array1, array2)
    except AssertionError:
        return False
    return True


def now():
    """ get a time string for messages/logging.
    """
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat("T") + "Z"


def print_headline(msg):
    """ print headlines
    """
    print()
    print(LINE)
    print(msg)
    print(LINE)


def get_longer_list(first_file, first_fname, second_file, second_fname):
    """ check length of list and put the longer one first
    """
    k_first = sorted(first_file.keys())
    k_second = sorted(second_file.keys())

    if len(k_first) < len(k_second):
        one = second_file
        one_f = second_fname
        one_k = k_second
        two = first_file
        two_f = first_fname
        two_k = k_first
    else:
        one = first_file
        one_f = first_fname
        one_k = k_first
        two = second_file
        two_f = second_fname
        two_k = k_second

    return one, one_f, one_k, two, two_f, two_k


def get_com_uniq(k_one, k_two):
    """ get common and unique keys from datasets
    """
    # get the common & unique keys
    common = set(k_one).intersection(k_two)
    uniq_1 = set(k_one).difference(k_two)
    uniq_2 = set(k_two).difference(k_one)
    com_1s = sorted(list(common))
    uniq_1s = sorted(list(uniq_1))
    uniq_2s = sorted(list(uniq_2))

    return com_1s, uniq_1s, uniq_2s


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] == '-h' or sys.argv[1] == '--help':
        usage(sys.argv)
    else:
        sys.exit(main(sys.argv))
