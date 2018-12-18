#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# essential vector algebra
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

from math import pi
from numpy import stack, arccos, sqrt, clip

RAD2DEG = 180./pi


def vector_angle(vect1, vect2):
    """ Get angle between two vectors. """
    return RAD2DEG*arccos(clip(vector_product(vect1, vect2) / sqrt(
        vector_product(vect1, vect1) * vector_product(vect2, vect2)
    ), -1.0, 1.0))


def normalize_vector(vect):
    """ Normalize input to a unit vector. """
    return scale_vector(vect, 1.0/vector_size(vect))


def vector_size(vect):
    """ Normalize input to a unit vector. """
    return sqrt(vector_product(vect, vect))


def vector_product(vect1, vect2):
    """ Calculate scalar product of two vectors. """
    return (vect1 * vect2).sum(axis=-1)


def scale_vector(vect, scale):
    """ Calculate scalar product of two vectors. """
    return stack([
        vect[..., idx] * scale for idx in range(vect.shape[-1])
    ], axis=-1)
