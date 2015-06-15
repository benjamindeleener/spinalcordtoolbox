#!/usr/bin/env python
#########################################################################################
#
# Command line utilities for ApplyTransfo class
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Olivier Comtois
#
#
# About the license: see the file LICENSE.TXT
#########################################################################################

import sys

from sct_class.ApplyTransfo import ApplyTransfo
from msct_parser import Parser


if __name__ == "__main__":

    # Initialize parser
    parser = Parser(__file__)

    # Mandatory arguments
    parser.usage.set_description('Apply transformations. This function is a wrapper for antsApplyTransforms (ANTs).')
    parser.add_option(name="-i",
                      type_value="image_nifti",
                      description="input image",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-d",
                      type_value="file",
                      description="destination image",
                      mandatory=True,
                      example="out.nii.gz")
    parser.add_option(name="-w",
                      type_value=[[','], "file"],
                      description="warping field",
                      mandatory=True,
                      example="warp1.nii.gz,warp2.nii.gz")
    parser.add_option(name="-c",
                      type_value="int",
                      description="Crop Reference. 0 : no reference. 1 : sets background to 0. 2 : use normal background",
                      mandatory=False,
                      default_value='0',
                      example=['0','1','2'])
    parser.add_option(name="-o",
                      type_value="file_output",
                      description="output file",
                      mandatory=False,
                      default_value='',
                      example="source.nii.gz")
    parser.add_option(name="-x",
                      type_value="multiple_choice",
                      description="interpolation method",
                      mandatory=False,
                      default_value='spline',
                      example=['nn','linear','spline'])

    arguments = parser.parse(sys.argv[1:])

    input_filename = arguments["-i"]
    output_filename = arguments["-d"]
    warp_filename = arguments["-w"]

    transform = ApplyTransfo(input_image=input_filename, output_filename=output_filename, warp=warp_filename)

    if "-c" in arguments:
        transform.crop = arguments["-c"]
    if "-o" in arguments:
        transform.source_reg = arguments["-o"]
    if "-x" in arguments:
        transform.interp = arguments["-x"]

    transform.execute()