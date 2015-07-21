#!/usr/bin/env python


import commands, sys, os

# Get path of the toolbox
status, path_sct = commands.getstatusoutput('echo $SCT_DIR')
# Append path that contains scripts, to be able to load modules
sys.path.append(path_sct + '/scripts')
sys.path.append(path_sct + '/dev/tamag')

from msct_register_regularized import generate_warping_field
from nibabel import load
import sct_utils as sct



path = '/Users/tamag/code/spinalcordtoolbox/data/template'
file_template = 'MNI-Poly-AMU_T2.nii.gz'
name_warp = 'warp_trans_0.5mm.nii.gz'
name_output = 'template_trans.nii.gz'


list_dir = os.listdir(path+'/center_x50')
os.chdir(path)

# # Get dimension of file_template
# nx, ny, nz, nt, px, py, pz, pt = sct.get_dimension(file_template)
#
# # Define x_trans and y_trans
# x_trans = [-0.5 for i in range(nz)]
# y_trans = [0 for i in range(nz)]
#
# generate_warping_field(file_template, x_trans, y_trans, fname=name_warp)


for i in range(len(list_dir)):
    if os.path.isfile('center_x50/' + list_dir[i]):
        sct.run('sct_apply_transfo -i center_x50/' + list_dir[i] + ' -d center_x50/' + list_dir[i] + ' -w center_x50/' + name_warp + ' -o ' + list_dir[i])