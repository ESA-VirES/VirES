#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Test Sun ephemeris and magnetic coordinates calculated by the VirES for Swarm
# server. The values are compared with the values calculated by the eoxmagmod
# package.
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
import sys
from os.path import basename
from datetime import datetime
from numpy import stack
from eoxmagmod import (
    vnorm, load_model_shc, load_model_shc_combined,
    load_model_swarm_mma_2c_external,
    load_model_swarm_mma_2c_internal,
    load_model_swarm_mma_2f_geo_external,
    load_model_swarm_mma_2f_geo_internal,
    load_model_swarm_mio_external,
    load_model_swarm_mio_internal,
)
from eoxmagmod.data import IGRF12, CHAOS6_STATIC, CHAOS6_CORE_LATEST, SIFM
from eoxmagmod.time_util import decimal_year_to_mjd2000_simple
from util.cdf import load_cdf, CDFError, read_time_as_mjd2000
from util.csv import load_csv
from util.time_util import parse_datetime
from util.testing import test_variables

DT_2000 = datetime(2000, 1, 1)
S2DAYS = 1.0/(24*60*60)

CDF_VARIABLE_READERS = {
    "Timestamp": read_time_as_mjd2000,
}

CSV_VALUE_PARSERS = {
    'id': str,
    'Spacecraft': str,
    'Timestamp': (
        lambda v: S2DAYS * (parse_datetime(v) - DT_2000).total_seconds()
    ),
}

MCO_SHA_2C = "./data/SW_OPER_MCO_SHA_2C.shc"
MCO_SHA_2D = "./data/SW_OPER_MCO_SHA_2D.shc"
MCO_SHA_2F = "./data/SW_OPER_MCO_SHA_2F.shc"
MLI_SHA_2C = "./data/SW_OPER_MLI_SHA_2C.shc"
MLI_SHA_2D = "./data/SW_OPER_MLI_SHA_2D.shc"
MIO_SHA_2C = "./data/SW_OPER_MIO_SHA_2C.txt"
MIO_SHA_2D = "./data/SW_OPER_MIO_SHA_2D.txt"
MMA_SHA_2C = "./data/SW_OPER_MMA_SHA_2C.cdf"
MMA_SHA_2F = "./data/SW_OPER_MMA_SHA_2F.cdf"

MODELS = {
    "IGRF12": {
        "loader": lambda f: load_model_shc(f, interpolate_in_decimal_years=True),
        "files": [IGRF12],
    },
    "CHAOS-6-Core": {
        "loader": lambda f: load_model_shc(
            f, to_mjd2000=decimal_year_to_mjd2000_simple
        ),
        "files": [CHAOS6_CORE_LATEST],
    },
    "CHAOS-6-Combined": {
        "loader": lambda f1, f2: load_model_shc_combined(
            f1, f2, to_mjd2000=decimal_year_to_mjd2000_simple
        ),
        "files": [CHAOS6_CORE_LATEST, CHAOS6_STATIC],
    },
    "CHAOS-6-Static": {"loader": load_model_shc, "files": [CHAOS6_STATIC]},
    "SIFM": {"loader": load_model_shc, "files": [SIFM]},
    "Custom": {"loader": load_model_shc, "files": None},
    "MCO_SHA_2C": {"loader": load_model_shc, "files": [MCO_SHA_2C]},
    "MCO_SHA_2D": {"loader": load_model_shc, "files": [MCO_SHA_2D]},
    "MCO_SHA_2F": {"loader": load_model_shc, "files": [MCO_SHA_2F]},
    "MLI_SHA_2C": {"loader": load_model_shc, "files": [MLI_SHA_2C]},
    "MLI_SHA_2D": {"loader": load_model_shc, "files": [MLI_SHA_2D]},
    "MIO_SHA_2C-Primary": {
        "loader": load_model_swarm_mio_external,
        "files": [MIO_SHA_2C], "parameters" : {"f107": "F107"},
    },
    "MIO_SHA_2C-Secondary": {
        "loader": load_model_swarm_mio_internal,
        "files": [MIO_SHA_2C], "parameters" : {"f107": "F107"},
    },
    "MIO_SHA_2D-Primary": {
        "loader": load_model_swarm_mio_external,
        "files": [MIO_SHA_2D], "parameters" : {"f107": "F107"},
    },
    "MIO_SHA_2D-Secondary": {
        "loader": load_model_swarm_mio_internal,
        "files": [MIO_SHA_2D], "parameters" : {"f107": "F107"},
    },
    "MMA_SHA_2C-Primary": {
        "loader": load_model_swarm_mma_2c_external, "files": [MMA_SHA_2C],
    },
    "MMA_SHA_2C-Secondary": {
        "loader": load_model_swarm_mma_2c_internal, "files": [MMA_SHA_2C],
    },
    "MMA_SHA_2F-Primary": {
        "loader": load_model_swarm_mma_2f_geo_external, "files": [MMA_SHA_2F],
    },
    "MMA_SHA_2F-Secondary": {
        "loader": load_model_swarm_mma_2f_geo_internal, "files": [MMA_SHA_2F],
    },
}

