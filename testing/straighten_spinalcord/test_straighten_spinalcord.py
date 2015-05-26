__author__ = 'olcoma'

import sys
sys.path.append("../../scripts")
import unittest
import shutil
import os
import nibabel
from osct_straighten_spinalcord import SpinalCordStraightener
import sct_utils as sct

class TestStraightenSpinalCord(unittest.TestCase):

    # Class Constants
    ORIGINAL_FILE = "../sct_testing_data/data/t2/t2.nii.gz"
    CENTERLINE_FILE = "../sct_testing_data/data/t2/t2_seg.nii.gz"
    OUT_FILE = "out.nii.gz"
    GOLD_FILE = "gold.nii.gz"
    TEST_DATA_PATH = "/sct_testing_data/data/t2/"
    S2C_WARP = 'warp_straight2curve.nii.gz'
    C2S_WARP = 'warp_curve2straight.nii.gz'
    STRAIGHT_FILE = 't2_straight.nii.gz'

    def setUp(self):
        os.mkdir("ref")
        os.mkdir("gold")

    def tearDown(self):
        shutil.rmtree("ref")
        shutil.rmtree("gold")

    def test_default(self):
        os.chdir("ref")
        try:
            SpinalCordStraightener(input_filename="../"+self.ORIGINAL_FILE, centerline_filename="../"+self.CENTERLINE_FILE, verbose=1).straighten()
        except:
            pass
        os.chdir("../gold")
        try:
            sct.run("sct_straighten_spinalcord -i ../"+self.ORIGINAL_FILE+" -c ../"+self.CENTERLINE_FILE)
        except:
            pass
        os.chdir('..')

        result = nibabel.load("ref/"+self.STRAIGHT_FILE).get_data().data
        expected = nibabel.load("gold/"+self.STRAIGHT_FILE).get_data().data

        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
