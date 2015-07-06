#!/usr/bin/env python
#########################################################################################
#
# Perform various types of processing from the spinal cord segmentation (e.g. extract centerline, compute CSA, etc.).
# (extract_centerline) extract the spinal cord centerline from the segmentation. Output file is an image in the same
# space as the segmentation.
#
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Author: Benjamin De Leener, Julien Touati, Gabriel Mangeat, Olivier Comtois
# Modified: 2014-07-20 by jcohenadad
#
# About the license: see the file LICENSE.TXT
#########################################################################################
import sys
# import getopt
import os
# import commands
import time

import scipy
import nibabel
import numpy as np

import sct_utils as sct
from msct_nurbs import NURBS
from sct_straighten_spinalcord import smooth_centerline
from sct_orientation import get_orientation, set_orientation
from msct_base_classes import Algorithm, BaseScript
from msct_parser import Parser

#=======================================================================================================================
# b_spline_centerline
#=======================================================================================================================
def b_spline_centerline(x_centerline,y_centerline,z_centerline):

    print '\nFitting centerline using B-spline approximation...'
    points = [[x_centerline[n],y_centerline[n],z_centerline[n]] for n in range(len(x_centerline))]
    nurbs = NURBS(3,3000,points)  # BE very careful with the spline order that you choose : if order is too high ( > 4 or 5) you need to set a higher number of Control Points (cf sct_nurbs ). For the third argument (number of points), give at least len(z_centerline)+500 or higher

    P = nurbs.getCourbe3D()
    x_centerline_fit=P[0]
    y_centerline_fit=P[1]
    Q = nurbs.getCourbe3D_deriv()
    x_centerline_deriv=Q[0]
    y_centerline_deriv=Q[1]
    z_centerline_deriv=Q[2]

    return x_centerline_fit, y_centerline_fit,x_centerline_deriv,y_centerline_deriv,z_centerline_deriv


#=======================================================================================================================
# Normalization
#=======================================================================================================================
def normalize(vect):
    norm=np.linalg.norm(vect)
    return vect/norm


#=======================================================================================================================
# Ellipse fitting for a set of data
#=======================================================================================================================
#http://nicky.vanforeest.com/misc/fitEllipse/fitEllipse.html
def Ellipse_fit(x,y):
    x = x[:,np.newaxis]
    y = y[:,np.newaxis]
    D =  np.hstack((x*x, x*y, y*y, x, y, np.ones_like(x)))
    S = np.dot(D.T,D)
    C = np.zeros([6,6])
    C[0,2] = C[2,0] = 2
    C[1,1] = -1
    E, V =  np.linalg.eig(np.dot(np.linalg.inv(S), C))
    n = np.argmax(np.abs(E))
    a = V[:,n]
    return a


#=======================================================================================================================
# Getting a and b parameter for fitted ellipse
#=======================================================================================================================
def ellipse_dim(a):
    b,c,d,f,g,a = a[1]/2, a[2], a[3]/2, a[4]/2, a[5], a[0]
    up = 2*(a*f*f+c*d*d+g*b*b-2*b*d*f-a*c*g)
    down1=(b*b-a*c)*( (c-a)*np.sqrt(1+4*b*b/((a-c)*(a-c)))-(c+a))
    down2=(b*b-a*c)*( (a-c)*np.sqrt(1+4*b*b/((a-c)*(a-c)))-(c+a))
    res1=np.sqrt(up/down1)
    res2=np.sqrt(up/down2)
    return np.array([res1, res2])


#=======================================================================================================================
# Detect edges of an image
#=======================================================================================================================
def edge_detection(f):

    import Image

    #sigma = 1.0
    img = Image.open(f) #grayscale
    imgdata = np.array(img, dtype = float)
    G = imgdata
    #G = ndi.filters.gaussian_filter(imgdata, sigma)
    gradx = np.array(G, dtype = float)
    grady = np.array(G, dtype = float)

    mask_x = np.array([[-1,0,1],[-2,0,2],[-1,0,1]])

    mask_y = np.array([[1,2,1],[0,0,0],[-1,-2,-1]])

    width = img.size[1]
    height = img.size[0]

    for i in range(1, width-1):
        for j in range(1, height-1):

            px = np.sum(mask_x*G[(i-1):(i+1)+1,(j-1):(j+1)+1])
            py = np.sum(mask_y*G[(i-1):(i+1)+1,(j-1):(j+1)+1])
            gradx[i][j] = px
            grady[i][j] = py

    mag = scipy.hypot(gradx,grady)

    treshold = np.max(mag)*0.9

    for i in range(width):
        for j in range(height):
            if mag[i][j]>treshold:
                mag[i][j]=1
            else:
                mag[i][j] = 0

    return mag

