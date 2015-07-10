#!/usr/bin/env python
#########################################################################################
#
# This script preps .nii data in uses Vladimir Frolov's straightening method in order
# to straighten the spinal cord
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Olivier Comtois
# Modified: 2015-07-8
#
# About the license: see the file LICENSE.TXT
#########################################################################################

import sct_utils as sct
from msct_parser import Parser
import os
import commands
import sys

class VladStraighten(object):
    def __init__(self, input_image, output_filnename="straight", verbose=1):
        self.input_image = input_image
        self.output_filename = output_filnename
        self.verbose = verbose

    def execute(self):
        # change input filename to mnc format
        fname_bare = str(self.input_image).split(".", 1)[0]
        mnc_out = self.output_filename + ".mnc"

        fname_in = self.input_image
        fname_nii = str(fname_in).replace(".gz", "")
        fname_mnc = str(fname_nii).replace(".nii", ".mnc")

        fname_seg = str(fname_bare)+"_seg.nii.gz"
        fname_seg_nii = str(fname_seg).replace(".gz", "")
        fname_seg_mnc = str(fname_seg_nii).replace(".nii", ".mnc")

        cmd = "sct_propseg -i "+fname_in+" -t t2 -o . -init 140"
        output = commands.getoutput(cmd)

        if str(output) == "0":
            raise Exception(str(output))
        else:
            sct.printv(output)

        if str(fname_in).endswith(".gz"):
            cmd = "gunzip -c "+self.input_image+" >"+fname_nii
            output = commands.getoutput(cmd)

        if str(fname_seg).endswith(".gz"):
            cmd = "gunzip -c "+fname_seg+" >"+fname_seg_nii
            output = commands.getoutput(cmd)

        cmd = "nii2mnc "+fname_nii
        output = commands.getoutput(cmd)

        cmd = "nii2mnc "+fname_seg_nii
        output = commands.getoutput(cmd)

        # we are now working with a minc file

        cmd = "itk_spine_straighten "+fname_mnc+" "+fname_seg_mnc+" "+mnc_out
        output = commands.getoutput(cmd)

        if str(output) != "0":
            os.remove(fname_seg_nii)
            os.remove(fname_seg)
            os.remove(fname_seg_mnc)

            os.remove(fname_nii)
            os.remove(fname_mnc)

            raise Exception(str(output))

        cmd = "mnc2nii "+mnc_out
        output = commands.getoutput(cmd)

        os.remove(fname_seg_nii)
        os.remove(fname_seg)
        os.remove(fname_seg_mnc)

        os.remove(fname_nii)
        os.remove(fname_mnc)
        os.remove(mnc_out)

if __name__ == "__main__":

    # Initialize parser
    parser = Parser(__file__)

    parser.usage.set_description("This script preps .nii data in order to use Vladimir Frolov's straightening method in order to straighten the spinal cord")
    parser.add_option(name="-i",
                      type_value="image_nifti",
                      description="input image.",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-o",
                      type_value="file_output",
                      description="Output's filnename.",
                      mandatory=False,
                      example="result")

    arguments = parser.parse(sys.argv[1:])

    input_filename = arguments["-i"]

    sc = VladStraighten(input_filename)

    if "-o" in arguments:
        sc.output_filename = arguments["-o"]

    try:
        sc.execute()
    except Exception, e:
        sct.printv(e.message, type="error")

