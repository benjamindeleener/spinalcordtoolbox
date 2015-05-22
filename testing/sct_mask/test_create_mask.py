__author__ = 'olcoma'

import unittest
import os
import sys
sys.path.append("../../scripts")
import sct_utils as sct
import nibabel
from osct_create_mask import Mask


class TestCreateMask(unittest.TestCase):

    # define class specific constants
    TEST_DATA_PATH = "/sct_testing_data/data/t2/"
    OUT_FILE = "out.nii.gz"
    GOLD_FILE = "gold.nii.gz"
    ORIENTED_FILE = "oriented.nii.gz"
    ORIGINAL_FILE = "../sct_testing_data/data/t2/t2.nii.gz"
    CENTERLINE_FILE = "../sct_testing_data/data/t2/t2_seg.nii.gz"

    def setUp(self):
        print "CURRENT DIR : "+os.getcwd()
        open(self.OUT_FILE, "w+").close()
        open(self.GOLD_FILE, "w+").close()
        sct.run("sct_orientation -i "+self.ORIGINAL_FILE+" -s RPI -o "+self.ORIENTED_FILE)

    def tearDown(self):
        os.remove(self.ORIENTED_FILE)
        os.remove(self.GOLD_FILE)
        os.remove(self.OUT_FILE)

    def test_method_coord(self):

        Mask(input_file=self.ORIENTED_FILE, output_file=self.OUT_FILE, method="coord", method_value="26x30", verbose=1).create_mask()
        sct.run("sct_create_mask -i "+self.ORIENTED_FILE+" -o "+self.GOLD_FILE+" -m coord,26x30")

        # get raw data from file
        result = nibabel.load(self.OUT_FILE).get_data().data
        expected = nibabel.load(self.GOLD_FILE).get_data().data
        # assert image contents
        self.assertEqual(result, expected)

    def test_method_point(self):
        # init crop object
        label_file = os.path.abspath(".."+self.TEST_DATA_PATH+"labels.nii.gz")

        Mask(input_file=self.ORIENTED_FILE, output_file=self.OUT_FILE, method="point", method_value=label_file, verbose=1).create_mask()
        sct.run("sct_create_mask -i "+self.ORIENTED_FILE+" -o "+self.GOLD_FILE+" -m point,"+label_file)

        # get raw data from file
        result = nibabel.load(self.OUT_FILE).get_data().data
        expected = nibabel.load(self.GOLD_FILE).get_data().data

        # assert image contents
        self.assertEqual(result, expected)

    def test_method_center(self):

        Mask(input_file=self.ORIENTED_FILE, output_file=self.OUT_FILE, method="center", verbose=1).create_mask()
        sct.run("sct_create_mask -i "+self.ORIENTED_FILE+" -o "+self.GOLD_FILE+" -m center")

        # get raw data from file
        result = nibabel.load(self.OUT_FILE).get_data().data
        expected = nibabel.load(self.GOLD_FILE).get_data().data
        # assert image contents
        self.assertEqual(result, expected)

    def test_method_centerline(self):
        oriented_seg = "oriented_seg.nii.gz"
        sct.run("sct_orientation -i "+os.path.abspath(self.CENTERLINE_FILE)+" -s RPI -o "+oriented_seg)
        Mask(input_file=os.path.abspath(self.ORIENTED_FILE), verbose=1,  output_file=os.path.abspath(self.OUT_FILE), method="centerline", method_value=os.path.abspath(oriented_seg)).create_mask()
        sct.run("sct_create_mask -i "+os.path.abspath(self.ORIENTED_FILE)+" -o "+os.path.abspath(self.GOLD_FILE)+" -m centerline,"+os.path.abspath(oriented_seg))

        # get raw data from file
        result = nibabel.load(self.OUT_FILE).get_data().data
        expected = nibabel.load(self.GOLD_FILE).get_data().data
        # assert image contents
        # os.remove(oriented_seg)
        self.assertEqual(result, expected)

    def test_shape_cylinder(self):

        Mask(input_file=self.ORIENTED_FILE, output_file=self.OUT_FILE, method="center", verbose=1, shape="cylinder").create_mask()
        sct.run("sct_create_mask -i "+self.ORIENTED_FILE+" -o "+self.GOLD_FILE+" -m center -f cylinder")

        # get raw data from file
        result = nibabel.load(self.OUT_FILE).get_data().data
        expected = nibabel.load(self.GOLD_FILE).get_data().data
        # assert image contents
        self.assertEqual(result, expected)

    def test_shape_box(self):

        Mask(input_file=self.ORIENTED_FILE, output_file=self.OUT_FILE, method="center", verbose=1, shape="box").create_mask()
        sct.run("sct_create_mask -i "+self.ORIENTED_FILE+" -o "+self.GOLD_FILE+" -m center -f box")

        # get raw data from file
        result = nibabel.load(self.OUT_FILE).get_data().data
        expected = nibabel.load(self.GOLD_FILE).get_data().data
        # assert image contents
        self.assertEqual(result, expected)

    def test_shape_gaussian(self):

        Mask(input_file=self.ORIENTED_FILE, output_file=self.OUT_FILE, method="center", verbose=1, shape="gaussian", size=3).create_mask()
        sct.run("sct_create_mask -i "+self.ORIENTED_FILE+" -o "+self.GOLD_FILE+" -m center -s 3 -f gaussian")

        # get raw data from file
        result = nibabel.load(self.OUT_FILE).get_data().data
        expected = nibabel.load(self.GOLD_FILE).get_data().data
        # assert image contents
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
