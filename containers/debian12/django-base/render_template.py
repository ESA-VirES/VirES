#!/usr/bin/env python3
#
# Helper script rendering Jinja2 templates to standard output.
#
# The keys are substituted from the environment variables and option parameters
# file(s).
#

import sys
import os
from os.path import basename
from io import StringIO
from jinja2 import Template


def usage(exename):
    """ Print simple command usage. """
    print(f"USAGE: {basename(exename)} <template> [<parameters> ...]", file=sys.stderr)


def main(template_file, *parameters_files):
    """ Main function. """
    parameters = dict(os.environ)
    for parameters_file in parameters_files:
        parameters.update(read_parameters(parameters_file))
    template = read_template(template_file)
    print(template.render(**parameters))


def read_template(filename):
    """ Read template from a filename or standard input. """
    with _open_file(filename) as file:
        return Template(file.read())


def read_parameters(filename):
    """ Read parameters from a filename or standard input. """
    with _open_file(filename) as file:
        return parse_parameters(file)


def _open_file(filename):
    if not filename:
        return StringIO("") # empty file
    if filename == "-":
        return sys.stdin # standard input
    return open(filename, encoding="utf8") # regular file


def parse_parameters(file):
    """ Parse simple parameters file with one <key>=<value> parameter per line.
    """
    parameters = dict(os.environ)
    for line in file:
        line = line.strip()
        if not line or line.startswith("#"): # skip blank lines and comments
            continue
        key, _, value = line.partition("=")
        parameters[key.strip()] = value.strip()
    return parameters


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage(sys.argv[0])
        sys.exit(1)
    sys.exit(main(*sys.argv[1:]))
