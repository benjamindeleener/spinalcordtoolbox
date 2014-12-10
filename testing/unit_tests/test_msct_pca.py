#!/usr/bin/env python

# Test script for pca_bis

import numpy as np

import pytest
from msct_pca import PCA


@pytest.fixture()
def dataset():
    dataset = np.array([[1, 2, 3],
                        [2, 3, 4]])
    return dataset


@pytest.fixture()
def pca(dataset):
    pca = PCA(dataset)
    return pca


def test_indices(pca):
    assert (pca.J == 3), 'Incorrect number of image sample returned by PCA (N)\n'
    assert (pca.N == 2), 'Incorrect image dimension returned by PCA (J)\n'


def test_mean_image(pca):
    np.testing.assert_array_equal(pca.mean_image, np.array([[2], [3]]),
                                  'PCA.mean() method is not functioning correctly\n')


def test_covariance_matrix(pca):
    np.testing.assert_array_equal(3.0*pca.covariance_matrix, np.array([[2.0, 2.0], [2.0, 2.0]]),
                                  'PCA.scatter_matrix() method is not functioning properly\n')


def test_sort_eig(pca):
    a = pca.eig_pairs[0][0]
    for eig_value in pca.eig_pairs:
        assert (a >= eig_value[0]), 'PCA.sort_eig() method does not work properly\n'


def test_generate_w(pca, dataset):
    assert (pca.W.shape == (2, 1)), 'PCA.w is not set properly\n'
    # pca = PCA(dataset, k=1)
    # print pca.W
    # assert (pca.W.shape == (2, 2)), 'PCA.w is not set properly\n'


# def test_project(pca, dataset):
#     print pca.project(pca.mean_image)
#     pca = PCA(dataset, k=1)
#     print pca.project(pca.mean_image)

