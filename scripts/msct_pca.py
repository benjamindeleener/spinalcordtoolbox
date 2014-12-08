#!/usr/bin/env python
########################################################################################################################
#
# Implementation of Principal Component Analysis using scatter matrix inspired by Sebastian Raschka
# http://sebastianraschka.com/Articles/2014_pca_step_by_step.html#sc_matrix
#
#
# Step 1: Take the whole dataset consisting of J N-dimensional flattened images
#
# Step 2: Compute the mean image
#
# Step 3: Compute the covariance matrix of the dataset
#
# Step 4: Compute the eigenvectors and corresponding eigenvalues
#
# Step 5: Sort the eigenvectors by decreasing eigenvalues and choose k in order to keep V of them such as:
#       sum(kept eigenvalues)/sum(all eigenvalues) > k
# This will give us a N*V dimensionnal matrix, we call it W, every column represents an eigenvector
#
# Step 6: Transform the target image onto the new subspace, this can be done by:
#       y = W.T*(x - mean)  where x is the target N*1 flatenned image and y is its
#
# ----------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Augustin Roux
# Modified: 2014-12-05
#
# About the license: see the file LICENSE.TXT
########################################################################################################################

import numpy as np


class PCA:

    def __init__(self, dataset, k=0.70):
        # STEP 1
        self.dataset = dataset  # This should be a J*N dimensional matrix of J N-dimensional flattened images
        self.N = dataset.shape[0]  # The number of rows is the dimension of flattened images
        self.J = dataset.shape[1]  # The number of columns is the number of images
        # STEP 2
        self.mean_image = self.mean()
        # STEP 3
        self.covariance_matrix = self.covariance_matrix()
        # STEP 4 eigpairs consist of a list of tuple (eigenvalue, eigenvector) already sorted by decreasing eigenvalues
        self.eig_pairs = self.sort_eig()
        # STEP 5
        self.k = k
        self.W, self.kept = self.generate_W()

    # STEP 2
    def mean(self, ):
        mean_im = []
        for row in self.dataset:
            m = sum(row)/self.J
            mean_im.append(m)
        mean_im = np.array([mean_im]).T
        return mean_im

    # STEP 3
    def covariance_matrix(self):
        N = self.N
        J = self.J
        covariance_matrix = np.zeros((N, N))
        for j in range(0, J):
            covariance_matrix += float(1)/self.J*(self.dataset[:, j].reshape(N, 1) - self.mean_image)\
                .dot((self.dataset[:, j].reshape(N, 1) - self.mean_image).T)
        return covariance_matrix

    # STEP 4
    def sort_eig(self):
        eigenvalues, eigenvectors = np.linalg.eig(self.covariance_matrix)
        # Create a list of (eigenvalue, eigenvector) tuple
        eig_pairs = [(np.abs(eigenvalues[i]), eigenvectors[:, i]) for i in range(len(eigenvalues))
                     if np.abs(eigenvalues[i]) > 0.0000001]
        # Sort the (eigenvalue, eigenvector) tuples from high to low
        eig_pairs.sort()
        eig_pairs.reverse()
        return eig_pairs

    # STEP 5
    def generate_W(self):
        eigenvalues_kept = []
        s = sum([eig[0] for eig in self.eig_pairs])
        first = 1
        for eig in self.eig_pairs:
            if first:
                W = eig[1].reshape(self.N, 1)
                eigenvalues_kept.append(eig[0])
                first = 0
            else:
                if (sum(eigenvalues_kept) + eig[0])/s <= self.k:
                    eigenvalues_kept.append(eig[0])
                    W = np.hstack((W, eig[1].reshape(self.N, 1)))
                else:
                    break
        kept = len(eigenvalues_kept)
        print 'kept = ', kept
        return W, kept

    # STEP 6
    def project(self, target):
        if target.shape == (self.N,):
            target = target.reshape(self.N, 1)
            coord_projected_img = self.W.T.dot(target - self.mean_image)
            return coord_projected_img
        else:
            print "target dimension is {}, must be {}.\n".format(target.shape, self.N)

    # Show all the mode
    def show(self, split=1):
        from math import sqrt
        import matplotlib.pyplot as plt
        if split:
            n = int(sqrt(2*self.N))
        else:
            n = int(sqrt(self.N))
        fig = plt.figure()
        for i_fig in range(0, self.kept):
            eigen_V = self.W.T[i_fig, :]
            a = fig.add_subplot(4, 4, i_fig)
            if split:
                imgplot = a.imshow(eigen_V.reshape(n, n/2))
            else:
                imgplot = a.imshow(eigen_V.reshape(n, n))
            imgplot.set_interpolation('nearest')
            imgplot.set_cmap('Greys')

        plt.show()

    # TODO
    # project all the images from the dataset in order to calculate geodesical distances between the target image
    # and the dataset
    #def project_all


