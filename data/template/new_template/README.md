This is a new version of the template (35 subjects). It is longer than the previous one (for anatomic images: a little above brainstem to frontier T12-L1).
However the AMU template of WM only goes from C1 to T11-T12. Thus the atlas of white and gray matter can only go from C1 to T11-T12.

The files contained in this folder are the originals and need some corrections in order to be used.
Those files are centered at x=50 when it should be x=49.
Apply warp_trans_0.5mm.nii.gz to all files to change x_center to 49 
(e.g.: sct_apply_transfo -i MNI-Poly-AMU_T2.nii.gz -d MNI-Poly-AMU_T2.nii.gz -w warp_trans_0.5mm.nii.gz -o MNI-Poly-AMU_T2_center49.nii.gz)


