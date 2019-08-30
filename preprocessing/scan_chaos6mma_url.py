#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Scan the CHAOS-6-MMA URL and dump the download URLs
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

from __future__ import print_function
import sys
import re
from os.path import basename
from functools import partial
from contextlib import closing

try:
    # Python 3.x
    from html.parser import HTMLParser
    from urllib.request import urlopen
    from urllib.parse import urljoin
except ImportError:
    # Python 2.x
    from HTMLParser import HTMLParser
    from urllib2 import urlopen
    from urlparse import urljoin


HTTP_TIMEOUT = 60 # seconds
URL = "http://www.spacecenter.dk/files/magnetic-models/RC/MMA/"

RE_CHAOS6_MMA_FILENAME = re.compile(
    r"SW_OPER_MMA_CHAOS6_\d{8,8}T\d{6,6}_\d{8,8}T\d{6,6}_\d{4,4}\.cdf"
)


def get_ulrs(url, extract):
    """ Download HTML page from the URL and extract the product URLs.
    """
    with closing(urlopen(url, timeout=HTTP_TIMEOUT)) as handle:
        return [
            urljoin(handle.geturl(), item)
            for item in extract(handle)
        ]

def extract_chaos6_mma_products(file, select_applicable=True):
    """ Extract applicable CHAOS-6-MMA products from an index HTML file. """
    products = extract_urls(file, RE_CHAOS6_MMA_FILENAME)
    if select_applicable:
        products = select_mma_products(products)
    return products


def select_mma_products(products):
    """ From a list of all products filter the applicable subset. """
    def _filter(products):
        products_it = iter(sorted(products, reverse=True))
        last = next(products_it)
        yield last
        for product in products_it:
            if last[19:34] > product[35:50]:
                last = product
                yield last
    return list(reversed(list(_filter(products))))


def extract_urls(source, pattern=None):
    """ Extract URLs from an HTML stream. """
    parser = HrefExtractor(pattern)
    data = source.read()
    if isinstance(data, bytes):
        data = data.decode('UTF-8')
    parser.feed(data)
    return parser.hrefs


class HrefExtractor(HTMLParser):
    """ HTML parser exacting anchor href attribute values. """

    def __init__(self, pattern=None):
        HTMLParser.__init__(self)
        self.pattern = pattern
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        """ Extract href attributes values matched by a regex pattern. """
        if tag == 'a':
            href = self._get_href(attrs)
            if self.pattern is None or self.pattern.match(href):
                self.hrefs.append(href)

    @staticmethod
    def _get_href(attrs):
        for key, val in attrs:
            if key == "href":
                return val
        return None


if __name__ == "__main__":
    extract = extract_chaos6_mma_products
    if len(sys.argv) > 1 and sys.argv[1] in ('-a', '--all'):
        extract = partial(extract, select_applicable=False)
    for item in get_ulrs(URL, extract):
        print(item)
