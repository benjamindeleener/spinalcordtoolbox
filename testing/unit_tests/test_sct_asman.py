#!/usr/bin/env python

# Test script for sct_asman

import pytest
import numpy as np
import sct_asman

@pytest.fixture()
def slice():
    slice = np.asarray([[1, 2, 3, 4],
                        [5, 6, 7, 8],
                        [9, 10, 11, 12]])
    return slice


def test_split(slice):
    left_slice, right_slice = sct_asman.split(slice)

    left_slice_expected = np.asarray([[1, 2],
                                      [5, 6],
                                      [9, 10]])

    right_slice_expected = np.asarray([[4, 3],
                                      [8, 7],
                                      [12, 11]])

    np.testing.assert_array_equal(left_slice, left_slice_expected,
                                  'PB left_slice')
    np.testing.assert_array_equal(right_slice, right_slice_expected,
                                  'PB right_slice')







