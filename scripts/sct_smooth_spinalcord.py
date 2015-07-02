#!/usr/bin/env python
#
# This program straightens the spinal cord of an anatomic image, apply a smoothing in the z dimension and apply
# the inverse warping field to get back the curved spinal cord but smoothed.
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2013 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Simon Levy
# Modified: 2014-09-01
#
# About the license: see the file LICENSE.TXT
#########################################################################################


# TODO: maybe no need to convert RPI at the beginning because strainghten spinal cord already does it!


import getopt
import os
import sys
import time
from msct_parser import Parser
import sct_utils as sct
from sct_orientation import set_orientation
from numpy import append, insert, nonzero, transpose, array
from nibabel import load, Nifti1Image, save
from scipy import ndimage
from copy import copy
from sct_apply_transfo import ApplyTransfo
from sct_straighten_spinalcord import SpinalCordStraightener
from sct_algorithm import Algorithm


class SmoothSpinalcord(Algorithm):

    def __init__(self, input_image, centerline_image, remove_temp_files=1, sigma = 3, verbose=1, produce_output=1):
        super(SmoothSpinalcord, self).__init__(input_image, produce_output, verbose)
        self.centerline_image = centerline_image
        self.sigma = sigma
        self.remove_temp_files = remove_temp_files
        self.verbose = verbose

    def execute(self):
        # check input file existence
        start_time = time.time()

        sct.check_file_exist(self.input_image)
        sct.check_file_exist(self.centerline_image)

        # Extract path/file/extension
        path_anat, file_anat, ext_anat = sct.extract_fname(self.input_image)
        path_centerline, file_centerline, ext_centerline = sct.extract_fname(self.centerline_image)

        path_tmp = 'tmp.'+time.strftime("%y%m%d%H%M%S")
        sct.run('mkdir '+path_tmp)

        sct.run('isct_c3d '+self.input_image+' -o '+path_tmp+'/anat.nii')
        sct.run('isct_c3d '+self.centerline_image+' -o '+path_tmp+'/centerline.nii')

        # go to tmp folder
        os.chdir(path_tmp)

        try:

            # Change orientation of the input image into RPI
            print '\nOrient input volume to RPI orientation...'
            set_orientation('anat.nii', 'RPI', 'anat_rpi.nii')
            # Change orientation of the input image into RPI
            print '\nOrient centerline to RPI orientation...'
            set_orientation('centerline.nii', 'RPI', 'centerline_rpi.nii')

            ## new

            ### Make sure that centerline file does not have halls
            file_c = load('centerline_rpi.nii')
            data_c = file_c.get_data()
            hdr_c = file_c.get_header()

            data_temp = copy(data_c)
            data_temp *= 0
            data_output = copy(data_c)
            data_output *= 0
            nx, ny, nz, nt, px, py, pz, pt = sct.get_dimension('centerline_rpi.nii')

            ## Change seg to centerline if it is a segmentation
            sct.printv('\nChange segmentation to centerline if it is a centerline...\n')
            z_centerline = [iz for iz in range(0, nz, 1) if data_c[:,:,iz].any() ]
            nz_nonz = len(z_centerline)
            if nz_nonz==0 :
                print '\nERROR: Centerline is empty'
                sys.exit()
            x_centerline = [0 for iz in range(0, nz_nonz, 1)]
            y_centerline = [0 for iz in range(0, nz_nonz, 1)]
            #print("z_centerline", z_centerline,nz_nonz,len(x_centerline))
            print '\nGet center of mass of the centerline ...'
            for iz in xrange(len(z_centerline)):
                x_centerline[iz], y_centerline[iz] = ndimage.measurements.center_of_mass(array(data_c[:,:,z_centerline[iz]]))
                data_temp[x_centerline[iz], y_centerline[iz], z_centerline[iz]] = 1

            ## Complete centerline
            sct.printv('\nComplete the halls of the centerline if there are any...\n')
            X,Y,Z = data_temp.nonzero()

            x_centerline_extended = [0 for i in range(0, nz, 1)]
            y_centerline_extended = [0 for i in range(0, nz, 1)]
            for iz in range(len(Z)):
                x_centerline_extended[Z[iz]] = X[iz]
                y_centerline_extended[Z[iz]] = Y[iz]

            X_centerline_extended = nonzero(x_centerline_extended)
            X_centerline_extended = transpose(X_centerline_extended)
            Y_centerline_extended = nonzero(y_centerline_extended)
            Y_centerline_extended = transpose(Y_centerline_extended)

            # initialization: we set the extrem values to avoid edge effects
            x_centerline_extended[0] = x_centerline_extended[X_centerline_extended[0]]
            x_centerline_extended[-1] = x_centerline_extended[X_centerline_extended[-1]]
            y_centerline_extended[0] = y_centerline_extended[Y_centerline_extended[0]]
            y_centerline_extended[-1] = y_centerline_extended[Y_centerline_extended[-1]]

            # Add two rows to the vector X_means_smooth_extended:
            # one before as means_smooth_extended[0] is now diff from 0
            # one after as means_smooth_extended[-1] is now diff from 0
            X_centerline_extended = append(X_centerline_extended, len(x_centerline_extended)-1)
            X_centerline_extended = insert(X_centerline_extended, 0, 0)
            Y_centerline_extended = append(Y_centerline_extended, len(y_centerline_extended)-1)
            Y_centerline_extended = insert(Y_centerline_extended, 0, 0)

            #recurrence
            count_zeros_x=0
            count_zeros_y=0
            for i in range(1,nz-1):
                if x_centerline_extended[i]==0:
                   x_centerline_extended[i] = 0.5*(x_centerline_extended[X_centerline_extended[i-1-count_zeros_x]] + x_centerline_extended[X_centerline_extended[i-count_zeros_x]])
                   count_zeros_x += 1
                if y_centerline_extended[i]==0:
                   y_centerline_extended[i] = 0.5*(y_centerline_extended[Y_centerline_extended[i-1-count_zeros_y]] + y_centerline_extended[Y_centerline_extended[i-count_zeros_y]])
                   count_zeros_y += 1

            # Save image centerline completed to be used after
            sct.printv('\nSave image completed: centerline_rpi_completed.nii...\n')
            for i in range(nz):
                data_output[x_centerline_extended[i],y_centerline_extended[i],i] = 1
            img = Nifti1Image(data_output, None, hdr_c)
            save(img, 'centerline_rpi_completed.nii')

            #end new


           # Straighten the spinal cord
            print '\nStraighten the spinal cord...'
            #sct.run('sct_straighten_spinalcord -i anat_rpi.nii -c centerline_rpi_completed.nii -x spline -v '+str(self.verbose))
            SpinalCordStraightener(input_image="anat_rpi.nii", centerline_filename="centerline_rpi_completed.nii", interpolation_warp="spline", verbose=self.verbose).execute()

            # Smooth the straightened image along z
            print '\nSmooth the straightened image along z...'
            sct.run('isct_c3d anat_rpi_straight.nii -smooth 0x0x'+str(self.sigma)+'vox -o anat_rpi_straight_smooth.nii', self.verbose)

            # Apply the reversed warping field to get back the curved spinal cord
            print '\nApply the reversed warping field to get back the curved spinal cord...'
            sct.run('sct_apply_transfo -i anat_rpi_straight_smooth.nii -o anat_rpi_straight_smooth_curved.nii -d anat.nii -w warp_straight2curve.nii.gz -x spline', self.verbose)
            # ApplyTransfo(input_image="anat_rpi_straight_smooth.nii", output_filename="anat.nii", warp="warp_straight2curve.nii.gz",verbose=self.verbose).execute()
        except Exception, e:
            print e.message
            print


        os.chdir('..')

        # Generate output file
        print '\nGenerate output file...'
        sct.generate_output_file(path_tmp+'/anat_rpi_straight_smooth_curved.nii', file_anat+'_smooth'+ext_anat)

        # Remove temporary files
        if self.remove_temp_files == 1:
            print('\nRemove temporary files...')
            sct.run('rm -rf '+path_tmp)

        # Display elapsed time
        elapsed_time = time.time() - start_time
        print '\nFinished! Elapsed time: '+str(int(round(elapsed_time)))+'s\n'

        # to view results
        sct.printv('Done! To view results, type:', self.verbose)
        sct.printv('fslview '+file_anat+' '+file_anat+'_smooth &\n', self.verbose, 'info')


