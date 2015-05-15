__author__ = 'olcoma'

import unittest
import os
import sys
sys.path.append("../../scripts")
import sct_utils as sct
import nibabel
from osct_crop_image import ImageCropper


class TestCropImage(unittest.TestCase):
    def test_star_end(self):
        # init crop object
        original_image = "test_files/t2.nii.gz"
        out_file = "start_end.nii.gz"
        gold_file = "start_end_gold.nii.gz"

        # Creates temp files if not present
        open(out_file, "w+").close()
        open(gold_file, "w+").close()

        # testing start and end parameters
        start_end_cropper = ImageCropper(input_file=original_image, output_file=out_file, dim=[1, 2],
                                         start=[10.0, 5.0], end=[150.0, 40.0], verbose=0)
        # produces result file
        start_end_cropper.crop()
        # produces golden file
        sct.run("isct_crop_image -i "+original_image+" -o "+gold_file+" -start 10,5 -end 150,40 -dim 1,2 -v 0", 0)
        # get image contents
        result = nibabel.load(out_file).get_data().data
        expected = nibabel.load(gold_file).get_data().data
        # remove temporary files
        os.remove(out_file)
        os.remove(gold_file)
        # assert image contents
        self.assertEqual(result, expected, "crop image : start/end test")

    def test_mask(self):
        original_image = "test_files/t2_RPI.nii.gz"
        out_file = "mask.nii.gz"
        gold_file = "mask_gold.nii.gz"
        mask_file = "test_files/t2_mask.nii.gz"

        open(out_file, "w+").close()
        open(gold_file, "w+").close()

        ImageCropper(input_file=original_image, output_file=out_file, mask=mask_file, verbose=0).crop()
        sct.run("isct_crop_image -i "+original_image+" -o "+gold_file+" -m "+mask_file, 0)
        # get raw data from file
        result = nibabel.load(out_file).get_data().data
        expected = nibabel.load(gold_file).get_data().data

        # remove temporary files
        os.remove(out_file)
        os.remove(gold_file)
        # assert image contents
        self.assertEqual(result, expected, "crop image : mask test")

    def test_background(self):
        # init crop object
        original_image = "test_files/t2.nii.gz"
        out_file = "background.nii.gz"
        gold_file = "background_gold.nii.gz"

        # Creates temp files if not present
        open(out_file, "w+").close()
        open(gold_file, "w+").close()

        # testing start and end parameters
        start_end_cropper = ImageCropper(input_file=original_image, output_file=out_file, dim=[1, 2],
                                         start=[10.0, 5.0], end=[150.0, 40.0], verbose=0, background=5)
        # produces result file
        start_end_cropper.crop()
        # produces golden file
        sct.run("isct_crop_image -i "+original_image+" -o "+gold_file+" -start 10,5 -end 150,40 -dim 1,2 -v 0 -b 5", 0)
        # get image contents
        result = nibabel.load(out_file).get_data().data
        expected = nibabel.load(gold_file).get_data().data
        # remove temporary files
        os.remove(out_file)
        os.remove(gold_file)
        # assert image contents
        self.assertEqual(result, expected, "crop image : background test")

    def test_bmax(self):
        # init crop object
        original_image = "test_files/t2_seg.nii.gz"
        out_file = "bmax.nii.gz"
        gold_file = "bmax_gold.nii.gz"

        # Creates temp files if not present
        open(out_file, "w+").close()
        open(gold_file, "w+").close()

        # testing start and end parameters
        start_end_cropper = ImageCropper(input_file=original_image, output_file=out_file, bmax=True, verbose=0)
        # produces result file
        start_end_cropper.crop()
        # produces golden file
        sct.run("isct_crop_image -i "+original_image+" -o "+gold_file+" -bmax", 0)
        # get image contents
        result = nibabel.load(out_file).get_data().data
        expected = nibabel.load(gold_file).get_data().data
        # remove temporary files
        os.remove(out_file)
        os.remove(gold_file)
        # assert image contents
        self.assertEqual(result, expected, "crop image : maximum cropping test")

    def test_ref(self):
        # init crop object
        original_image = "test_files/t2.nii.gz"
        out_file = "ref.nii.gz"
        gold_file = "ref_gold.nii.gz"
        ref_file = "test_files/ref_file.nii.gz"

        # Creates temp files if not present
        open(out_file, "w+").close()
        open(gold_file, "w+").close()

        # produces result file
        cropper = ImageCropper(input_file=original_image, output_file=out_file, ref=ref_file, verbose=0)
        cropper.crop()
        # produces golden file
        sct.run("isct_crop_image -i "+original_image+" -o "+gold_file+" -ref "+ref_file, 0)
        # get image contents
        result = nibabel.load(out_file).get_data().data
        expected = nibabel.load(gold_file).get_data().data
        # remove temporary files
        os.remove(out_file)
        os.remove(gold_file)
        # assert image contents
        self.assertEqual(result, expected, "crop image : reference cropping test")


if __name__ == '__main__':
    unittest.main()
