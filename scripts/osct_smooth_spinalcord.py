#!/usr/bin/env python
#########################################################################################
#
# Command line utilities for Smoothspinalcord class
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Olivier Comtois
#
#
# About the license: see the file LICENSE.TXT
#########################################################################################


from msct_parser import Parser
from sct_class.SmoothSpinalcord import SmoothSpinalcord


if __name__ == "__main__":

    # Initialize parser
    parser = Parser(__file__)

    parser.usage.set_description(        '  Smooth the spinal cord along its centerline. Steps are: 1) Spinal cord is straightened (using\n' \
        '  centerline), 2) a Gaussian kernel is applied in the superior-inferior direction, 3) then cord is\n' \
        '  de-straightened as originally.\n')
    parser.add_option(name="-i",
                      type_value="image_nifti",
                      description="input image",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-c",
                      type_value="image_nifti",
                      description="Centerline image",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-s",
                      type_value="float",
                      description="Sigma for the gaussian smoothing",
                      mandatory=False,
                      default_value=3,
                      example="3")
    parser.add_option(name="-r",
                      type_value="int",
                      description="Sigma for the gaussian smoothing",
                      mandatory=False,
                      default_value=3,
                      example="3")
    parser.add_option(name="-v",
                      type_value="multiple_choice",
                      description="1: display on, 0: display off (default)",
                      mandatory=False,
                      example=['0', '1'],
                      default_value='1')

    arguments = parser.parse(sys.argv[1:])

    input_filename = arguments["-i"]
    centerline = arguments["-c"]

    smooth = SmoothSpinalcord(input_image=input_filename, centerline_image=centerline)

    if "-s" in arguments:
        smooth.sigma = arguments["-s"]
    if "-r" in arguments:
        smooth.remove_temp_files = arguments["-r"]
    if "-v" in arguments:
        smooth.verbose = arguments["-v"]

    smooth.execute()



