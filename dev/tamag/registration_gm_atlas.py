#!/usr/bin/env python

import os, sys, commands

# Get path of the toolbox
status, path_sct = commands.getstatusoutput('echo $SCT_DIR')
# Append path that contains scripts, to be able to load modules
sys.path.append(path_sct + '/scripts')


import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from PIL import Image
import nibabel
import sct_utils as sct
import matplotlib.pyplot as plt

ext_o = '.nii.gz'


def main():

    os.chdir('/Users/tamag/Desktop/GM_atlas/def_new_atlas/test_2')

    # Define names
    fname1 = 'greyscale_antisym.png'
    fname2 = 'binary_gm_black.png'
    fname3 = 'gm_white.png'
    fname4 = 'mask_grays_cerv_sym_correc_r5.png'
    slice = 'slice_ref_template.nii.gz'
    name1 = 'greyscale_antisym'
    name2 = 'binary_gm_black'
    name3 = 'gm_white'
    name4 = 'mask_grays_cerv_sym_correc_r5'


    save_nii_from_png(fname1)
    save_nii_from_png(fname2)
    save_nii_from_png(fname3)
    save_nii_from_png(fname4)

    # Crop image background

    #sct.run('sct_crop_image -i '+ name2 + ext_o +' -dim 0,1 -start 84,0 -end 1581,1029 -b 0 -o binary_gm_crop.nii.gz')
    #name2 = 'binary_gm_crop'

    # Interpolation of the images to set them in the right format
    interpolate(name1+ext_o)
    interpolate(name2+ext_o)
    interpolate(name3+ext_o)

    # Copy some info from hdr of the slice template
    copy_hdr(name1+'_resampled'+ext_o, slice)
    copy_hdr(name2+'_resampled'+ext_o, slice)
    copy_hdr(name3+'_resampled'+ext_o, slice)
    copy_hdr(name4+ext_o, slice)

    # transformation affine pour premier recalage
    warp_1_prefix = 'warp_1_'
    tmp_file = 'tmp.nii.gz'
    cmd = ('isct_antsRegistration --dimensionality 2 -m MeanSquares[mask_grays_cerv_sym_correc_r5.nii.gz, '+name2+'_resampled'+ext_o+', 3, 4] -t Affine[50] --convergence 100x10 -s 1x0 -f 4x1 -o '+ warp_1_prefix +' -r [mask_grays_cerv_sym_correc_r5.nii.gz, '+name2+'_resampled'+ext_o+', 0]')
    sct.run(cmd)
    cmd_0 = ('isct_antsApplyTransforms -d 2 -i '+name2+'_resampled'+ext_o+' -t '+warp_1_prefix+'0GenericAffine.mat -r mask_grays_cerv_sym_correc_r5.nii.gz  -o '+ tmp_file)
    sct.run(cmd_0)

    # transformation Syn pour faire correspondre les formes
    warp_2_prefix = 'warp_2_'
    tmp_file_2 = 'tmp_2.nii.gz'
    # cmd_1 = ('isct_antsRegistration --dimensionality 2 -m MeanSquares[mask_grays_cerv_sym_correc_r5.nii.gz, '+ tmp_file+', 1, 4] -t BSplineSyN[0.2,3] --convergence 100x10 -s 1x0 -f 4x1 -o '+warp_2_prefix+' -r [mask_grays_cerv_sym_correc_r5.nii.gz, ' + tmp_file + ', 0]')
    cmd_1 = ('isct_antsRegistration --dimensionality 2 -m MeanSquares[mask_grays_cerv_sym_correc_r5.nii.gz, '+ tmp_file+', 1, 32] -t SyN[0.1,3,0] --convergence 1000x1000 -s 1x0 -f 2x1 -o '+warp_2_prefix+' -r [mask_grays_cerv_sym_correc_r5.nii.gz, ' + tmp_file + ', 0]')
    sct.run(cmd_1)
    cmd_2 = ('isct_antsApplyTransforms -d 2 -i '+tmp_file+' -t '+ warp_2_prefix + '1Warp.nii.gz -r mask_grays_cerv_sym_correc_r5.nii.gz  -o '+tmp_file_2)
    sct.run(cmd_2)


    # concatenation et application des warping fields aux images de base
    # cmd = ('isct_ComposeMultiTransform 2 outwarp.nii.gz  test_registration0GenericAffine.mat test_registration_Bspline1Warp.nii.gz -R mask_grays_cerv_sym_correc_r5.nii.gz')
    # cmd = ('isct_antsApplyTransforms -d 2 -i greyscale_select_inv_resampled.nii.gz -o greyscale_registered.nii.gz -n Linear -t outwarp.nii.gz -r mask_grays_cerv_sym_correc_r5.nii.gz')
    concat_and_apply(inputs=[name1+'_resampled'+ext_o, name2+'_resampled'+ext_o, name3+'_resampled'+ext_o], dest=name4+ext_o, output_names=[name1+'_resampled'+'_registered'+ext_o, name2+'_resampled'+'_registered'+ext_o, name3+'_resampled'+'_registered'+ext_o], warps=[warp_1_prefix+'0GenericAffine.mat', warp_2_prefix + '1Warp.nii.gz'])

    # Save png images of the registered NIFTI images
    save_png_from_nii(name1+'_resampled'+'_registered'+ext_o)
    save_png_from_nii(name2+'_resampled'+'_registered'+ext_o)
    save_png_from_nii(name3+'_resampled'+'_registered'+ext_o)

    # Crop png images to erase blank borders
    crop_blank_edges(name1+'_resampled'+'_registered')
    crop_blank_edges(name2+'_resampled'+'_registered')
    crop_blank_edges(name3+'_resampled'+'_registered')

    # resize images to the same size as the WM atlas images
    resize_gm_png_to_wm_png_name(name1+'_resampled'+'_registered'+'_crop', name4)
    resize_gm_png_to_wm_png_name(name2+'_resampled'+'_registered'+'_crop', name4)
    resize_gm_png_to_wm_png_name(name3+'_resampled'+'_registered'+'_crop', name4)

    # tester correspondances entre les images
    status, output = sct.run('sct_dice_coefficient ' + name2 + '_resampled' + '_registered' + ext_o + ' ' + name4 + ext_o)
    print output

