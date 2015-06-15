#!/usr/bin/env python


from sct_class.CreateMask import *
from msct_parser import Parser
import sys

if __name__ == "__main__":
    # Initialize parser,
    parser = Parser(__file__)

    parser.usage.set_description('Creates a mask with a specific method and shape and returns it as a file')
    parser.add_option(name="-i",
                      type_value="image_nifti",
                      description="input image.",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-m",
                      type_value='str',
                      description="""method to generate mask and associated value.\ncoord: X,Y coordinate of center of mask. E.g.: coord,20x15\npoint: volume that contains a single point. E.g.: point,label.nii.gz\ncenter: mask is created at center of FOV. In that case, "val" is not required.\ncenterline: volume that contains centerline. E.g.: centerline,my_centerline.nii")""",
                      mandatory=False,
                      default_value=Mask.DEFAULT_METHOD)
    parser.add_option(name="-s",
                      type_value="int",
                      description="size in voxel. Odd values are better (for mask to be symmetrical).If shape=gaussian, size corresponds to sigma",
                      mandatory=False,
                      default_value=Mask.DEFAULT_SIZE,
                      example="41")
    parser.add_option(name="-f",
                      type_value="str",
                      description="shape of the mask.",
                      mandatory=False,
                      default_value=Mask.DEFAULT_SHAPE,
                      example="gaussian")
    parser.add_option(name="-o",
                      type_value="file_output",
                      description="output image.",
                      mandatory=False,
                      example="test.nii.gz")
    parser.add_option(name="-r",
                      type_value="multiple_choice",
                      description="Remove temporary files.",
                      mandatory=False,
                      default_value=1,
                      example=['0', '1'])
    parser.add_option(name="-v",
                      type_value="multiple_choice",
                      description="Verbose",
                      mandatory=False,
                      default_value=0,
                      example=['0', '1'])

    # Fetching script arguments
    arguments = parser.parse(sys.argv[1:])

    input_filename = arguments["-i"]

    if "-m" in arguments:
        method_list = arguments["-m"].replace(' ', '').split(',')
        if method_list[0] == "center":
            mask = MaskCenter(input_filename)
        elif method_list[0] == "centerline":
            mask = MaskCenterline(input_filename)
        elif method_list[0] == "point":
            mask = MaskPoint(input_filename)
        elif method_list[0] == "coord":
            mask = MaskCoordinates(input_filename)
        else:
            sct.printv("Mask method invalid", "error")
        if len(method_list) == 2:
            mask.method_value = method_list[1]
        elif len(method_list) > 2:
            sct.printv("Seperate the method by its values with only 1 coma.", "warning")

    # Handling arguments
    if "-o" in arguments:
        mask.output_file = arguments["-o"]
    if "-f" in arguments:
        mask.shape = arguments["-f"]
    if "-s" in arguments:
        mask.size = arguments["-s"]
    if "-r" in arguments:
        mask.rm_tmp_files = arguments["-r"]
    if "-v" in arguments:
        mask.verbose = arguments["-v"]

    mask.execute()
