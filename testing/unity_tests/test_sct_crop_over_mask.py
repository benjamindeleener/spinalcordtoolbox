#!/usr/bin/env python
import msct_image
import numpy as np
import pytest


# Creating fake 4x4x4 images including a cubic 4x2x2 mask
@pytest.fixture()
def array_mask():
    mask = np.asarray([[[0, 0, 0, 0],
                        [0, 1, 1, 0],
                        [0, 1, 1, 0],
                        [0, 0, 0, 0]],
                       [[0, 0, 0, 0],
                        [0, 1, 1, 0],
                        [0, 1, 1, 0],
                        [0, 0, 0, 0]],
                       [[0, 0, 0, 0],
                        [0, 1, 1, 0],
                        [0, 1, 1, 0],
                        [0, 0, 0, 0]],
                       [[0, 0, 0, 0],
                        [0, 1, 1, 0],
                        [0, 1, 1, 0],
                        [0, 0, 0, 0]]])

    array = np.asarray([[[0, 0, 0, 0],
                         [0, 0, 0, 0],
                         [0, 8, 0, 0],
                         [0, 0, 0, 0]],
                        [[0, 0, 0, 0],
                         [0, 2, 3, 0],
                         [7, 0, 5, 0],
                         [0, 0, 0, 0]],
                        [[0, 0, 0, 0],
                         [0, 6, 7, 0],
                         [0, 8, 0, 0],
                         [0, 0, 0, 0]],
                        [[0, 0, 0, 0],
                         [1, 0, 0, 2],
                         [0, 0, 0, 0],
                         [0, 0, 0, 0]]])
    return array, mask


def test_crop_mask(array_mask):
    array, mask = array_mask
    print msct_image.crop_mask(array, mask)
    np.testing.assert_array_equal(msct_image.crop_mask(array, mask), np.asarray([[[0, 0],
                                                                                  [8, 0]],
                                                                                 [[2, 3],
                                                                                  [0, 5]],
                                                                                 [[6, 7],
                                                                                  [8, 0]],
                                                                                 [[0, 0],
                                                                                  [0, 0]]]),\
                                  'sct_crop_over_mask does not work')