def extract_centerline(fname_segmentation, remove_temp_files, verbose = 0, algo_fitting = 'hanning', type_window = 'hanning', window_length = 80):
   # Extract path, file and extension
    fname_segmentation = os.path.abspath(fname_segmentation)
    path_data, file_data, ext_data = sct.extract_fname(fname_segmentation)

    # create temporary folder
    path_tmp = 'tmp.'+time.strftime("%y%m%d%H%M%S")
    sct.run('mkdir '+path_tmp)

    # copy files into tmp folder
    sct.run('cp '+fname_segmentation+' '+path_tmp)

    # go to tmp folder
    os.chdir(path_tmp)

    try:
        # Change orientation of the input centerline into RPI
        sct.printv('\nOrient centerline to RPI orientation...', verbose)
        fname_segmentation_orient = 'segmentation_rpi' + ext_data
        set_orientation(file_data+ext_data, 'RPI', fname_segmentation_orient)

        # Get dimension
        sct.printv('\nGet dimensions...', verbose)
        nx, ny, nz, nt, px, py, pz, pt = sct.get_dimension(fname_segmentation_orient)
        sct.printv('.. matrix size: '+str(nx)+' x '+str(ny)+' x '+str(nz), verbose)
        sct.printv('.. voxel size:  '+str(px)+'mm x '+str(py)+'mm x '+str(pz)+'mm', verbose)

        # Extract orientation of the input segmentation
        orientation = get_orientation(file_data+ext_data)
        sct.printv('\nOrientation of segmentation image: ' + orientation, verbose)

        sct.printv('\nOpen segmentation volume...', verbose)
        file = nibabel.load(fname_segmentation_orient)
        data = file.get_data()
        hdr = file.get_header()

        # Extract min and max index in Z direction
        X, Y, Z = (data>0).nonzero()
        min_z_index, max_z_index = min(Z), max(Z)
        x_centerline = [0 for i in range(0,max_z_index-min_z_index+1)]
        y_centerline = [0 for i in range(0,max_z_index-min_z_index+1)]
        z_centerline = [iz for iz in range(min_z_index, max_z_index+1)]
        # Extract segmentation points and average per slice
        for iz in range(min_z_index, max_z_index+1):
            x_seg, y_seg = (data[:,:,iz]>0).nonzero()
            x_centerline[iz-min_z_index] = np.mean(x_seg)
            y_centerline[iz-min_z_index] = np.mean(y_seg)
        for k in range(len(X)):
            data[X[k], Y[k], Z[k]] = 0

        # extract centerline and smooth it
        x_centerline_fit, y_centerline_fit, z_centerline_fit, x_centerline_deriv,y_centerline_deriv,z_centerline_deriv = smooth_centerline(fname_segmentation_orient, type_window=type_window, window_length=window_length, algo_fitting=algo_fitting, verbose=verbose)

        if verbose == 2:
                import matplotlib.pyplot as plt

                #Creation of a vector x that takes into account the distance between the labels
                nz_nonz = len(z_centerline)
                x_display = [0 for i in range(x_centerline_fit.shape[0])]
                y_display = [0 for i in range(y_centerline_fit.shape[0])]
                for i in range(0, nz_nonz, 1):
                    x_display[int(z_centerline[i]-z_centerline[0])] = x_centerline[i]
                    y_display[int(z_centerline[i]-z_centerline[0])] = y_centerline[i]

                plt.figure(1)
                plt.subplot(2,1,1)
                plt.plot(z_centerline_fit, x_display, 'ro')
                plt.plot(z_centerline_fit, x_centerline_fit)
                plt.xlabel("Z")
                plt.ylabel("X")
                plt.title("x and x_fit coordinates")

                plt.subplot(2,1,2)
                plt.plot(z_centerline_fit, y_display, 'ro')
                plt.plot(z_centerline_fit, y_centerline_fit)
                plt.xlabel("Z")
                plt.ylabel("Y")
                plt.title("y and y_fit coordinates")
                plt.show()


        # Create an image with the centerline
        for iz in range(min_z_index, max_z_index+1):
            data[round(x_centerline_fit[iz-min_z_index]), round(y_centerline_fit[iz-min_z_index]), iz] = 1 # if index is out of bounds here for hanning: either the segmentation has holes or labels have been added to the file
        # Write the centerline image in RPI orientation
        hdr.set_data_dtype('uint8') # set imagetype to uint8
        sct.printv('\nWrite NIFTI volumes...', verbose)
        img = nibabel.Nifti1Image(data, None, hdr)
        nibabel.save(img, 'centerline.nii.gz')
        sct.generate_output_file('centerline.nii.gz', file_data+'_centerline'+ext_data, verbose)

        # create a txt file with the centerline
        file_name = file_data+'_centerline'+'.txt'
        sct.printv('\nWrite text file...', verbose)
        file_results = open(file_name, 'w')
        for i in range(min_z_index, max_z_index+1):
            file_results.write(str(int(i)) + ' ' + str(x_centerline_fit[i-min_z_index]) + ' ' + str(y_centerline_fit[i-min_z_index]) + '\n')
        file_results.close()

        # Copy result into parent folder
        sct.run('cp '+file_name+' ../')

        del data

    except Exception, e:
        raise e
    # come back to parent folder
    os.chdir('..')

    # Change orientation of the output centerline into input orientation
    sct.printv('\nOrient centerline image to input orientation: ' + orientation, verbose)
    fname_segmentation_orient = 'tmp.segmentation_rpi' + ext_data
    set_orientation(path_tmp+'/'+file_data+'_centerline'+ext_data, orientation, file_data+'_centerline'+ext_data)

   # Remove temporary files
    if remove_temp_files:
        sct.printv('\nRemove temporary files...', verbose)
        sct.run('rm -rf '+path_tmp, verbose)

    return file_data+'_centerline'+ext_data

