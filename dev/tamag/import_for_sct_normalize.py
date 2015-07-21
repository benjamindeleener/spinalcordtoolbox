#!/usr/bin/env python


import commands, sys, os

# Get path of the toolbox
status, path_sct = commands.getstatusoutput('echo $SCT_DIR')
# Append path that contains scripts, to be able to load modules
sys.path.append(path_sct + '/scripts')
sys.path.append(path_sct + '/dev/tamag')

from numpy import mean, append, isnan, array
import sct_utils as sct
from scipy import ndimage



path = '/Users/tamag/data/data_template/test_new_pipeline/subjects'
path_out = '/Users/tamag/Desktop/test_normalize_intensity/T1'

list_dir = os.listdir(path)
# os.chdir(path)
#
# for i in range(1,len(list_dir)): #subjects
#     if os.path.isdir(list_dir[i]):
#         list_dir_2 = os.listdir(path + '/' + list_dir[i])
#         for j in range(len(list_dir_2)): # T1 or T2
#             if list_dir_2[j] == 'T1':
#                 list_dir_3 = os.listdir(path + '/' + list_dir[i] + '/' + list_dir_2[j])  # files in subject/contrast
#                 os.chdir(list_dir[i]+ '/' + list_dir_2[j])
#                 for k in range(len(list_dir_3)):
#                     if list_dir_3[k] == 'data_RPI_crop.nii.gz':
#                         # Copy file to path_out and rename
#                         sct.run('cp ' + list_dir_3[k]+ ' ' + path_out + '/' + list_dir[i] +'.nii.gz')
#         os.chdir('../..')
# os.chdir('../')
# os.chdir(path)
#
# for i in range(1,len(list_dir)): #subjects
#     if os.path.isdir(list_dir[i]):
#         list_dir_2 = os.listdir(path + '/' + list_dir[i])
#         for j in range(len(list_dir_2)): # T1 or T2
#             if list_dir_2[j] == 'T1':
#                 list_dir_3 = os.listdir(path + '/' + list_dir[i] + '/' + list_dir_2[j])  # files in subject/contrast
#                 os.chdir(list_dir[i]+ '/' + list_dir_2[j])
#                 for k in range(len(list_dir_3)):
#                     if list_dir_3[k] == 'generated_centerline.nii.gz':
#                         # Copy file to path_out and rename
#                         sct.run('cp ' + list_dir_3[k]+ ' ' + path_out + '/' + list_dir[i] +'_centerline.nii.gz')
#         os.chdir('../..')
#
#
# os.chdir(path)


os.chdir(path_out)

for i in range(1,len(list_dir)): #subjects
    sct.run('sct_normalize.py -i ' + list_dir[i] +'.nii.gz -c ' + list_dir[i] +'_centerline.nii.gz -v 1')