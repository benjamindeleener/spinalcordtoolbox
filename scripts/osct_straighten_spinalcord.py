#!/usr/bin/env python
#
# This program takes as input an anatomic image and the centerline or segmentation of its spinal cord (that you can get
# using sct_get_centerline.py or sct_segmentation_propagation) and returns the anatomic image where the spinal
# cord was straightened.
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2013 NeuroPoly, Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Julien Cohen-Adad, Geoffrey Leveque, Julien Touati
# Modified: 2014-09-01
#
# License: see the LICENSE.TXT
#=======================================================================================================================
# check if needed Python libraries are already installed or not
import os
import getopt
import time
import commands
import sys

from nibabel import load, Nifti1Image, save
from numpy import array, asarray, append, insert, linalg, mean, isnan, sum
from sympy.solvers import solve
from sympy import Symbol
from scipy import ndimage

import sct_utils as sct
from msct_smooth import smoothing_window, evaluate_derivative_3D
from sct_orientation import set_orientation