#=======================================================================================================================
# create text file info_label.txt
#=======================================================================================================================
def create_info_label(file_name, path_folder, fname_seg):

    os.chdir(path_folder)
    file_info_label = open(file_name, 'w')
    file_info_label.write('# Spinal cord segmentation\n')
    file_info_label.write('# ID, name, file\n')
    file_info_label.write('0, mean CSA, '+fname_seg)
    file_info_label.close()
    os.chdir('..')


class ProcessSegmentation(Algorithm):
    def __init__(self, input_image, produce_output=1, verbose=1, debug=0, remove_temp_files=1, algo_fitting='hanning'):
        super(ProcessSegmentation, self).__init__(input_image=input_image, produce_output=produce_output, verbose=verbose)
        # self._process_name = process_name
        self._debug = debug
        # self._step = step  # step of discretized plane in mm default is min(x_scale,py)
        self._remove_temp_files = remove_temp_files
        # self._volume_output = volume_output
        # self._smoothing_param = smoothing_param  # window size (in mm) for smoothing CSA along z. 0 for no smoothing.
        # self._figure_fit = figure_fit
        # self._fname_csa = fname_csa  # output name for txt CSA
        # self._name_output = name_output  # output name for slice CSA
        # self._name_method = name_method  # for compute_CSA
        # self._slices = slices
        # self._vertebral_levels = vertebral_levels
        # self._path_to_template = path_to_template
        # self._type_window = type_window  # for smooth_centerline @sct_straighten_spinalcord
        # self._window_length = window_length  # for smooth_centerline @sct_straighten_spinalcord
        self._algo_fitting = algo_fitting  # nurbs, hanning

    @property
    def debug(self):
        return self.debug

    @debug.setter
    def debug(self, value):
        self._debug = value

    @property
    def remove_temp_files(self):
        return self._remove_temp_files

    @remove_temp_files.setter
    def remove_temp_files(self, value):
        self._remove_temp_files = value

    @property
    def algo_fitting(self):
        return self._algo_fitting

    @algo_fitting.setter
    def algo_fitting(self, value):
        self._algo_fitting = value


    def execute(self):
        raise NotImplementedError("Please use a concrete implementation of a process : CSAProcess, CenterlineProcess or LengthProcess")