def concat_and_apply(inputs, dest, output_names, warps):
    # input = [input1, input2]
    # warps = [warp_1, warp_2]
    warp_str = ''
    for i in range(len(warps)):
        warp_str = ' '.join((warp_str, warps[-1-i]))
    cmd_0 = ('isct_ComposeMultiTransform 2 outwarp.nii.gz  ' + warp_str + ' -R ' + dest)
    sct.run(cmd_0)
    for j in range(len(inputs)):
        cmd_1 = ('isct_antsApplyTransforms -d 2 -i ' + inputs[j] + ' -o '+ output_names[j] + ' -n Linear -t outwarp.nii.gz -r '+ dest)
        sct.run(cmd_1)

def save_nii_from_png(fname):
    path, file, ext = sct.extract_fname(fname)
    image = Image.open(fname).convert("L")
    arr = np.asarray(image)
    img = nibabel.Nifti1Image(arr, None)
    nibabel.save(img, file + ext_o)

#define header of output
def copy_hdr(input, dest):
    # Copy part of the header of dest into the header of intput
    cmd = ('fslcpgeom ' + dest +' '+ input + ' -d')
    sct.run(cmd)
    #change size of pixel by hand with set_q_form and set set_s_form

# creer fichier nifti de meme taille: interpoler pour mettre les 2 images a la bonne taille
def interpolate(fname, interpolation = 'Linear'):
    path, file, ext = sct.extract_fname(fname)
    cmd =('isct_c3d '+fname+' -interpolation '+interpolation + ' -resample 492x363x1 -o '+ file + '_resampled' + ext)
    sct.run(cmd)

def save_png_from_nii(fname):
    path, file, ext = sct.extract_fname(fname)
    data = nibabel.load(fname).get_data()
    sagittal = data[ :, :].T
    fig, ax = plt.subplots(1,1)
    ax.imshow(sagittal, cmap='gray', origin='lower')
    ax.set_title('sagittal')
    ax.set_axis_off()
    fig1 = plt.gcf()
    fig1.savefig(file + '.png', format='png')

# Crop blank edges coming from save_png_from_nii
# minus 102 along x and minus 75 along y (on each side)
def crop_blank_edges(name_png):
    img = Image.open(name_png+'.png')
    data = np.asarray(img)
    data_out = data[75:525, 102:715]
    im_out = Image.fromarray(data_out)
    im_out.save(name_png+'_crop'+'.png')

def resize_gm_png_to_wm_png_name(name_png, name_dest_png):
    img = Image.open(name_png+'.png')
    img_dest = Image.open(name_dest_png+'.png')
    img_resized = img.resize((img_dest.size[1],img_dest.size[0]))
    img_resized.save(name_png+'_resized.png')


#=======================================================================================================================
# Start program
#=======================================================================================================================
if __name__ == "__main__":
    # call main function
    main()
