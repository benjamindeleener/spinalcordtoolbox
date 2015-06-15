#!/usr/bin/env python
import sys

from sct_class.ImageCropper import ImageCropper
from msct_parser import Parser


if __name__ == "__main__":

    # Initialize parser
    parser = Parser(__file__)

    # Mandatory arguments
    parser.usage.set_description('Tools to crop an image. Either through command line or GUI')
    parser.add_option(name="-i",
                      type_value="image_nifti",
                      description="input image.",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-g",
                      type_value="multiple_choice",
                      description="1: use the GUI to crop, 0: use the command line to crop",
                      mandatory=False,
                      example=['0', '1'],
                      default_value='0')

    # Command line mandatory arguments
    parser.usage.addSection("\nCOMMAND LINE RELATED MANDATORY ARGUMENTS")
    parser.add_option(name="-o",
                      type_value="file_output",
                      description="output image. This option is REQUIRED for the command line execution",
                      mandatory=False,
                      example=['t1', 't2'])

    # Optional arguments section
    parser.add_option(name="-v",
                      type_value="multiple_choice",
                      description="1: display on, 0: display off (default)",
                      mandatory=False,
                      example=['0', '1'],
                      default_value='1')

    parser.add_option(name="-h",
                      type_value=None,
                      description="Displays help",
                      mandatory=False)

    # GUI optional argument
    parser.usage.addSection("\nGUI RELATED OPTIONAL ARGUMENTS")
    parser.add_option(name="-r",
                      type_value="multiple_choice",
                      description="Remove temporary files. Default = 1",
                      mandatory=False,
                      example=['0', '1'])

    # Command line optional arguments
    parser.usage.addSection("\nCOMMAND LINE RELATED OPTIONAL ARGUMENTS")
    parser.add_option(name="-m",
                      type_value="file",
                      description="cropping around the mask",
                      mandatory=False)
    parser.add_option(name="-start",
                      type_value=[[','], 'float'],
                      description="start slices, ]0,1[: percentage, 0 & >1: slice number",
                      mandatory=False,
                      example="40,30,5")
    parser.add_option(name="-end",
                      type_value=[[','], 'float'],
                      description="end slices, ]0,1[: percentage, 0: last slice, >1: slice number, <0: last slice - value",
                      mandatory=False,
                      example="60,100,10")
    parser.add_option(name="-dim",
                      type_value=[[','], 'int'],
                      description="dimension to crop, from 0 to n-1, default is 1",
                      mandatory=False,
                      example="0,1,2")
    parser.add_option(name="-shift",
                      type_value=[[','], 'int'],
                      description="adding shift when used with mask, default is 0",
                      mandatory=False,
                      example="10,10,5")
    parser.add_option(name="-b",
                      type_value="float",
                      description="replace voxels outside cropping region with background value",
                      mandatory=False)
    parser.add_option(name="-bmax",
                      type_value=None,
                      description="maximize the cropping of the image (provide -dim if you want to specify the dimensions)",
                      mandatory=False)
    parser.add_option(name="-ref",
                      type_value="file",
                      description="crop input image based on reference image (works only for 3D images)",
                      mandatory=False,
                      example="ref.nii.gz")
    parser.add_option(name="-mesh",
                      type_value="file",
                      description="mesh to crop",
                      mandatory=False)
    parser.add_option(name="-rof",
                      type_value="multiple_choice",
                      description="remove output file created when cropping",
                      mandatory=False,
                      default_value='0',
                      example=['0', '1'])
    parser.add_option(name="-bzmax",
                      type_value=None,
                      description="maximize the cropping of the image (provide -dim if you want to specify the dimensions)",
                      deprecated_by="-bmax",
                      mandatory=False)

    # Fetching script arguments
    arguments = parser.parse(sys.argv[1:])

    # assigning variables to arguments
    input_filename = arguments["-i"]
    exec_choice = 0
    if "-g" in arguments:
        exec_choice = bool(int(arguments["-g"]))

    cropper = ImageCropper(input_filename)
    if exec_choice:
        fname_data = arguments["-i"]
        if "-r" in arguments:
            cropper.rm_tmp_files = int(arguments["-r"])
        if "-v" in arguments:
            cropper.verbose = int(arguments["-v"])

        cropper.crop_with_gui()

    else:
        if "-o" in arguments:
            cropper.output_filename = arguments["-o"]
        else:
            print "An output file needs to be specified using the command line"
            sys.exit(2)
        # Handling optional arguments
        if "-m" in arguments:
            cropper._mask = arguments["-m"]
        if "-start" in arguments:
            cropper.start = arguments["-start"]
        if "-end" in arguments:
            cropper.end = arguments["-end"]
        if "-dim" in arguments:
            cropper.dim = arguments["-dim"]
        if "-shift" in arguments:
            cropper.shift = arguments["-shift"]
        if "-b" in arguments:
            cropper.background = arguments["-b"]
        if "-bmax" in arguments:
            cropper.bmax = True
        if "-ref" in arguments:
            cropper.ref = arguments["-ref"]
        if "-mesh" in arguments:
            cropper.mesh = arguments["-mesh"]

        cropper.execute()
