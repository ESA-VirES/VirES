#-------------------------------------------------------------------------------
#
# VirES integration tests - WPS utilities
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
# pylint: disable=missing-docstring

from __future__ import print_function
import sys
from time import sleep
import xml.etree.ElementTree as ElementTree
import json
from contextlib import closing
try:
    # Python 2.7 compatibility
    from urllib2 import urlopen, Request, HTTPError
except ImportError:
    from urllib.request import urlopen, Request, HTTPError
from jinja2 import Environment, FileSystemLoader
from .csv import parse_csv
from .cdf import parse_cdf, read_time_as_mjd2000

try:
    from service import SERVICE_URL, HEADERS
except ImportError:
    SERVICE_URL = "http://127.0.0.1:80/ows"
    HEADERS = []

JINJA2_ENVIRONMENT = Environment(loader=FileSystemLoader("./templates"))
JINJA2_ENVIRONMENT.filters.update(
    d2s=lambda d: d.isoformat("T") + "Z",
    l2s=lambda l: ", ".join(str(v) for v in l),
    o2j=json.dumps,
)

WPS_STATUS = {
    "{http://www.opengis.net/wps/1.0.0}ProcessAccepted": "ACCEPTED",
    "{http://www.opengis.net/wps/1.0.0}ProcessFailed": "FAILED",
    "{http://www.opengis.net/wps/1.0.0}ProcessStarted": "STARTED",
    "{http://www.opengis.net/wps/1.0.0}ProcessSucceeded": "FINISHED",
}


class WpsException(Exception):
    def __init__(self, code, locator, text):
        Exception.__init__(
            self, "WPS Process Failed!\n%s [%s]: %s" % (code, locator, text)
        )


class HttpMixIn(object):
    url = SERVICE_URL

    @staticmethod
    def retrieve(request, parser):
        try:
            with closing(urlopen(request)) as file_in:
                return parser(file_in)
        except HTTPError as error:
            print(error.read())
            raise

    @staticmethod
    def iter_decoded(source):
        for line in source:
            yield line.decode('UTF-8')


class WpsPostRequestMixIn(HttpMixIn):
    url = SERVICE_URL
    headers = {"Content-Type": "application/xml"}
    headers.update(HEADERS)
    template_source = None
    extra_template_params = {}

    @property
    def template(self):
        return self.get_template(self.template_source)

    @staticmethod
    def get_template(source):
        return JINJA2_ENVIRONMENT.get_template(source)

    def get_request(self, **template_params):
        template_params.update(self.extra_template_params)
        return self.template.render(**template_params).encode('utf-8')

    def get_response(self, parser, request):
        return self.retrieve(
            Request(self.url, request, self.headers), parser
        )


class WpsAsyncPostRequestMixIn(WpsPostRequestMixIn):
    process_name = "vires:fetch_filtered_data_async"
    output_name = "output"
    template_list_jobs = "vires_list_jobs.xml"
    template_remove_job = "vires_remove_job.xml"
    extra_template_params = {"response_type": "text/csv"}

    def get_response(self, parser, request):
        execute_response = self.retrieve(
            Request(self.url, request, self.headers),
            ElementTree.parse
        )
        status_url = execute_response.getroot().attrib["statusLocation"]

        while True:
            status = self.parse_process_status(execute_response)

            if status == "FINISHED":
                break

            if status == "FAILED":
                self.delete_all_async_jobs()
                self.raise_process_exception(execute_response)

            execute_response = self.retrieve(
                Request(status_url, None, self.headers),
                ElementTree.parse
            )
            status_url = execute_response.getroot().attrib["statusLocation"]
            sleep(0.1)

        output_url = self.extract_output_reference(
            execute_response, self.output_name
        )

        response = self.retrieve(Request(output_url, None, self.headers), parser)
        self.delete_all_async_jobs()
        return response

    @staticmethod
    def extract_output_reference(xml, identifier):
        root = xml.getroot()
        wps_outputs = root.find("{http://www.opengis.net/wps/1.0.0}ProcessOutputs")
        for elm in wps_outputs.findall("./{http://www.opengis.net/wps/1.0.0}Output"):
            elm_id = elm.find("./{http://www.opengis.net/ows/1.1}Identifier")
            if elm_id is not None and identifier == elm_id.text:
                elm_reference = elm.find(
                    "./{http://www.opengis.net/wps/1.0.0}Reference"
                )
                return elm_reference.attrib["href"]
        return None

    @staticmethod
    def raise_process_exception(xml):
        elm_exception = xml.find(".//{http://www.opengis.net/ows/1.1}Exception")
        locator = elm_exception.attrib["locator"]
        exception_code = elm_exception.attrib["exceptionCode"]
        elm_exception_text = elm_exception.find(
            "{http://www.opengis.net/ows/1.1}ExceptionText"
        )
        exception_text = elm_exception_text.text
        raise WpsException(exception_code, locator, exception_text)

    @staticmethod
    def parse_process_status(xml):
        root = xml.getroot()
        elm_status = root.find("{http://www.opengis.net/wps/1.0.0}Status")
        if elm_status is None:
            # status not found
            return None

        for elm in elm_status:
            return WPS_STATUS[elm.tag]

    def delete_all_async_jobs(self):
        for item in self.list_async_jobs():
            if not self.remove_async_job(item["id"]):
                print("Failed to remove asynchronous job %s (%s)!" % (
                    item["id"], item["url"]
                ))

    def list_async_jobs(self):
        request = self.get_template(self.template_list_jobs).render()
        request = request.encode('utf-8')
        job_list = self.retrieve(
            Request(self.url, request, self.headers), json.load
        )
        return job_list.get(self.process_name, [])

    def remove_async_job(self, job_id):
        request = self.get_template(self.template_remove_job).render(
            job_id=job_id
        ).encode('utf-8')
        return self.retrieve(
            Request(self.url, request, self.headers), json.load
        )


class CsvRequestMixIn(object):
    extra_template_params = {"response_type": "text/csv"}
    csv_variable_parsers = {
        'id': str,
        'Spacecraft': str,
    }

    @classmethod
    def csv_parser(cls, file_in):
        if sys.version_info[0]:
            file_in = cls.iter_decoded(file_in)
        return parse_csv(file_in, cls.csv_variable_parsers)

    def get_parsed_response(self, request):
        return self.get_response(self.csv_parser, request)


class CdfRequestMixIn(object):
    extra_template_params = {"response_type": "application/x-cdf"}
    cdf_variable_readers = {
        "Timestamp": read_time_as_mjd2000,
    }

    @classmethod
    def cdf_reader(cls, file_in):
        return parse_cdf(file_in, cls.cdf_variable_readers)

    def get_parsed_response(self, request):
        return self.get_response(self.cdf_reader, request)
