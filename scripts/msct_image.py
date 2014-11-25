#!/usr/bin/env python
#########################################################################################
#
# Image class implementation
#
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Augustin Roux
# Modified: 2014-11-20
#
# About the license: see the file LICENSE.TXT
#########################################################################################

import nibabel as nib
import sct_utils as sct
import numpy as np
from sct_orientation import get_orientation


class Image_sct:

    def __init__(self, path=None, verbose=0, np_array=None):
        if path is not None:
            sct.check_file_exist(path, verbose=verbose)
            try:
                im_file = nib.load(path)
            except nib.spatialimages.ImageFileError:
                sct.printv('Error: make sure ' + path + ' is an image.')
            self.path = path
            self.orientation = get_orientation(path)
            self.data = im_file.get_data()
        elif np_array:
            self.data = np_array
            self.path = None
            self.orientation = None
        else:
            raise TypeError(' Image constructor takes at least one argument.')

    # flatten the array in a single dimension vector
    def flatten(self):
        return self.data.flatten()

    # return a list of slice flattened
    def slices(self):
        slices = []
        for slc in self.data:
            slices.append(slc.flatten())
        return slices

    # return image dimensions
    def get_dim(self):
        if self.orientation:
            return self.orientation
        else:
            sct.printv('No file provided for the image')

    # return an empty image of the same size as the image passed in parameters
    def empty_image(self):
        import copy
        im_buf = copy.copy(self)
        im_buf.data *= 0
        return im_buf