class ExtractCenterlineProcess(ProcessSegmentation):
    def __init__(self, input_image, produce_output=1, verbose=1, debug=0, algo_fitting='hanning', window_length=80, type_window='hanning', remove_temp_files=1):
        super(ExtractCenterlineProcess, self).__init__(input_image, produce_output, verbose, debug, algo_fitting=algo_fitting, remove_temp_files=remove_temp_files)
        self.window_length = window_length
        self.type_window = type_window

    def execute(self):

        output = extract_centerline(self.input_image,self.remove_temp_files, self.verbose, self.algo_fitting, self.type_window, self.window_length)

        sct.printv('\nDone! To view results, type:', self.verbose)
        sct.printv('fslview '+output+' &\n', self.verbose, 'info')



class ComputeLengthProcess(ProcessSegmentation):
    def __init__(self, input_image, produce_output=1, verbose=1, debug=0, algo_fitting='hanning', remove_temp_files=1):
        super(ComputeLengthProcess, self).__init__(input_image, produce_output, verbose, debug, algo_fitting=algo_fitting, remove_temp_files=remove_temp_files)

    def execute(self):
        from math import sqrt

        # Extract path, file and extension
        self.input_image = os.path.abspath(self.input_image)
        path_data, file_data, ext_data = sct.extract_fname(self.input_image)

        # create temporary folder
        path_tmp = 'tmp.'+time.strftime("%y%m%d%H%M%S")
        sct.run('mkdir '+path_tmp)

        # copy files into tmp folder
        sct.run('cp '+self.input_image+' '+path_tmp)

        # go to tmp folder
        os.chdir(path_tmp)

        # Change orientation of the input centerline into RPI
        sct.printv('\nOrient centerline to RPI orientation...', self.verbose)
        fname_segmentation_orient = 'segmentation_rpi' + ext_data
        set_orientation(file_data+ext_data, 'RPI', fname_segmentation_orient)

        # Get dimension
        sct.printv('\nGet dimensions...', self.verbose)
        nx, ny, nz, nt, px, py, pz, pt = sct.get_dimension(fname_segmentation_orient)
        sct.printv('.. matrix size: '+str(nx)+' x '+str(ny)+' x '+str(nz), self.verbose)
        sct.printv('.. voxel size:  '+str(px)+'mm x '+str(py)+'mm x '+str(pz)+'mm', self.verbose)

        # smooth segmentation/centerline
        x_centerline_fit, y_centerline_fit, z_centerline, x_centerline_deriv,y_centerline_deriv,z_centerline_deriv = smooth_centerline(fname_segmentation_orient, type_window='hanning', window_length=80, algo_fitting='hanning', verbose=self.verbose)
        # compute length of centerline
        result_length = 0.0
        for i in range(len(x_centerline_fit)-1):
            result_length += sqrt(((x_centerline_fit[i+1]-x_centerline_fit[i])*px)**2+((y_centerline_fit[i+1]-y_centerline_fit[i])*py)**2+((z_centerline[i+1]-z_centerline[i])*pz)**2)

        sct.printv('\nLength of the segmentation = '+str(round(result_length, 2))+' mm\n', self.verbose, 'info')
        return result_length

