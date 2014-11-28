#!/usr/bin/env python
#
#
# Implementation of Principal Component Analysis using scatter matrix inspired by Sebastian Raschka
# http://sebastianraschka.com/Articles/2014_pca_step_by_step.html#sc_matrix
#
# Step 1: Take the whole dataset consisting of J N-dimensional flattened images

# Step 2: Compute the mean image

# Step 3: Compute the scatter matrix of the dataset

# Step 4: Compute the eigenvectors and corresponding eigenvalues

# Step 5: Sort the eigenvectors by decreasing eigenvalues and choose k in order to keep V of them such as:
#       sum(kept eigenvalues)/sum(all eigenvalues) > k
# This will give us a N*V dimensionnal matrix, we call it W, every column represents an eigenvector

# Step 6: Transform the target image onto the new subspace, this can be done by:
#       y = W.T*(x - mean)  where x is the target N*1 flatenned image and y is its


#=======================================================================================================================
import numpy as np


class PCA:

    def __init__(self, dataset, k=0.90):
        # STEP 1
        self.dataset = dataset  # This should be a J*N dimensional matrix of J N-dimensional flattened images
        self.N = dataset.shape[0]  # The number of rows is the dimension of flattened images
        self.J = dataset.shape[1]  # The number of columns is the number of images
        # STEP 2
        self.mean_image = self.mean()
        # STEP 3
        self.scatter_matrix = self.scatter_matrix()
        # STEP 4 eigpairs consist of a list of tuple (eigenvalue, eigenvector) already sorted by decreasing eigenvalues
        self.eig_pairs = self.sort_eig()
        # STEP 5
        self.k = k
        self.W = self.generate_W()

    # STEP 2
    def mean(self, ):
        mean_im = []
        for row in self.dataset:
            m = sum(row)/self.J
            mean_im.append(m)
        mean_im = np.array([mean_im]).T
        return mean_im

    # STEP 3
    def scatter_matrix(self):
        N = self.N
        J = self.J
        scatter_matrix = np.zeros((N, N))
        for j in range(0, J):
            scatter_matrix += (self.dataset[:, j].reshape(N, 1) - self.mean_image)\
                .dot((self.dataset[:, j].reshape(N, 1) - self.mean_image).T)
        return scatter_matrix

    # STEP 4
    def sort_eig(self):
        eigenvalues, eigenvectors = np.linalg.eig(self.scatter_matrix)
        # Create a list of (eigenvalue, eigenvector) tuple
        eig_pairs = [(np.abs(eigenvalues[i]), eigenvectors[:, i]) for i in range(len(eigenvalues))]
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
        return W

    # STEP 6
    def project(self, target):
        if (target.shape == (self.N, 1)):
            return self.W.T.dot(target - self.mean_image)
        else:
            print "target dimension is {}, must be {}.\n".format(target.shape, self.N)


