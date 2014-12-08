#!/usr/bin/env python
from msct_parser import *
import sys
from msct_image import Image


class Param:
    def __init__(self):
        self.debug = 0


def main():
    fname_out = ''

    parser = Parser(__file__)
    parser.usage.set_description('Crop the image depending the mask, therefore the mask\'s\
                                slices must be squares or rectangles of the same size.')
    parser.add_option("-input", "file", "image you want to crop", True, "t2.nii.gz")
    parser.add_option("-mask", "file", "mask you want to crop with", True, "t2_segin.nii.gz")
    parser.add_option("-output", "file", "output file name", False, "t2_segin_cropped_over_mask.nii.gz")
    usage = parser.usage.generate()

    arguments = parser.parse(sys.argv[1:])
    #if "-input" in arguments:
    fname_input = arguments["-input"]
    #if "-mask" in arguments:
    fname_mask = arguments["-mask"]
    #else:
    #    print usage
    #    exit(1)

    if "-output" in arguments:
        fname_out = arguments["-output"]

    input_img = Image(fname_input)
    mask = Image(fname_mask)

    input_img.crop_from_square_mask(mask)

    input_img.path = './'

    if fname_out == '':
        fname_out = input_img.file + '_smartly_cropped_over_mask'

    input_img.file = fname_out
    input_img.save()


if __name__ == "__main__":
    # call main function
    main()