class ComputeCSAProcess(ProcessSegmentation):
    def __init__(self, input_image, produce_output=1, verbose=1, debug=0, step=1, remove_temp_files=1, volume_output=1, smoothing_param=50, figure_fit=0,
                 fname_csa='csa.txt', name_output='csa_volume.nii.gz', name_method='counting_z_plane', slices='',
                 vertebral_levels='', path_to_template='', type_window='hanning', window_length=50, algo_fitting='hanning'):
        super(ComputeCSAProcess, self).__init__(input_image, produce_output, verbose, debug, algo_fitting=algo_fitting, remove_temp_files=remove_temp_files)
        self.step = step
        self.smoothing_param = smoothing_param
        self.figure_fit = figure_fit
        self.name_output = name_output
        self.name_method = name_method
        self.slices = slices
        self.vertebral_levels = vertebral_levels
        self.path_to_template = path_to_template
        self.type_window = type_window
        self.fname_csa = fname_csa
        self.window_length = window_length
        self.volume_output = volume_output

    def execute(self):
        # Extract path, file and extension
        fname_segmentation = os.path.abspath(self.input_image)
        path_data, file_data, ext_data = sct.extract_fname(fname_segmentation)

        # create temporary folder
        sct.printv('\nCreate temporary folder...', self.verbose)
        path_tmp = sct.slash_at_the_end('tmp.'+time.strftime("%y%m%d%H%M%S"), 1)
        sct.run('mkdir '+path_tmp, self.verbose)

        # Copying input data to tmp folder and convert to nii
        sct.printv('\nCopying input data to tmp folder and convert to nii...', self.verbose)
        sct.run('isct_c3d '+fname_segmentation+' -o '+path_tmp+'segmentation.nii')

        # go to tmp folder
        os.chdir(path_tmp)

        # try:
        # Change orientation of the input segmentation into RPI
        sct.printv('\nChange orientation of the input segmentation into RPI...', self.verbose)
        fname_segmentation_orient = set_orientation('segmentation.nii', 'RPI', 'segmentation_orient.nii')

        # Get size of data
        sct.printv('\nGet data dimensions...', self.verbose)
        nx, ny, nz, nt, px, py, pz, pt = sct.get_dimension(fname_segmentation_orient)
        sct.printv('  ' + str(nx) + ' x ' + str(ny) + ' x ' + str(nz), self.verbose)

        # Open segmentation volume
        sct.printv('\nOpen segmentation volume...', self.verbose)
        file_seg = nibabel.load(fname_segmentation_orient)
        data_seg = file_seg.get_data()
        hdr_seg = file_seg.get_header()

        # # Extract min and max index in Z direction
        X, Y, Z = (data_seg > 0).nonzero()
        min_z_index, max_z_index = min(Z), max(Z)
        # Xp, Yp = (data_seg[:, :, 0] >= 0).nonzero()  # X and Y range

        # extract centerline and smooth it
        x_centerline_fit, y_centerline_fit, z_centerline, x_centerline_deriv,y_centerline_deriv,z_centerline_deriv = smooth_centerline(fname_segmentation_orient, algo_fitting=self.algo_fitting, type_window=self.type_window, window_length=self.window_length, verbose = self.verbose)
        z_centerline_scaled = [x*pz for x in z_centerline]

        # Compute CSA
        sct.printv('\nCompute CSA...', self.verbose)

        # Empty arrays in which CSA for each z slice will be stored
        csa = np.zeros(max_z_index-min_z_index+1)
        # csa = [0.0 for i in xrange(0, max_z_index-min_z_index+1)]

        for iz in xrange(0, len(z_centerline)):

            # compute the vector normal to the plane
            normal = normalize(np.array([x_centerline_deriv[iz], y_centerline_deriv[iz], z_centerline_deriv[iz]]))

            # compute the angle between the normal vector of the plane and the vector z
            angle = np.arccos(np.dot(normal, [0, 0, 1]))

            # compute the number of voxels, assuming the segmentation is coded for partial volume effect between 0 and 1.
            number_voxels = sum(sum(data_seg[:, :, iz+min_z_index]))

            # compute CSA, by scaling with voxel size (in mm) and adjusting for oblique plane
            csa[iz] = number_voxels * px * py * np.cos(angle)

        if self.smoothing_param:
            from msct_smooth import smoothing_window
            sct.printv('\nSmooth CSA across slices...', self.verbose)
            sct.printv('.. Hanning window: '+str(self.smoothing_param)+' mm', self.verbose)
            csa_smooth = smoothing_window(csa, window_len=self.smoothing_param/pz, window='hanning', verbose=0)
            # display figure
            if self.verbose == 2:
                import matplotlib.pyplot as plt
                plt.figure()
                pltx, = plt.plot(z_centerline_scaled, csa, 'bo')
                pltx_fit, = plt.plot(z_centerline_scaled, csa_smooth, 'r', linewidth=2)
                plt.title("Cross-sectional area (CSA)")
                plt.xlabel('z (mm)')
                plt.ylabel('CSA (mm^2)')
                plt.legend([pltx, pltx_fit], ['Raw', 'Smoothed'])
                plt.show()
            # update variable
            csa = csa_smooth

        # Create output text file
        sct.printv('\nWrite text file...', self.verbose)
        file_results = open('csa.txt', 'w')
        for i in range(min_z_index, max_z_index+1):
            file_results.write(str(int(i)) + ',' + str(csa[i-min_z_index])+'\n')
            # Display results
            sct.printv('z='+str(i-min_z_index)+': '+str(csa[i-min_z_index])+' mm^2', self.verbose, 'bold')
        file_results.close()

        # output volume of csa values
        if self.volume_output:
            sct.printv('\nCreate volume of CSA values...', self.verbose)
            # get orientation of the input data
            orientation = get_orientation('segmentation.nii')
            data_seg = data_seg.astype(np.float32, copy=False)
            # loop across slices
            for iz in range(min_z_index, max_z_index+1):
                # retrieve seg pixels
                x_seg, y_seg = (data_seg[:, :, iz] > 0).nonzero()
                seg = [[x_seg[i],y_seg[i]] for i in range(0, len(x_seg))]
                # loop across pixels in segmentation
                for i in seg:
                    # replace value with csa value
                    data_seg[i[0], i[1], iz] = csa[iz-min_z_index]
            # create header
            hdr_seg.set_data_dtype('float32')  # set imagetype to uint8
            # save volume
            img = nibabel.Nifti1Image(data_seg, None, hdr_seg)
            nibabel.save(img, 'csa_RPI.nii')
            # Change orientation of the output centerline into input orientation
            fname_csa_volume = set_orientation('csa_RPI.nii', orientation, 'csa_RPI_orient.nii')

        # come back to parent folder
        os.chdir('..')

        # Generate output files
        sct.printv('\nGenerate output files...', self.verbose)
        sct.generate_output_file(path_tmp+'csa.txt', path_data+self.fname_csa)  # extension already included in param.fname_csa
        if self.volume_output:
            sct.generate_output_file(fname_csa_volume, path_data+self.name_output)  # extension already included in name_output

        # average csa across vertebral levels or slices if asked (flag -z or -l)
        if self.slices or self.vertebral_levels:

            if self.vertebral_levels and not self.path_to_template:
                sct.printv('\nERROR: Path to template is missing. See usage.\n', 1, 'error')
                sys.exit(2)
            elif self.vertebral_levels and self.path_to_template:
                abs_path_to_template = os.path.abspath(self.path_to_template)

            # go to tmp folder
            os.chdir(path_tmp)

            # create temporary folder
            sct.printv('\nCreate temporary folder to average csa...', self.verbose)
            path_tmp_extract_metric = sct.slash_at_the_end('label_temp', 1)
            sct.run('mkdir '+path_tmp_extract_metric, self.verbose)

            # Copying output CSA volume in the temporary folder
            sct.printv('\nCopy data to tmp folder...', self.verbose)
            sct.run('cp '+fname_segmentation+' '+path_tmp_extract_metric)

            # create file info_label
            path_fname_seg, file_fname_seg, ext_fname_seg = sct.extract_fname(fname_segmentation)
            create_info_label('info_label.txt', path_tmp_extract_metric, file_fname_seg+ext_fname_seg)

            # average CSA
            if self.slices:
                os.system("sct_extract_metric -i "+path_data+self.name_output+" -f "+path_tmp_extract_metric+" -m wa -o ../csa_mean.txt -z "+self.slices)
            if self.vertebral_levels:
                sct.run('cp -R '+abs_path_to_template+' .')
                os.system("sct_extract_metric -i "+path_data+self.name_output+" -f "+path_tmp_extract_metric+" -m wa -o ../csa_mean.txt -v "+self.vert_levels)

            os.chdir('..')

            # Remove temporary files
            print('\nRemove temporary folder used to average CSA...')
            sct.run('rm -rf '+path_tmp_extract_metric)

        # Remove temporary files
        if self.remove_temp_files:
            print('\nRemove temporary files...')
            sct.run('rm -rf '+path_tmp)

        sct.printv('\nDone!', self.verbose)
        if (self.volume_output):
            sct.printv('Output CSA volume: '+self.name_output, self.verbose, 'info')
        if self.slices or self.vertebral_levels:
            sct.printv('Output CSA file (averaged): csa_mean.txt', self.verbose, 'info')
        sct.printv('Output CSA file (all slices): '+self.fname_csa+'\n', self.verbose, 'info')

