#!/usr/bin/env python
__author__ = 'olcoma'

import sys
import os
import math
import time

import scipy
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import nibabel

from sct_orientation import set_orientation
import sct_utils as sct
from msct_image import Image
from sct_class.Algorithm import Algorithm


class LineBuilder(object):
    def __init__(self, line):
        self.line = line
        self.xs = list(line.get_xdata())
        self.ys = list(line.get_ydata())
        self.cid = line.figure.canvas.mpl_connect('button_press_event', self)

    def __call__(self, event):
        print 'click', event
        if event.inaxes != self.line.axes:
            # if user clicked outside the axis, ignore
            return
        if event.button == 2 or event.button == 3:
            # if right button, remove last point
            del self.xs[-1]
            del self.ys[-1]
        if len(self.xs) >= 2:
            # if user already clicked 2 times, ignore
            return
        if event.button == 1:
            # if left button, add point
            self.xs.append(event.xdata)
            self.ys.append(event.ydata)
        # update figure
        self.line.set_data(self.xs, self.ys)
        self.line.figure.canvas.draw()


class ImageCropper(Algorithm):
    def __init__(self, input_image, output_filename=None, mask=None, start=None, end=None, shift=None, dim=None, background=None, bmax=False, ref=None, mesh=None, verbose=1, produce_output=True, rm_tmp_file=0):
        super(ImageCropper, self).__init__(input_image, produce_output, verbose)
        self.output_filename = output_filename
        self._mask = mask
        self.start = start
        self.end = end
        self.dim = dim
        self.shift = shift
        self.background = background
        self.bmax = bmax
        self.ref = ref
        self.mesh = mesh
        self.cmd = None
        self.rm_tmp_files = rm_tmp_file

    def execute(self):

         # create command line
        self.cmd = "isct_crop_image" + " -i " + self.input_image + " -o " + self.output_filename
        # Handling optional arguments
        if self._mask is not None:
            self.cmd += " -m " + self._mask
        if self.start is not None:
            self.cmd += " -start " + ','.join(map(str, self.start))
        if self.end is not None:
            self.cmd += " -end " + ','.join(map(str, self.end))
        if self.dim is not None:
            self.cmd += " -dim " + ','.join(map(str, self.dim))
        if self.shift is not None:
            self.cmd += " -shift " + ','.join(map(str, self.shift))
        if self.background is not None:
            self.cmd += " -b " + str(self.background)
        if self.bmax is True:
            self.cmd += " -bmax"
        if self.ref is not None:
            self.cmd += " -ref " + self.ref
        if self.mesh is not None:
            self.cmd += " -mesh " + self.mesh

        verb = 0
        if self.verbose == 1:
            verb = 2
        # Run command line
        sct.run(self.cmd, verb)

        result = Image(self.output_filename)

        # removes the output file created by the script if it is not needed
        if not self.produce_output:
            try:
                os.remove(self.output_filename)
            except OSError:
                sct.printv("WARNING : Couldn't remove output file. Either it is opened elsewhere or "
                           "it doesn't exist.", 0, 'warning')
        else:
            # Complete message
            sct.printv('\nDone! To view results, type:', self.verbose)
            sct.printv("fslview "+self.output_filename+" &\n", self.verbose, 'info')

        return result

    def crop_with_gui(self):
        # Initialization
        fname_data = self.input_filename
        suffix_out = '_crop'
        remove_temp_files = self.rm_tmp_files
        verbose = self.verbose

        # for faster processing, all outputs are in NIFTI
        fsloutput = 'export FSLOUTPUTTYPE=NIFTI; '

        # Check file existence
        sct.printv('\nCheck file existence...', verbose)
        sct.check_file_exist(fname_data)

        # Get dimensions of data
        sct.printv('\nGet dimensions of data...', verbose)
        nx, ny, nz, nt, px, py, pz, pt = sct.get_dimension(fname_data)
        sct.printv('.. '+str(nx)+' x '+str(ny)+' x '+str(nz), verbose)
        # check if 4D data
        if not nt == 1:
            sct.printv('\nERROR in '+os.path.basename(__file__)+': Data should be 3D.\n', 1, 'error')
            sys.exit(2)

        # print arguments
        print '\nCheck parameters:'
        print '  data ................... '+fname_data
        print

        # Extract path/file/extension
        path_data, file_data, ext_data = sct.extract_fname(fname_data)
        path_out, file_out, ext_out = '', file_data+suffix_out, ext_data

        # create temporary folder
        path_tmp = 'tmp.'+time.strftime("%y%m%d%H%M%S")+'/'
        sct.run('mkdir '+path_tmp)

        # copy files into tmp folder
        sct.run('isct_c3d '+fname_data+' -o '+path_tmp+'data.nii')

        # go to tmp folder
        os.chdir(path_tmp)

        # change orientation
        sct.printv('\nChange orientation to RPI...', verbose)
        set_orientation('data.nii', 'RPI', 'data_rpi.nii')

        # get image of medial slab
        sct.printv('\nGet image of medial slab...', verbose)
        image_array = nibabel.load('data_rpi.nii').get_data()
        nx, ny, nz = image_array.shape
        scipy.misc.imsave('image.jpg', image_array[math.floor(nx/2), :, :])

        # Display the image
        sct.printv('\nDisplay image and get cropping region...', verbose)
        fig = plt.figure()
        # fig = plt.gcf()
        # ax = plt.gca()
        ax = fig.add_subplot(111)
        img = mpimg.imread("image.jpg")
        implot = ax.imshow(img.T)
        implot.set_cmap('gray')
        plt.gca().invert_yaxis()
        # mouse callback
        ax.set_title('Left click on the top and bottom of your cropping field.\n Right click to remove last point.\n Close window when your done.')
        line, = ax.plot([], [], 'ro')  # empty line
        cropping_coordinates = LineBuilder(line)
        plt.show()
        # disconnect callback
        # fig.canvas.mpl_disconnect(line)

        # check if user clicked two times
        if len(cropping_coordinates.xs) != 2:
            sct.printv('\nERROR: You have to select two points. Exit program.\n', 1, 'error')
            sys.exit(2)

        # convert coordinates to integer
        zcrop = [int(i) for i in cropping_coordinates.ys]

        # sort coordinates
        zcrop.sort()

        # crop image
        sct.printv('\nCrop image...', verbose)
        sct.run(fsloutput+'fslroi data_rpi.nii data_rpi_crop.nii 0 -1 0 -1 '+str(zcrop[0])+' '+str(zcrop[1]-zcrop[0]+1))

        # come back to parent folder
        os.chdir('..')

        sct.printv('\nGenerate output files...', verbose)
        sct.generate_output_file(path_tmp+'data_rpi_crop.nii', path_out+file_out+ext_out)

        # Remove temporary files
        if remove_temp_files == 1:
            print('\nRemove temporary files...')
            sct.run('rm -rf '+path_tmp)

        # to view results
        print '\nDone! To view results, type:'
        print 'fslview '+path_out+file_out+ext_out+' &'
        print
