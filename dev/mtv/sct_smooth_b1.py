#!/usr/bin/env python
__author__ = 'slevy'
# Simon LEVY, Julien Cohen-Adad
# Created: 2014-10-30

import getopt
import sys
import commands
import time
import os
# Get path of the toolbox
status, path_sct = commands.getstatusoutput('echo $SCT_DIR')
# Append path that contains scripts, to be able to load modules
sys.path.append(path_sct + '/scripts')
import sct_utils as sct
from msct_parser import *

class Param:
    def __init__(self):
        self.debug = 0
        self.file_fname_output = 'b1_smoothed'

#=======================================================================================================================
# main
#=======================================================================================================================
def main():
    # Parameters for debug mode
    if param.debug:
        sct.printv('\n*** WARNING: DEBUG MODE ON ***\n', type='warning')
        fname_spgr10 = 'spgr10.nii.gz'
        epi_fnames = 'b1/ep60.nii.gz,b1/ep120.nii.gz'
        file_fname_output = 'b1_smoothed'

    # Check input parameters
    parser = Parser(__file__)
    parser.usage.set_description('compute Ialpha/I2*alpha')
    parser.add_option("-d", "file", "image you want to crop", True, "t2.nii.gz")
    parser.add_option("-i", "str", "Two NIFTI : flip angle alpha and 2*alpha", True, "ep_fa60.nii.gz,ep_fa120.nii.gz")
    parser.add_option("-o", "str", "output file name", False, "t2_segin_cropped_over_mask.nii.gz")
    usage = parser.usage.generate()

    arguments = parser.parse(sys.argv[1:])

    # Initialization of variables
    fname_spgr10 = arguments["-d"]
    epi_fnames   = arguments["-i"]
    file_fname_output = arguments["-o"]

    # Parse inputs to get the actual data
    epi_fname_list = epi_fnames.split(',')

    # Extract path, file names and extensions
    path_epi, fname_epi, ext_epi = sct.extract_fname(epi_fname_list[0])

    # Create temporary folders and go in it
    sct.printv('Create temporary folder...')
    path_tmp = 'tmp_'+time.strftime("%y%m%d%H%M%S")
    sct.create_folder(path_tmp)
    os.chdir(path_tmp)

    # Compute the half ratio of the 2 epi (Saturated Double-Angle Method for Rapid B1 Mapping - Cunningham)
    fname_half_ratio = '../'+path_epi+'epi_half_ratio.nii.gz'
    sct.run('fslmaths -dt double ../'+epi_fname_list[0]+' -div 2 -div ../'+epi_fname_list[1]+' '+fname_half_ratio)

    # Smooth this half ratio slice-by-slice
    nx, ny, nz, nt, px, py, pz, pt = sct.get_dimension('../'+epi_fname_list[0])
    # split slices
    sct.run('fslsplit '+fname_half_ratio+' -z')
    # 2D median filtering of each slice
    vol_list=''
    for slice in range(0, nz):
        sct.run('fslmaths vol'+str(slice).zfill(4)+' -kernel boxv 7x7x1 -fmedian vol'+str(slice).zfill(4)+'_median_smoothed')
        vol_list += 'vol'+str(slice).zfill(4)+'_median_smoothed '

    # merge volumes
    fname_half_ratio_smoothed = path_epi+file_fname_output+ext_epi
    sct.run('fslmerge -z ../'+fname_half_ratio_smoothed+' '+vol_list)

    # Remove temporary folder
    os.chdir('..')
    sct.run('rm -rf '+path_tmp)

    # Check if the dimensions of the b1 profile are the same as the SPGR data
    sct.printv('\nCheck consistency between dimensions of B1 profile and dimensions of SPGR images...')
    b1_nx, b1_ny, b1_nz, b1_nt, b1_px, b1_py, b1_pz, b1_pt = sct.get_dimension(fname_half_ratio_smoothed)
    spgr_nx, spgr_ny, spgr_nz, spgr_nt, spgr_px, spgr_py, spgr_pz, spgr_pt = sct.get_dimension(fname_spgr10)
    if (b1_nx, b1_ny, b1_nz) != (spgr_nx, spgr_ny, spgr_nz):
        sct.printv('\tDimensions of the B1 profile are different from dimensions of SPGR data. \n\t--> register it into the SPGR data space...')
        path_fname_ratio, file_fname_ratio, ext_fname_ratio = sct.extract_fname(fname_half_ratio_smoothed)
        path_spgr10, file_spgr10, ext_spgr10 = sct.extract_fname(fname_spgr10)

        #fname_output = path_fname_ratio + file_fname_ratio + '_resampled_' + str(spgr_nx) + 'x' + str(spgr_ny) + 'x' + str(spgr_nz) + 'vox' + ext_fname_ratio
        #sct.run('c3d ' + fname_ratio + ' -interpolation Cubic -resample ' + str(spgr_nx) + 'x' + str(spgr_ny) + 'x' + str(spgr_nz) + 'vox -o '+fname_output)

        fname_output = path_fname_ratio + file_fname_ratio + '_in_'+file_spgr10+'_space' + ext_fname_ratio
        sct.run('sct_register_multimodal -i ' + fname_half_ratio_smoothed + ' -d ' + fname_spgr10+' -o '+fname_output+' -p 0,SyN,0.5,MeanSquares')
        # Delete useless outputs
        sct.delete_nifti(path_fname_ratio+'/warp_dest2src.nii.gz')
        sct.delete_nifti(path_fname_ratio+'/warp_src2dest.nii.gz')
        sct.delete_nifti(path_fname_ratio+'/'+file_spgr10+'_reg.nii.gz')

        #fname_b1_smoothed = fname_output
        sct.printv('\t\tDone.--> '+fname_output)

    sct.printv('\tDone.')


#=======================================================================================================================
# Start program
#=======================================================================================================================
if __name__ == "__main__":
    # Construct object fro class 'param'
    param = Param()
    # Call main function
    main()