class ScriptProcessSegmentation(BaseScript):
    def __init__(self):
        super(ScriptProcessSegmentation, self).__init__()

    @staticmethod
    def get_parser():
        # Init parser
        parser = Parser(__file__)

        parser.usage.set_description("This function performs various types of processing from the spinal cord segmentation")
        parser.add_option(name="-i",
                          type_value="image_nifti",
                          description="segmentation image.",
                          mandatory=True,
                          example="t2.nii.gz")
        parser.add_option(name="-p",
                          type_value="multiple_choice",
                          description="type of process to be performed:\n- centerline: extract centerline as binary file\n - length: compute length of the segmentation\n - csa: computes cross-sectional area by counting pixels in each\n  slice and then geometrically adjusting using centerline orientation.\n  Output is a text file with z (1st column) and CSA in mm^2 (2nd column) and\n  a volume in which each slice\'s value is equal to the CSA (mm^2).",
                          mandatory=True,
                          example=['centerline', 'csa', 'length'])
        # optional arguments
        parser.add_option(name="-s",
                          type_value="multiple_choice",
                          description="smooth CSA values with spline.",
                          mandatory=False,
                          example=["0", '1'],
                          default_value=1)
        parser.add_option(name="-b",
                          type_value="multiple_choice",
                          description="outputs a volume in which each slice's value is equal to the CSA in mm^2.",
                          mandatory=False,
                          example=["0", '1'],
                          default_value=0)
        parser.add_option(name="-z",
                          type_value=[[':'], 'int'],
                          description="Slice range to compute the CSA across (requires \"-p csa\").\nExample: 5:23. First slice is 0.", # TODO : Implement an option of the parser in order to parse multiple layer of lists
                          mandatory=False,
                          example="[5:23]")
        parser.add_option(name="-l",
                          type_value=[[':'], 'int'],
                          description="Vertebral levels to compute the CSA across (requires \"-p csa\").",
                          mandatory=False,
                          example="[5:23]")
        parser.add_option(name="-t",
                          type_value="string",
                          description="Path to warped template. Typically: ./label/template.\n Only use with flag -l",
                          mandatory=False,
                          example="./label/template")
        parser.add_option(name="-w",
                          type_value="string",
                          description="Smoothing window size. Only used with \'centerline\'",
                          mandatory=False,
                          example=["0", '1'])
        parser.add_option(name="-o",
                          type_value="file_output",
                          description="name of the output volume if -b 1.",
                          mandatory=False,
                          example="csa_volume.nii.gz",
                          default_value="csa_volume.nii.gz")
        parser.add_option(name="-r",
                          type_value="multiple_choice",
                          description="remove temporary files.",
                          mandatory=False,
                          example=["0", '1'],
                          default_value=1)
        parser.add_option(name="-a",
                          type_value="multiple_choice",
                          description="remove temporary files.",
                          mandatory=False,
                          example=["hanning", 'nurbs'],
                          default_value="hanning")
        parser.add_option(name="-v",
                          type_value="int",
                          description="verbose",
                          mandatory=False,
                          example="0",
                          default_value="1")

        return parser

    def main(self):
        parser = self.get_parser()

        arguments = parser.parse(sys.argv[1:])

        # assigning variables to arguments
        input_filename = arguments["-i"]
        process = arguments["-p"]

        if process == 'centerline':
            sc_process = ExtractCenterlineProcess(input_image=input_filename)
        elif process == 'length':
            sc_process = ComputeLengthProcess(input_image=input_filename)
        elif process == 'csa':
            sc_process = ComputeCSAProcess(input_image=input_filename)
        else:
            raise Exception("Chosen process -p is not valid. WE SHOULD NOT BE HERE ABANDON SHIP. No seriously something is wrong in the parser")

        if "-m" in arguments:
            sc_process.name_method = arguments["-m"]
        if "-b" in arguments:
            sc_process.volume_output = int(arguments["-b"])
        if "-l" in arguments:
            sc_process.vertebral_levels = arguments["-l"]
        if "-r" in arguments:
            sc_process.remove_temp_files = int(arguments["-r"])
        if "-s" in arguments:
            sc_process.smoothing_param = int(arguments["-s"])
        if "-f" in arguments:
            sc_process.figure_fit = int(arguments["-f"])
        if "-o" in arguments:
            sc_process.name_output = arguments["-o"]
        if "-t" in arguments:
            sc_process.name_output = arguments["-t"]
        if "-z" in arguments:
            sc_process.name_output = arguments["-z"]
        if "-v" in arguments:
            sc_process.verbose = int(arguments["-v"])
        if "-a" in arguments:
            sc_process.verbose = str(arguments["-a"])

        sc_process.execute()

if __name__ == "__main__":
    script = ScriptProcessSegmentation()
    script.main()




