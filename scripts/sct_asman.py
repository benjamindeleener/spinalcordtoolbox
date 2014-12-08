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
from scipy.misc import toimage
from msct_pca import PCA
import numpy as np
from math import sqrt
from msct_image import Image
import matplotlib.pyplot as plt
import sct_utils as sct


class Param:
    def __init__(self):
        self.debug = 0
        self.path_dictionnary = '/home/django/aroux/Desktop/data_asman/Dictionnary/'
        self.patient_id = ['09', '24', '30', '31', '32', '25', '10', '08', '11', '16', '17', '18']
        #self.patient_id = ['09', '24', '30', '31', '32']
        self.include_GM = 0
        self.split_data = 1
        self.verbose = 0


########################################################################################################################
######-------------------------------------------------- MAIN ----------------------------------------------------######
########################################################################################################################

def main():
    v = param.verbose

    # Load all the images's slices from param.path_dictionnary
    list_atlas_seg = load_dictionnary(param.split_data)

    # Construct a dataset composed of all the slices
    dataset = construct_dataset(list_atlas_seg)
    dataset = np.asarray(dataset).T
    sct.printv(dataset.shape, verbose=v)

    #save(dataset, list_atlas_seg)

    # create a PCA instance given the dataset
    pca = PCA(dataset)
    sct.printv('J = ' + str(pca.J) + '  N = ' + str(pca.N), verbose=v)

    # Project a random image
    target = list_atlas_seg[8][0].flatten()
    coord_projected_img = pca.project(target)

    # Showing pca's kept modes and the original & projected image
    pca.plot_omega()
    pca.show(split=param.split_data)
    show(coord_projected_img, pca, target)


########################################################################################################################
######------------------------------------------------- CLASSES --------------------------------------------------######
########################################################################################################################

class AppearenceModel:

    def __init__(self, pca, target_image, number_of_variation_mode=5):
        self.pca = pca
        self.mean = pca.mean_image
        self.target = target_image
        self.number_of_variation_mode = number_of_variation_mode


########################################################################################################################
######------------------------------------------------ FUNCTIONS -------------------------------------------------######
########################################################################################################################

# ----------------------------------------------------------------------------------------------------------------------
# Load the dictionary:
# each slice of each patient will be load separately with its corresponding GM segmentation
# they will be stored as tuples in list_atlas_seg
def load_dictionnary(split_data):
    # init
    list_atlas_seg = []

    # loop across all the volume
    for id in param.patient_id:
        atlas = Image(param.path_dictionnary + 'errsm_' + id + '.nii.gz')
        #atlas = Image(param.path_dictionnary + 'errsm_' + id + '_seg_in.nii.gz')

        if split_data:
            if param.include_GM:
                seg = Image(param.path_dictionnary + 'errsm_' + id + '_GMr.nii.gz')
                index_s = 0
                for slice in atlas.data:
                    left_slice, right_slice = split(slice)
                    seg_slice = seg.data[index_s]
                    left_slice_seg, right_slice_seg = split(seg_slice)
                    list_atlas_seg.append((left_slice, left_slice_seg))
                    list_atlas_seg.append((right_slice, right_slice_seg))
                    index_s += 1
            else:
                index_s = 0
                for slice in atlas.data:
                    left_slice, right_slice = split(slice)
                    list_atlas_seg.append((left_slice, None))
                    list_atlas_seg.append((right_slice, None))
                    index_s += 1
        else:
            if param.include_GM:
                seg = Image(param.path_dictionnary + 'errsm_' + id + '_GMr.nii.gz')
                index_s = 0
                for slice in atlas.data:
                    seg_slice = seg.data[index_s]
                    list_atlas_seg.append((slice, seg_slice))
                    index_s += 1
            else:
                for slice in atlas.data:
                    list_atlas_seg.append((slice, None))
    return list_atlas_seg


def split(slice):
    left_slice = []
    right_slice = []
    row_length = slice.shape[0]
    print 'ROW LEN = ', row_length
    i = 0
    for column in slice:
        if i < row_length/2:
            left_slice.append(column)
        else:
            right_slice.insert(0, column)
        i += 1
    left_slice = np.asarray(left_slice).T
    right_slice = np.asarray(right_slice).T
    assert (left_slice.shape == right_slice.shape), str(left_slice.shape) + '==' + str(right_slice.shape) + 'You should check that the first dim of your image (or slice) is an odd number'
    return left_slice, right_slice


# ----------------------------------------------------------------------------------------------------------------------
# in order to build the PCA from all the J atlases, we must construct a matrix of J columns and N rows,
# with N the dimension of flattened images
def construct_dataset(list_atlas_seg):
    dataset = []
    for atlas_slice in list_atlas_seg:
        dataset.append(atlas_slice[0].flatten())
    return dataset


# ----------------------------------------------------------------------------------------------------------------------
def show(coord_projected_img, pca, target):
    import matplotlib.pyplot as plt

    # Retrieving projected image from the mean image & its coordinates
    import copy
    img_reducted = copy.copy(pca.mean_image)
    for i in range(0, coord_projected_img.shape[0]):
        img_reducted += int(coord_projected_img[i][0])*pca.W.T[i].reshape(pca.N,1)

    if param.split_data:
        n = int(sqrt(pca.N*2))
    else:
        n = int(sqrt(pca.N))
    if param.split_data:
        imgplot = plt.imshow(pca.mean_image.reshape(n, n/2))
    else:
        imgplot = plt.imshow(pca.mean_image.reshape(n, n))
    imgplot.set_interpolation('nearest')
    imgplot.set_cmap('gray')
    plt.title('Mean Image')
    plt.show()
    if param.split_data:
        imgplot = plt.imshow(target.reshape(n, n/2))
    else:
        imgplot = plt.imshow(target.reshape(n, n))
    imgplot.set_interpolation('nearest')
    imgplot.set_cmap('gray')
    plt.title('Original Image')
    plt.show()
    if param.split_data:
        imgplot = plt.imshow(img_reducted.reshape(n, n/2))
    else:
        imgplot = plt.imshow(img_reducted.reshape(n, n))
    imgplot.set_interpolation('nearest')
    imgplot.set_cmap('gray')
    plt.title('Projected Image')
    plt.show()


# ----------------------------------------------------------------------------------------------------------------------
# This little loop save projection through several pcas with different k i.e. different number of modes
def save(dataset, list_atlas_seg):
    import scipy
    import copy
    betas = [0.6, 0.7, 0.75, 0.8, 0.82, 0.85, 0.86, 0.87, 0.88, 0.89, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95]
    target = list_atlas_seg[8][0].flatten()
    for beta in betas:
        pca = PCA(dataset, beta)
        coord_projected_img = pca.project(target)
        img_reducted = copy.copy(pca.mean_image)
        n = int(sqrt(pca.N*2))
        for i in range(0, coord_projected_img.shape[0]):
            img_reducted += int(coord_projected_img[i][0])*pca.W.T[i].reshape(pca.N,1)
        scipy.misc.imsave("/home/django/aroux/Desktop/pca_modesInfluence/"+ str(pca.kept) +"modes.jpeg",
                          img_reducted.reshape(n, n/2))




if __name__ == "__main__":
    param = Param()
    main()

