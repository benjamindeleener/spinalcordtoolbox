#Atlas creation

In this branch the atlas was created using a new template. This version of the template is longer than the previous one
and was generated for the conference ISMRM. A T1 and a T2 template were generated using 35 subjects.
We replaced the old template in $SCT_DIR/data/template by the new version and created a new version of the atlas
-containing both WM and GM tracts- from this template.

##GM_atlas

The  original GM atlas image was chosen from the book ``The human central nervous system``, chapter ``Topography of Spinal Cord, Brain Stem and Cerebellum``, figure 6.1. (screenshot: **original_atlas.png** in raw_data).
It was numerized by hand into a greyscale image (**greyscale_GM_atlas.png**) and binary masks (**white_GM_mask.png and white_WM_mask.png**).
The GM tracks selected for the GM atlas are: dorsal horn, ventral horn and the intermediate zone. With separation between left and right side of the GM, this gives us an atlas of 6 tracts.
-Values attributed to each tract (**greyscale_GM_atlas.png**):
  -220: right dorsal horn
  -190: right intermediate zone
  -150: right ventral horn
  -120: left dorsal horn
  -80: left intermediate zone
  -45: left ventral horn



##Generation of the atlas

For the generation of the GM atlas we first register the mask of the image of the GM atlas (**white_WM_mask.png**) obtain
from documentation to the WM atlas mask (**mask_grays_cerv_sym_correc_r5.png**) obtain from documentation. Then we
concatenate the greyscale images of the WM tracts (atlas_grays_cerv_sym_correc_r5.png) and of the GM tracts
(**greyscale_reg_no_trans_sym.png**) into one. This is done using the script **registration_GM_atlas.py**.

Then, we complete the automatic process by small handmaid corrections filling the blank pixels with closest non
zero values (**concatenation.png** to **concatenation_corrected.png**) (use Seashore or any other relevant software).

Finally we uses a similar script to create_atlas.m (**create_atlas_WM_and_GM2.m**) to generate the GM and WM atlas altogether.
This is done by first registrating the mask image of the concatenation (**mask_grays_cerv_sym_correc_r5.png**) to the
corresponding slice of the probabilist template of the WM (**MNI-Poly-AMU_WM.nii.gz**) and then by propagating the
registration along the spinalcord.



###To generate the atlas

- To generate the atlas png image of WM and GM
  - Open: **registration_GM_atlas.py**
    - edit variable ``path_output`` which will gather all the results from the script
  - Run: **registration_GM_atlas.py**
    - It is a Python script to be used to register the GM atlas to the WM atlas. It uses antsRegistration with algo syn as
    we want the outlines to match perfectly.
  - Complete the blank pixel of **concatenation.png** with closest non-zero value (e.g.: use seashore) and save it as
      **concatenation_corrected.png**.
  The file **concatenation_corrected.png** is the image that we will be using to generate the atlas for all the spinal cord.

- To expand the atlas along the spinal cord
  - Open with matlab: **create_atlas_WM_and_GM2.m**:
    - edit variable ``path_atlas_data`` with what was chosen for ``path_output`` (for file **registration_GM_atlas.py**)
    - edit variable ``path_out`` which will gather all the results from the script
  - Run **create_atlas_WM_and_GM2.m**.

N.B.: The tracts of this atlas does not perfectly sum to 1 even in the middle of the spine. In order to correct
this, an idea is to divide each tract by the sum of each tract.

- To divide each tract by the sum of each tract
  - Open **divide_by_sum.m**:
    - edit variable ``path_out`` with what was chosen for ``path_out`` in **create_atlas_WM_and_GM2.m** adding
    ``final_results`` at the end of the string (e.g.: enter ``'User/tamag/test/final_results'`` if you entered
    ``'User/tamag/test/'`` in **create_atlas_WM_and_GM2.m**)
  - Run **divide_by_sum.m**.
    - it will return a file for each tract with the suffix ``_div``.





##DATA

All data (inputs, outputs and script files) are located in (NeuroPoly lab):
~~~
/Volumes/Usagers/Etudiants/tamag/data/data_atlas_for_new_template
~~~