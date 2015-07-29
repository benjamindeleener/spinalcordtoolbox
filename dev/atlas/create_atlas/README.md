###



GM_atlas
=============

The GM atlas original image was chosen from the book The human central nervous system, chapter Topography of Spinal Cord, Brain Stem and Cerebellum, figure 6.1. (screenshot: original_atlas.png). It was numerized by hand into a greyscale image (greyscale_GM_atlas.png) and binary masks (white_GM_mask.png and white_WM_mask.png). 
The GM areas selected for the GM atlas are: dorsal horn, ventral horn and the intermediate zone. With separation between left and right side of the GM, this gives us an atlas of 6 tracts.
Value attributed to each tract (greyscale_GM_atlas.png):
	-220: right dorsal horn
	-190: right intermediate zone
	-150: right ventral horn
	-120: left dorsal horn
	-80: left intermediate zone
	-45: left ventral horn


For the generation of the GM atlas we first register the mask of the image of the GM atlas (white_WM_mask.png) obtain from documentation to the WM atlas mask (mask_grays_cerv_sym_correc_r5.png) obtain from documentation. This is done with the script registration_GM_atlas.py. Then we concatenate the greyscale images of the WM tracts (atlas_grays_cerv_sym_correc_r5.png) and of the GM tracts (greyscale_final_for_atlas.png) into one (script: concatenate_WM_and_GM.py), completting the automatic process by small handmaid correction (concatenation.png and concatenation_corrected.png). Finally we uses a similar script to create_atlas.m (create_atlas_WM_and_GM.m) to generate the GM and WM atlas altogether (output_folder: WM_and_GM_tracts_output). This is done by first registrating the mask image of the concatenation (mask_grays_cerv_sym_correc_r5.png) to the corresponding slice of the probabilist template of the WM (MNI-Poly-AMU_WM) and then by propagating the registration along the spinalcord.

    registration_GM_atlas.py
    =======
        Python script to be used to register the GM atlas to the WM atlas. It uses antsRegistration with algo syn as we want the outlines to match perfectly.
        
    


    concatenate_WM_and_GM.py
    =======
        Python script to concatenate WM and GM tracts after registration.
        




    create_atlas_WM_and_GM.m
    ========
        Matlab script to generate an atlas compose of WM and GM tracts. (Same process as for the WM atlas.)      