__author__ = 'olcoma'

import sys
sys.path.append("../../scripts")
import unittest
import os
import shutil
from sct_apply_transfo import Transform
import sct_label_utils
import sct_utils as sct
import nibabel


class ApplyTransfo(unittest.TestCase):

    INPUT_FILE = "../sct_testing_data/data/template/MNI-Poly-AMU_T2.nii.gz"
    OUT_FILE = "MNI-Poly-AMU_T2_reg.nii.gz"
    GOLD_FILE = "gold.nii.gz"
    WARP_FILE = "../sct_testing_data/data/t2/warp_template2anat.nii.gz"
    DEST_FILE = "test_files/t2.nii.gz"

    def setUp(self):

        os.mkdir("ref")
        os.mkdir("gold")
        os.mkdir("cmd")

        # open("ref/"+self.OUT_FILE, "w+").close()
        # open("gold/"+self.GOLD_FILE, "w+").close()

    def tearDown(self):

        shutil.rmtree("ref")
        shutil.rmtree("cmd")
        shutil.rmtree("gold")

    def test_default(self):
        os.chdir("ref")
        try:
            Transform(input_filename="../"+self.INPUT_FILE, output_filename="../"+self.DEST_FILE, warp="../"+self.WARP_FILE).apply()
        except:
            pass
        os.chdir("../gold")
        try:
            sct.run("d_sct_apply_transfo.py -i ../"+self.INPUT_FILE+" -d ../"+self.DEST_FILE+" -w ../"+self.WARP_FILE)
        except:
            pass
        os.chdir('../cmd')
        try:
            sct.run("sct_apply_transfo -i ../"+self.INPUT_FILE+" -d ../"+self.DEST_FILE+" -w ../"+self.WARP_FILE)
        except:
            pass
        os.chdir("..")

        sct.printv("Asserting files")
        try:
            result = nibabel.load("ref/"+self.OUT_FILE).get_data().data
            cmd = nibabel.load("cmd/"+self.OUT_FILE).get_data().data
            expected = nibabel.load("gold/"+self.OUT_FILE).get_data().data
        except:
            pass

        self.assertEqual(result, expected)
        self.assertEqual(cmd, expected)

    def test_crop(self):
        os.chdir("ref")
        try:
            Transform(input_filename="../"+self.INPUT_FILE, output_filename="../"+self.DEST_FILE, warp="../"+self.WARP_FILE, crop=1).apply()
        except:
            pass
        os.chdir("../gold")
        try:
            sct.run("d_sct_apply_transfo.py -c 1 -i ../"+self.INPUT_FILE+" -d ../"+self.DEST_FILE+" -w ../"+self.WARP_FILE)
        except:
            pass
        os.chdir('../cmd')
        try:
            sct.run("sct_apply_transfo -c 1 -i ../"+self.INPUT_FILE+" -d ../"+self.DEST_FILE+" -w ../"+self.WARP_FILE)
        except:
            pass
        os.chdir("..")

        sct.printv("Asserting files")
        try:
            result = nibabel.load("ref/"+self.OUT_FILE).get_data().data
            cmd = nibabel.load("cmd/"+self.OUT_FILE).get_data().data
            expected = nibabel.load("gold/"+self.OUT_FILE).get_data().data
        except:
            pass

        self.assertEqual(result, expected)
        self.assertEqual(cmd, expected)

    def test_interp(self):
        os.chdir("ref")
        try:
            Transform(input_filename="../"+self.INPUT_FILE, output_filename="../"+self.DEST_FILE, warp="../"+self.WARP_FILE, interp="linear").apply()
        except:
            pass
        os.chdir("../gold")
        try:
            sct.run("d_sct_apply_transfo.py -x linear -i ../"+self.INPUT_FILE+" -d ../"+self.DEST_FILE+" -w ../"+self.WARP_FILE)
        except:
            pass
        os.chdir('../cmd')
        try:
            sct.run("sct_apply_transfo -x linear -i ../"+self.INPUT_FILE+" -d ../"+self.DEST_FILE+" -w ../"+self.WARP_FILE)
        except:
            pass
        os.chdir("..")

        sct.printv("Asserting files")
        try:
            result = nibabel.load("ref/"+self.OUT_FILE).get_data().data
            cmd = nibabel.load("cmd/"+self.OUT_FILE).get_data().data
            expected = nibabel.load("gold/"+self.OUT_FILE).get_data().data
        except:
            pass

        self.assertEqual(result, expected)
        self.assertEqual(cmd, expected)

if __name__ == '__main__':
    unittest.main()
