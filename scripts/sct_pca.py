#!/usr/bin/env python
#########################################################################################
#
# Principal Component Analysis
#
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Augustin Roux
# Modified: 2014-11-20
#
# About the license: see the file LICENSE.TXT
#########################################################################################
from matplotlib.mlab import PCA
import numpy as np
from msct_image import Image_sct
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from PIL import Image
import scipy
import copy


def main():
    # a = [[1, 0], [-1, 0], [6, 1], [9, -1.5]]
    img = Image_sct('/home/django/aroux/Desktop/MNI-Poly-AMU_WM_IRP.nii.gz')
    print len(img.data)
    dataset = img.slices()
    dataMat = np.array(dataset)
    #dataMat = np.transpose(dataMat)
    myPCA = PCA(dataMat)
    print myPCA
    print myPCA.numrows
    print myPCA.numcols
    x = []
    y = []
    z = []
    for s in dataMat:
        l = myPCA.project(s)
        x.append(l[0])
        y.append(l[1])
        z.append(l[2])
    #print x

    #get_similar_images(dataMat, myPCA, img)
    #plot(x, y, z)
    save_mu(myPCA)


def save_mu(myPCA):
    scipy.misc.imsave('mu.jpg', myPCA.mu.reshape((19, 12)))


def plot(x, y, z):
    fig = plt.figure()
    ax = Axes3D(fig)
    ax.plot(x, y, z, '.')
    ax.set_xlabel('m1')
    ax.set_ylabel('m2')
    ax.set_zlabel('m3')
    plt.show()


def get_similar_images(dataMat, myPCA, img):
    i = -1
    print len(dataMat)
    for image in dataMat:
        print i
        i += 1
        l = myPCA.project(image)
        index = l[0]
        # if index > 0:
        print index
        im = img.data[i]
        print scipy.misc.imsave(str(index) + "_" + str(i) + '.jpg', copy.copy(im))
        print "i = " + str(i) + "\n"
        #print img.data[i]
        # im = Image.fromarray(im)
        # im.save(str(index) + ".jpeg")


if __name__ == "__main__":
    main()
