#!/usr/bin/env python
import msct_image
from msct_image import Image
import numpy as np
import pytest


# Creating fake 4x4x4 images including a cubic 4x2x2 mask
@pytest.fixture()
def array_mask():
    data_mask = np.asarray([[[0, 0, 0, 0],
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
    mask = Image(np_array=data_mask)
    img = Image(np_array=array)

    return img, mask


def test_crop_mask(array_mask):
    img, mask = array_mask
    print img.crop_from_square_mask(mask)
    np.testing.assert_array_equal(img.crop_from_square_mask(mask), np.asarray([[[0, 0],
                                                                                [8, 0]],
                                                                               [[2, 3],
                                                                                [0, 5]],
                                                                               [[6, 7],
                                                                                [8, 0]],
                                                                               [[0, 0],
                                                                                [0, 0]]]),
                                  'sct_crop_over_mask does not work')
