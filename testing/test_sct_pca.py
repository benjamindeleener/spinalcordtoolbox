import sct_pca
from msct_image import Image_sct
import commands
import pytest


class Data:
    def __init__(self):
        status, path_sct_testing = commands.getstatusoutput('echo $SCT_TESTING_DATA_DIR')
        self.path = path_sct_testing
        self.folder_data = '/template/'
        self.file_data = 'MNI-Poly-AMU_T2_PCA.nii.gz'
        self.img = None

    def init_image_sct(self):
        self.img = Image_sct(self.path + self.folder_data + self.file_data)


@pytest.fixture()
def data1():
    data = Data()
    return data


@pytest.fixture()
def data2():
    data = Data()
    data.init_image_sct()
    return data


def test_image_sct(data1):
    data1.init_image_sct()


def test_sct_(data2):
    slice_array = data2.img.slices()