TESTED_VARIABLES = {
    "F_%s": {"uom": "nT", "atol": 1e-1},
    "F_res_%s": {"uom": "nT", "atol": 1e-1},
    "B_NEC_%s": {"uom": "nT", "atol": 1e-1},
    "B_NEC_res_%s": {"uom": "nT", "atol": 1e-1},
}


class CommandError(Exception):
    """ Command error exception. """
    pass


def main(model_name, filename, *model_filenames):
    """ main subroutine """
    print("Loading data ..."); sys.stdout.flush()
    data = load_data(filename)

    print("Calculating reference values ..."); sys.stdout.flush()
    model, model_params = get_model_instance(model_name, *model_filenames)
    params = dict(
        (name, data[variable]) for name, variable in model_params.items()
    )
    reference = eval_model(
        model_name, model, data['Timestamp'], data['Latitude'],
        data['Longitude'], data['Radius'], data['F'], data['B_NEC'], **params
    )

    tested_variables = dict(
        (key % model_name, params) for key, params in TESTED_VARIABLES.items()
    )

    test_variables(data, reference, tested_variables)


def get_model_instance(model_name, *model_filenames):
    """ Get instance of the model. """
    try:
        model_def = MODELS[model_name]
    except KeyError:
        raise CommandError("Invalid model name %s! Allowed names are: %s" % (
            model_name, ", ".join(MODELS)
        ))

    if model_def["files"] is None and not model_filenames:
        raise CommandError("%s model requires model filename!" % model_name)

    if not model_filenames:
        model_filenames = model_def["files"]

    print("Using following Model files:")
    for filename in model_filenames:
        print(filename)

    model = model_def["loader"](*model_filenames)

    return model, model_def.get("parameters", {})


def eval_model(model_name, model, mjd2000, latitude, longitude, radius,
               measured_f, measured_b_nec, **params):
    """Evaluate magnetic model. """
    coords = stack((latitude, longitude, radius*1e-3), axis=-1)
    model_b_nec = model.eval(mjd2000, coords, scale=[1, 1, -1], **params)
    model_f = vnorm(model_b_nec)

    data = {
        "Timestamp": mjd2000,
        "Latitude": latitude,
        "Longitude": longitude,
        "Radius": radius,
        "F_%s" % model_name: model_f,
        "B_NEC_%s" % model_name: model_b_nec,
    }

    if measured_f is not None:
        data["F_res_%s" % model_name] = measured_f - model_f

    if measured_b_nec is not None:
        data["B_NEC_res_%s" % model_name] = measured_b_nec - model_b_nec

    return data


def parse_inputs(argv):
    """ Parse input arguments. """
    try:
        model_name = argv[1]
        filename = argv[2]
        model_filenames = argv[3:]
    except IndexError:
        raise CommandError("Not enough input arguments!")
    return (model_name, filename) + tuple(model_filenames)


def usage(exename, file=sys.stderr):
    """ Print usage. """
    print(
        "USAGE: %s <model_name> <tested file> [<model_file> ...]"
        % basename(exename), file=file
    )


def load_data(filename):
    """ Load data from the input file. """
    try:
        return load_cdf(filename, CDF_VARIABLE_READERS)
    except CDFError:
        pass
    return load_csv(filename, CSV_VALUE_PARSERS)


if __name__ == "__main__":
    try:
        sys.exit(main(*parse_inputs(sys.argv)))
    except CommandError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        usage(sys.argv[0])