if __name__ == "__main__":

    # Initialize parser
    parser = Parser(__file__)

    parser.usage.set_description(        '  Smooth the spinal cord along its centerline. Steps are: 1) Spinal cord is straightened (using\n' \
        '  centerline), 2) a Gaussian kernel is applied in the superior-inferior direction, 3) then cord is\n' \
        '  de-straightened as originally.\n')
    parser.add_option(name="-i",
                      type_value="image_nifti",
                      description="input image",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-c",
                      type_value="image_nifti",
                      description="Centerline image",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-s",
                      type_value="float",
                      description="Sigma for the gaussian smoothing",
                      mandatory=False,
                      default_value=3,
                      example="3")
    parser.add_option(name="-r",
                      type_value="int",
                      description="Sigma for the gaussian smoothing",
                      mandatory=False,
                      default_value=3,
                      example="3")
    parser.add_option(name="-v",
                      type_value="multiple_choice",
                      description="1: display on, 0: display off (default)",
                      mandatory=False,
                      example=['0', '1'],
                      default_value='1')

    arguments = parser.parse(sys.argv[1:])

    input_filename = arguments["-i"]
    centerline = arguments["-c"]

    smooth = SmoothSpinalcord(input_image=input_filename, centerline_image=centerline)

    if "-s" in arguments:
        smooth.sigma = arguments["-s"]
    if "-r" in arguments:
        smooth.remove_temp_files = arguments["-r"]
    if "-v" in arguments:
        smooth.verbose = arguments["-v"]

    smooth.execute()