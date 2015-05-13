# !/usr/bin/env python
#########################################################################################
#
# sct_create_mask obect equivalent. Creates a mask along the Z axis
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Benjamin Leener, Julien Cohen-Adad, Olivier Comtois
# Modified: 2015-05-13
#
# About the license: see the file LICENSE.TXT
#########################################################################################

import sys
from msct_parser import Parser
import os
import getopt
import commands
from msct_image import Image
import sct_utils as sct
import time
import numpy
import nibabel
from scipy import ndimage
from sct_orientation import get_orientation, set_orientation


class Mask:

    # class constants definition
    OUTPUT_PREFIX = "mask_"
    METHOD_LIST = ['coord', 'point', 'centerline', 'center']
    SHAPE_LIST = ['cylinder', 'box', 'gaussian']
    DEFAULT_SHAPE = "cylinder"
    DEFAULT_METHOD = "center"
    DEFAULT_SIZE = 41

    def __init__(self, input_filename, output_filename=None, method=DEFAULT_METHOD, shape=DEFAULT_SHAPE, size=DEFAULT_SIZE, verbose=1, rm_tmp_files=1):

        self.input_file = input_filename
        self.output_file = output_filename
        self.method = method
        self.shape = shape
        self.size = size
        self.verbose = verbose
        self.rm_tmp_files = rm_tmp_files
        self.result = None

    def create_mask(self):
        """
        This method creates a mask and returns the result either through a file or as an msct_image Image object

        """

        fsloutput = 'export FSLOUTPUTTYPE=NIFTI; '

        method_list = self.method
        method_type = method_list[0]

        # checking if method is valid
        if method_type not in Mask.METHOD_LIST:
            sct.printv('\nERROR in '+os.path.basename(__file__)+': Method "'+self.method+'" is not recognized. \n', self.verbose, 'error')

        if not method_type == 'center':
            method_val = method_list[1]

        # checking if shape is valid
        if self.shape not in Mask.SHAPE_LIST:
            sct.printv('\nERROR in '+os.path.basename(__file__)+': Shape "'+self.shape+'" is not recognized. \n', self.verbose, 'error')

        # checking file existence
        sct.printv('\ncheck existence of input files...', self.verbose)
        sct.check_file_exist(self.input_file, self.verbose)
        if method_type == 'centerline':
            sct.check_file_exist(method_val, self.verbose)

        # checking orientation in RPI
        if not get_orientation(self.input_file) == 'RPI':
            sct.printv('\nERROR in '+os.path.basename(__file__)+': Orientation of input image should be RPI. Use sct_orientation to put your image in RPI.\n', self.verbose, 'error')

        # display input parameters
        sct.printv('\nInput parameters:', self.verbose)
        sct.printv('  data ..................'+self.input_file, self.verbose)
        sct.printv('  method ................'+method_type, self.verbose)

        # Extract path/file/extension
        path_data, file_data, ext_data = sct.extract_fname(self.input_file)

        # Get output folder and file name
        if self.output_file is None:
            self.output_file = Mask.OUTPUT_PREFIX+file_data+ext_data

        # creating temporary folder
        path_tmp = sct.slash_at_the_end('tmp.'+time.strftime("%y%m%d%H%M%S"), 1)
        os.mkdir(path_tmp)

        # Copying input data to tmp folder and convert to nii
        # NB: cannot use c3d here because c3d cannot convert 4D data.
        # TODO : replace the run commands by os calls
        sct.printv('\nCopying input data to tmp folder and convert to nii...', self.verbose)
        sct.run('cp '+self.input_file+' '+path_tmp+'data'+ext_data, self.verbose)
        if method_type == 'centerline':
            sct.run('isct_c3d '+method_val+' -o '+path_tmp+'/centerline.nii.gz')

        # go to tmp folder
        os.chdir(path_tmp)

        # convert to nii format
        sct.run('fslchfiletype NIFTI data', self.verbose)

        # Get dimensions of data
        nx, ny, nz, nt, px, py, pz, pt = sct.get_dimension('data.nii')
        sct.printv('  ' + str(nx) + ' x ' + str(ny) + ' x ' + str(nz)+ ' x ' + str(nt), self.verbose)
        # in case user input 4d data
        if nt != 1:
            sct.printv('WARNING in '+os.path.basename(__file__)+': Input image is 4d but output mask will 3D.', self.verbose, 'warning')
            # extract first volume to have 3d reference
            sct.run(fsloutput+'fslroi data data -0 1', self.verbose)

        if method_type == 'coord':
            # parse to get coordinate
            coord = map(int, method_val.split('x'))

        if method_type == 'point':
            # get file name
            fname_point = method_val
            # extract coordinate of point
            sct.printv('\nExtract coordinate of point...', self.verbose)
            # TODO : Running outside script
            status, output = sct.run('sct_label_utils -i '+fname_point+' -t display-voxel', self.verbose)
            # parse to get coordinate
            coord = output[output.find('Position=')+10:-17].split(',')

        if method_type == 'center':
            # set coordinate at center of FOV
            coord = round(float(nx)/2), round(float(ny)/2)

        if method_type == 'centerline':
            # get name of centerline from user argument
            fname_centerline = 'centerline.nii.gz'
        else:
            # generate volume with line along Z at coordinates 'coord'
            sct.printv('\nCreate line...', self.verbose)
            fname_centerline = Mask.create_line('data.nii', coord, nz)

        # create mask
        sct.printv('\nCreate mask...', self.verbose)
        centerline = nibabel.load(fname_centerline)  # open centerline
        hdr = centerline.get_header()  # get header
        hdr.set_data_dtype('uint8')  # set imagetype to uint8
        data_centerline = centerline.get_data()  # get centerline
        z_centerline = [iz for iz in range(0, nz, 1) if data_centerline[:, :, iz].any()]
        nz = len(z_centerline)
        # get center of mass of the centerline
        cx = [0] * nz
        cy = [0] * nz
        for iz in range(0, nz, 1):
            cx[iz], cy[iz] = ndimage.measurements.center_of_mass(numpy.array(data_centerline[:, :, z_centerline[iz]]))

        # create 2d masks
        file_mask = 'data_mask'
        for iz in range(nz):
            center = numpy.array([cx[iz], cy[iz]])
            mask2d = Mask.create_mask2d(center, self.shape, self.size, nx, ny)
            # Write NIFTI volumes
            img = nibabel.Nifti1Image(mask2d, None, hdr)
            nibabel.save(img, (file_mask+str(iz)+'.nii'))
        # merge along Z
        cmd = 'fslmerge -z mask '
        for iz in range(nz):
            cmd = cmd + file_mask+str(iz)+' '
        status, output = sct.run(cmd, self.verbose)

        # copy geometry
        sct.run(fsloutput+'fslcpgeom data mask', self.verbose)

        # come back to parent folder
        os.chdir('..')

        # Generate output files
        sct.printv('\nGenerate output files...', self.verbose)
        sct.generate_output_file(path_tmp+'mask.nii.gz', self.output_file)

        # Remove temporary files
        if self.rm_tmp_files == 1:
            sct.printv('\nRemove temporary files...', self.verbose)
            sct.run('rm -rf '+path_tmp, self.verbose)

        # to view results
        sct.printv('\nDone! To view results, type:', self.verbose)
        sct.printv('fslview '+self.input_file+' '+self.output_file+' -l Red -t 0.5 &', self.verbose, 'info')
        print

        self.result = Image.loadFromPath(self.output_filename, 0)
        return self.result


    # create_line
    # ==========================================================================================
    def create_line(self, fname, coord, nz):

        # duplicate volume (assumes input file is nifti)
        sct.run('cp '+fname+' line.nii', self.verbose)

        # set all voxels to zero
        sct.run('isct_c3d line.nii -scale 0 -o line.nii', self.verbose)

        # loop across z and create a voxel at a given XY coordinate
        for iz in range(nz):
            sct.run('sct_label_utils -i line.nii -o line.nii -t add -x '+str(int(coord[0]))+','+str(int(coord[1]))+','+str(iz)+',1', self.verbose)

        return 'line.nii'

    # create_mask2d
    # ==========================================================================================
    def create_mask2d(self, center, shape, size, nx, ny):

        # initialize 2d grid
        xx, yy = numpy.mgrid[:nx, :ny]
        mask2d = numpy.zeros((nx, ny))
        xc = center[0]
        yc = center[1]
        radius = round(float(size+1)/2)  # add 1 because the radius includes the center.

        if shape == 'box':
            mask2d[xc-radius:xc+radius+1, yc-radius:yc+radius+1] = 1

        elif shape == 'cylinder':
            mask2d = ((xx-xc)**2 + (yy-yc)**2 <= radius**2)*1

        elif shape == 'gaussian':
            sigma = float(radius)
            mask2d = numpy.exp(-(((xx-xc)**2)/(2*(sigma**2)) + ((yy-yc)**2)/(2*(sigma**2))))

        # import matplotlib.pyplot as plt
        # plt.imshow(mask2d)
        # plt.show()

        return mask2d

