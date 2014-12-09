#!/usr/bin/env python
#########################################################################################
#
# Asman et al. groupwise multi-atlas segmentation method implementation
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Author: Augustin Roux
# Modified: 2014-11-20
#
# About the license: see the file LICENSE.TXT
#########################################################################################
from msct_parser import *
import sys
from msct_image import Image


class Param:
    def __init__(self):
        self.debug = 0


def main():
    fname_out = ''

    parser = Parser(__file__)
    parser.usage.set_description('Crop the image depending the mask, therefore the mask\'s'
                                 + 'slices must be squares or rectangles of the same size.')
    parser.add_option("-input", "file", "image you want to crop", True, "t2.nii.gz")
    parser.add_option("-mask", "file", "mask you want to crop with", True, "t2_segin.nii.gz")
    parser.add_option("-output", "file", "output file name", False, "t2_segin_cropped_over_mask.nii.gz")

    # Getting the arguments
    arguments = parser.parse(sys.argv[1:])
    fname_input = arguments["-input"]
    fname_mask = arguments["-mask"]
    if "-output" in arguments:
        fname_out = arguments["-output"]

    input_img = Image(fname_input)
    mask = Image(fname_mask)

    input_img.crop_from_square_mask(mask)

    input_img.path = './'

    if fname_out == '':
        fname_out = input_img.file_name + '_smartly_cropped_over_mask'

    input_img.file_name = fname_out
    input_img.save()


if __name__ == "__main__":
    # call main function
    main()
