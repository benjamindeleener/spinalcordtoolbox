#!/usr/bin/env python
#########################################################################################
#
# Asman et al. groupwise multi-atlas segmentation method implementation
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Augustin Roux
# Modified: 2014-11-20
#
# About the license: see the file LICENSE.TXT
#########################################################################################
from msct_pca import PCA
import numpy as np
from math import exp


def main():



class AtlasInformation:
    def __init__(self, dict_atlas_seg):
        self.dict_atlas_seg = dict_atlas_seg

    # TODO
    # This method register all of the couple {atlas,seg} into a common groupwise space
    def rigid_registering(self):
        return 1


class AppearenceModel:

    def __init__(self, pca, number_of_variation_mode):
        self.number_of_variation_mode = number_of_variation_mode
        self.psi = pca.mu
        self.pca = pca

    def get_eigen_values(self):
        # J is the number of couple {atlas:seg} that has been used to generate the PCA,
        # it also is the dimension of the original space
        J = self.pca.numcols

    # return a vector
    def get_beta(self, target_img):
        beta = []
        t = 1
        for omega in Omega:
            norm = np.linalg.norm(omega - target_img, 2)
            beta.append(exp(-t*norm))







if __name__ == "__main__":
    main()