if __name__ == "__main__":
    # Initialize parser,
    parser = Parser(__file__)

    parser.usage.set_description('Creates a mask with a specific method and shape and returns it as a file')
    parser.add_option(name="-i",
                      type_value="file",
                      description="input image.",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-m",
                      type_value=[[','], 'str'],
                      description="""method to generate mask and associated value.\ncoord: X,Y coordinate of center of mask. E.g.: coord,20x15\npoint: volume that contains a single point. E.g.: point,label.nii.gz\ncenter: mask is created at center of FOV. In that case, "val" is not required.\ncenterline: volume that contains centerline. E.g.: centerline,my_centerline.nii")""",
                      mandatory=False,
                      default_value=Mask.DEFAULT_METHOD)
    parser.add_option(name="-s",
                      type_value="int",
                      description="size in voxel. Odd values are better (for mask to be symmetrical).If shape=gaussian, size corresponds to sigma",
                      mandatory=False,
                      default_value=Mask.DEFAULT_SIZE,
                      example="41")
    parser.add_option(name="-f",
                      type_value="str",
                      description="shape of the mask.",
                      mandatory=False,
                      default_value=Mask.DEFAULT_SHAPE,
                      example="gaussian")
    parser.add_option(name="-o",
                      type_value="file",
                      description="output image.",
                      mandatory=False,
                      example="test.nii.gz")
    parser.add_option(name="-r",
                      type_value="multiple_choice",
                      description="Remove temporary files.",
                      mandatory=False,
                      default_value=1,
                      example=['0', '1'])
    parser.add_option(name="-v",
                      type_value="multiple_choice",
                      description="Verbose",
                      mandatory=False,
                      default_value=0,
                      example=['0', '1'])
