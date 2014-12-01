#!/usr/bin/env python
#########################################################################################
#
# Image class implementation
#
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Augustin Roux
# Modified: 2014-11-28
#
# About the license: see the file LICENSE.TXT
#########################################################################################

import nibabel as nib
import sct_utils as sct
import numpy as np
from sct_orientation import get_orientation


class Image:

    def __init__(self, path=None, verbose=0, np_array=None):
        if path is not None:
            sct.check_file_exist(path, verbose=verbose)
            try:
                im_file = nib.load(path)
            except nib.spatialimages.ImageFileError:
                sct.printv('Error: make sure ' + path + ' is an image.')
            self.orientation = get_orientation(path)
            self.data = im_file.get_data()
            self.hdr = im_file.get_header()
            self.path, self.file, self.ext = sct.extract_fname(path)
        elif np_array:
            self.data = np_array
            self.path = None
            self.orientation = None
        else:
            raise TypeError(' Image constructor takes at least one argument.')

    def save(self):
        #hdr.set_data_dtype(img_type) # set imagetype to uint8 #TODO: maybe use int32
        self.hdr.set_data_shape(self.data.shape)
        img = nib.Nifti1Image(self.data, None, self.hdr)
        print 'saving ' + self.path + self.file + self.ext + '\n'
        print self.hdr.get_data_shape()
        nib.save(img, self.path + self.file + self.ext)

    # flatten the array in a single dimension vector
    def flatten(self):
        return self.data.flatten()

    # return a list of the image slices flattened
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

    # crop the image in order to keep only voxels in the mask, therefore the mask's slices must be squares or
    # rectangles of the same size
    def crop_from_square_mask(self, mask):
        self.data = crop_mask(self.data, mask.data)


def crop_mask(array, data_mask):
    print 'ORIGINAL SHAPE: ', array.shape, '   ==   ', data_mask.shape
    array = np.asarray(array)
    data_mask = np.asarray(data_mask)
    new_data = []
    buffer = []
    buffer_mask = []
    s = 0
    r = 0
    ok = 0
    for slice in data_mask:
        #print 'SLICE ', s, slice
        for row in slice:
            if sum(row) > 0:
                buffer_mask.append(row)
                buffer.append(array[s][r])
                #print 'OK1', ok
                ok += 1
            r += 1
        new_slice_mask = np.asarray(buffer_mask).T
        new_slice = np.asarray(buffer).T
        r = 0
        buffer = []
        for row in new_slice_mask:
            if sum(row) != 0:
                buffer.append(new_slice[r])
            r += 1
        #print buffer
        new_slice = np.asarray(buffer).T
        r = 0
        buffer_mask = []
        buffer = []
        new_data.append(new_slice)
        s += 1
    new_data = np.asarray(new_data)
    #print data_mask
    print 'SHAPE ', new_data.shape
    return new_data