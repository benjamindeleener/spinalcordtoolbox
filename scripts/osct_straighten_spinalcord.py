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
from msct_parser import Parser
from nibabel import load, Nifti1Image, save
from numpy import array, asarray, append, insert, linalg, mean, isnan, sum
from sympy.solvers import solve
from sympy import Symbol
from scipy import ndimage

import sct_utils as sct
from msct_smooth import smoothing_window, evaluate_derivative_3D
from sct_orientation import set_orientation


class SpinalCordStraightener(object):

    def __init__(self, input_filename, centerline_filename, debug=0, deg_poly=10, gapxy=20, gapz=15, padding=30, interpolation_warp='spline', rm_tmp_files=1, verbose=1, algo_fitting='hanning', type_window='hanning', window_length=50, crop=1):
        self.input_filename = input_filename
        self.centerline_filename = centerline_filename
        self.debug = debug
        self.deg_poly = deg_poly  # maximum degree of polynomial function for fitting centerline.
        self.gapxy = gapxy  # size of cross in x and y direction for the landmarks
        self.gapz = gapz  # gap between landmarks along z voxels
        self.padding = padding  # pad input volume in order to deal with the fact that some landmarks might be outside the FOV due to the curvature of the spinal cord
        self.interpolation_warp = interpolation_warp
        self.remove_temp_files = rm_tmp_files  # remove temporary files
        self.verbose = verbose
        self.algo_fitting = algo_fitting  # 'hanning' or 'nurbs'
        self.type_window = type_window  # !! for more choices, edit msct_smooth. Possibilities: 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
        self.window_length = window_length
        self.crop = crop

    def straighten(self):
        pass

    def smooth_centerline(fname_centerline, algo_fitting = 'hanning', type_window = 'hanning', window_length = 80, verbose = 0):
        pass

if __name__ == "__main__":
    # Initialize parser
    parser = Parser(__file__)

    #Mandatory arguments
    parser.usage.set_description("This program takes as input an anatomic image and the centerline or segmentation of its spinal cord (that you can get using sct_get_centerline.py or sct_segmentation_propagation) and returns the anatomic image where the spinal cord was straightened.")
    parser.add_option(name="-i",
                      type_value="image_nifti",
                      description="input image.",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-c",
                      type_value="image_nifti",
                      description="centerline or segmentation.",
                      mandatory=True,
                      example="centerline.nii.gz")
    parser.add_option(name="-p",
                      type_value="int",
                      description="amount of padding for generating labels.",
                      mandatory=False,
                      example="30",
                      default_value=30)
    parser.add_option(name="-x",
                      type_value="multiple_choice",
                      description="Final interpolation.",
                      mandatory=False,
                      example=["nn", "linear", "spline"],
                      default_value="spline")
    parser.add_option(name="-r",
                      type_value="multiple_choice",
                      description="remove temporary files.",
                      mandatory=False,
                      example="spline",
                      default_value=['0', '1'])
    parser.add_option(name="-a",
                      type_value="str",
                      description="Algorithm for curve fitting.",
                      mandatory=False,
                      example=["hanning", "nurbs"],
                      default_value="hanning")
    parser.add_option(name="-f",
                      type_value="multiple_choice",
                      description="Crop option. 0: no crop, 1: crop around landmarks.",
                      mandatory=False,
                      example=['0', '1'],
                      default_value=1)
    parser.add_option(name="-v",
                      type_value="multiple_choice",
                      description="Verbose. 0: nothing, 1: basic, 2: extended.",
                      mandatory=False,
                      example=['0', '1', '2'],
                      default_value=1)

    arguments = parser.parse(sys.argv[1:])

    # assigning variables to arguments
    input_filename = arguments["-i"]
    centerline_file = arguments["-c"]

    sc_straight = SpinalCordStraightener(input_filename, centerline_file)

    # Handling optional arguments
    if "-r" in arguments:
        sc_straight.remove_temp_files = int(arguments["-r"])
    if "-p" in arguments:
        sc_straight.padding = int(arguments["-p"])
    if "-x" in arguments:
        sc_straight.interpolation_warp = str(arguments["-x"])
    if "-a" in arguments:
        sc_straight.algo_fitting = str(arguments["-a"])
    if "-f" in arguments:
        sc_straight.crop = int(arguments["-f"])
    if "-v" in arguments:
        sc_straight.verbose = int(arguments["-v"])

    sc_straight.straighten()
