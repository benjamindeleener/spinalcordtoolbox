#! /usr/bin/env perl

#----------------------------- MNI Header -----------------------------------
#@NAME       : spine_minipipe.pl
#@DESCRIPTION: spine segmentation mini-pipeline
#@COPYRIGHT  :
#              Copyright 2014 Vladimir S. FONOV, 
#              McConnell Brain Imaging Centre, 
#              Montreal Neurological Institute, McGill University.
#              Permission to use, copy, modify, and distribute this
#              software and its documentation for any purpose and without
#              fee is hereby granted, provided that the above copyright
#              notice appear in all copies.  The author and McGill University
#              make no representations about the suitability of this
#              software for any purpose.  It is provided "as is" without
#              express or implied warranty.
#---------------------------------------------------------------------------- 

use strict;
use File::Basename;
use File::Temp qw/ tempfile tempdir /;
use Getopt::Long;

my $fake=0;
my $verbose=1;
my $clobber=0;
my $me=basename($0);
my $mydir=dirname($0);
my $model_dir;
my $nuc;
my $cleanup;
my $subject;
my $qc=1;
my $manual_xfm;
my $threshold=0.0;
my $variant='labels';
my $compare;
my $tags;
my $stage1=0;
my $threads=1;
my $t1;
my $fl;
my $fix_flip=0;
my $manual;
my $norm_iter=1;
my $validate;
my $convert_nii=0;

GetOptions (
          'verbose'        => \$verbose,
          'qc'             => \$qc,
          'clobber'        => \$clobber,
          'model-dir=s'    => \$model_dir,
          'subject=s'      => \$subject,
          'tags=s'         => \$tags,
          'stage1'         => \$stage1,
          't1=s'           => \$t1,
          'fl=s'           => \$fl,
          'fix-flip'       => \$fix_flip,
          'manual=s'       => \$manual,
          'validate=s'       => \$validate,
          );

my $HELP=<<HELP ;
Usage $me input_t2.mnc input_init.mnc output_prefix  
          --model-dir <anatomical model directory> - required!
         [
          --qc - produce qc images
          --subject <name>
          --stage1 - run only N3 & straightening
          --t1 <file> additional T1 modality
          --fl <file> additional FLAIR modality
          --validate <seg> provide ground truth segmentation for validation
         ]
HELP


die $HELP if $#ARGV<2 || !$model_dir;

my $model       ="$model_dir/model_t2.mnc";
my $model_mask  ="$model_dir/model_mask.mnc";
my $model_cls   ="$model_dir/model_seg.mnc";
my $model_bnd   ="$model_dir/model_bnd.mnc";
my $model_levels="$model_dir/model_seg2.mnc";
my $model_cord  ="$model_dir/model_cord_c.tag";
my $model2_mask ="$model_dir/model_mask.mnc";
my $model_CSF   ="$model_dir/model_CSF.mnc";
my $model_GM    ="$model_dir/model_GM.mnc";
my $model_WM    ="$model_dir/model_WM.mnc";
my $model_WM_tr ="$model_dir/model_WM";

check_presence($model,$model_mask,$model_cls,$model_bnd,$model_levels,$model_cord);
#,$model_CSF,$model_WM,$model_GM);

my ($in,$init,$prefix)=@ARGV;
my $tmpdir = &tempdir( "$me-XXXXXXXX", TMPDIR => 1, CLEANUP => 1 );
do_cmd('mkdir','-p',$prefix);

unless($subject) #figure out subject id
{
  $subject=basename($in,'.gz');
  $subject =~ s/\.gz$//;
  $subject =~ s/\.mnc$//;
}

$t1='' unless -e $t1;
$fl='' unless -e $fl;

my $compress=$ENV{MINC_COMPRESS};
#$ENV{ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS}=1;

#normalization
if(! -e "${prefix}/norm_${subject}_t2.mnc")
{
  do_cmd("itk_resample",$in,'--normalize',"${prefix}/norm_${subject}_t2.mnc",'--short');
}

# noise estimate
#my $noise=`noise_estimate $in`;
#chomp($noise);

# denoise using patches
if(! -e "${prefix}/den_${subject}_t2.mnc")
{
  do_cmd('minc_anlm','--mt',$threads,"${prefix}/norm_${subject}_t2.mnc","${prefix}/den_${subject}_t2.mnc");
}

if( $t1 && ! -e "${prefix}/den_${subject}_t1.mnc")
{
  do_cmd('minc_anlm','--mt',$threads,$t1,"${prefix}/den_${subject}_t1.mnc");
}

if( $fl && ! -e "${prefix}/den_${subject}_fl.mnc")
{
  do_cmd('minc_anlm','--mt',$threads,$fl,"${prefix}/den_${subject}_fl.mnc");
}

# intensity normalization: N3 + interslice norm + volume_pol
if(! -e "${prefix}/clp0_${subject}_t2.mnc")
{
  # add padding to make N3/N4 happy
  my $width=`mincinfo -dimlength xspace ${prefix}/norm_${subject}_t2.mnc`;
  my $padding=50;
  my $new_width=$width+$padding*2;
  do_cmd('mincreshape','-dimrange',"xspace=-${padding},${new_width}","${prefix}/den_${subject}_t2.mnc","${tmpdir}/padded_${subject}_t2.mnc",'-q');
  do_cmd('c3d','-verbose','-n4_spline_distance',"100,100,100",'-n4_shrink_factor',2,'-n4_convergence_threshold', 0.001,'-n4_max_iterations',100,"${tmpdir}/padded_${subject}_t2.mnc",'-n4',"${tmpdir}/n3_${subject}_t2.mnc");
  # remove padding
  do_cmd('mincreshape','-dimrange',"xspace=${padding},${width}","${tmpdir}/n3_${subject}_t2.mnc","${tmpdir}/n3_${subject}_t2_unpad.mnc",'-q');
  # perform vertical interslice intensity normalization

  do_cmd('volume_pol', '--order', 1, "$tmpdir/n3_${subject}_t2_unpad.mnc",$model,'--expfile', "$tmpdir/stats",'--noclamp');
  do_cmd('minccalc',"$tmpdir/n3_${subject}_t2_unpad.mnc","${prefix}/clp0_${subject}_t2.mnc", '-expfile', "$tmpdir/stats", '-clobber','-short','-q');
}

if( $t1 && ! -e "${prefix}/n3_${subject}_t1.mnc")
{
  do_cmd("nu_correct","${prefix}/den_${subject}_t1.mnc", "-iter", 100, "-stop", 0.0001, "-fwhm", 0.1,'-distance',50,"$tmpdir/n3_${subject}_t1.mnc");
  
}

if( $t1 && ! -e "${prefix}/${subject}_t1_elx/TransformParameters.0.txt")
{
  do_cmd('mkdir','-p',"${prefix}/${subject}_t1_elx");
  do_cmd("itk_resample","${prefix}/n3_${subject}_t1.mnc",
         '--normalize',"${prefix}/${subject}_t1_elx/n3_${subject}_t1.mnc",'--short')
    unless -e "${prefix}/${subject}_t1_elx/n3_${subject}_t1.mnc";

  system('elastix',
          '-f',"${prefix}/clp_${subject}_t2.mnc",
          '-m',"${prefix}/${subject}_t1_elx/n3_${subject}_t1.mnc",
          '-out',"${prefix}/${subject}_t1_elx",
          '-p','parameters_Affine.txt');
  system('cp',"${prefix}/${subject}_t1_elx/result.0.mnc","${prefix}/res_${subject}_t1.mnc");
}


if( $fl && ! -e "${prefix}/n3_${subject}_fl.mnc")
{
  do_cmd("nu_correct","${prefix}/den_${subject}_fl.mnc", 
                      "-iter", 100, "-stop", 0.0001, 
                      "-fwhm", 0.1,
                      '-distance',50,"$tmpdir/n3_${subject}_fl.mnc");
}

if( $fl && ! -e "${prefix}/${subject}_fl_elx/TransformParameters.0.txt")
{
  do_cmd('mkdir','-p',"${prefix}/${subject}_fl_elx");
  
  do_cmd("itk_resample","${prefix}/n3_${subject}_fl.mnc",'--normalize',"${prefix}/${subject}_fl_elx/n3_${subject}_fl.mnc",'--short')
    unless -e "${prefix}/${subject}_fl_elx/n3_${subject}_fl.mnc";

  do_cmd('elastix',
          '-f',"${prefix}/clp_${subject}_t2.mnc",
          '-m',"${prefix}/${subject}_fl_elx/n3_${subject}_fl.mnc",
          '-out',"${prefix}/${subject}_fl_elx",
          '-p','parameters_Affine.txt');
  do_cmd('cp',"${prefix}/${subject}_fl_elx/result.0.mnc","${prefix}/res_${subject}_fl.mnc");
}


# straightening the spine,  make it vertical and place center at the origin
if(! -e "${prefix}/str_${subject}.xfm" )
{
  do_cmd('itk_spine_straighten', 
         "${prefix}/clp0_${subject}_t2.mnc" ,$init ,
         '--smooth', 10,
         '--vertical',
         '--smoothness',0.1,
         '--extend',100,
         "${tmpdir}/clp2_${subject}_t2.mnc",
         '--tag',"${prefix}/str_${subject}.tag",
         '--transform',"${prefix}/str_${subject}.xfm",
         '--inv-transform',"${prefix}/str_${subject}_inv.xfm",
         '--ref',$model_mask,
         '--output-seg',"${prefix}/gc_${subject}_t2.mnc",'--verbose',
         '--z-scale'
         );
  do_cmd('mincresample','-nearest',"${tmpdir}/clp2_${subject}_t2.mnc",'-like',"${prefix}/gc_${subject}_t2.mnc","${tmpdir}/clp3_${subject}_t2.mnc");
  
  my $intensity=`mincstats -q -mean ${tmpdir}/clp3_${subject}_t2.mnc -mask ${prefix}/gc_${subject}_t2.mnc -mask_floor 0.5`;
  chomp($intensity);
  $intensity*=1.0;
  do_cmd('minccalc',"${tmpdir}/clp2_${subject}_t2.mnc","${prefix}/clp_${subject}_t2.mnc", '-express', "A[0]*1000.0/$intensity", '-clobber','-short','-q');
}

if( ! -e "${prefix}/str_${subject}_t2.mnc" )
{
  do_cmd('itk_resample','--like',$model_mask,
         '--invert','--transform',"${prefix}/str_${subject}.xfm",
         "${prefix}/clp_${subject}_t2.mnc",
         "${prefix}/str_${subject}_t2.mnc");
}

if($qc && ! -e "${prefix}/qc_str_${subject}.jpg")
{
  do_cmd('minc_qc.pl',"${prefix}/str_${subject}_t2.mnc",
         "${prefix}/qc_str_${subject}.jpg",'--image-range',0,1000);
}

die "Stage 1 finished\n" if $stage1;

# linear registration
#if(! -e "${prefix}/lin_${subject}_t2.xfm")
#{
#   if( $manual )
#   {
#     if( ! -e "${prefix}/str_${subject}_man.tag")
#     {
#       do_cmd('xfminvert',"${prefix}/str_${subject}.xfm","$tmpdir/str_${subject}__.xfm");
# 
#       do_cmd('transformtags','-transformation',"$tmpdir/str_${subject}__.xfm",
#             $manual, "${prefix}/str_${subject}_man.tag");
# 
#       do_cmd('rm','-f',"$tmpdir/str_${subject}__.xfm","$tmpdir/str_${subject}___grid_0.mnc");
#     }
# 
#     if(! -e "${prefix}/str_${subject}_man.xfm")
#     {
#       do_cmd('tagtoxfm','-lsq6',"${prefix}/str_${subject}_man.tag","${prefix}/str_${subject}_man.xfm"); 
#     }
#   }

#   if( -e "${prefix}/str_${subject}_man.xfm")
#   {
#     do_cmd('bestlinreg_s','-lsq6',
#            "${prefix}/str_${subject}_t2.mnc",$model,"${prefix}/lin_${subject}_t2.xfm",
#            '-source_mask',"${prefix}/str_${subject}_mask.mnc",'-target_mask',$model_mask,
#            '-init_xfm',"${prefix}/str_${subject}_man.xfm",'-close');
#   } else  {
#    do_cmd('param2xfm',"$tmpdir/identity.xfm");

#    do_cmd('bestlinreg_s','-lsq6',
#           "${prefix}/str_${subject}_t2.mnc",$model,"${prefix}/lin_${subject}_t2.xfm",
#           '-init_xfm',"$tmpdir/identity.xfm");
#  }
#}

#if(! -e "${prefix}/lin_${subject}_t2.mnc")
#{
#  do_cmd('itk_resample','--like',$model,"${prefix}/str_${subject}_t2.mnc",'--transform',"${prefix}/lin_${subject}_t2.xfm","${prefix}/lin_${subject}_t2.mnc");
#}

#if($qc && ! -e "${prefix}/qc_lin_${subject}.jpg")
#{
#  do_cmd('minc_qc.pl',"${prefix}/lin_${subject}_t2.mnc","${prefix}/qc_lin_${subject}.jpg",'--mask',$model_bnd,'--image-range',0,1000);
#}

# NL registration, TODO: should I apply mask here?
if(! -e "${prefix}/nl_${subject}_t2.xfm")
{
  #do_cmd('nlfit_s',"${prefix}/str_${subject}_t2.mnc",$model_ref,"${prefix}/nl_${subject}_t2.xfm",'-level',2,'-start',8);
  do_cmd('ANTS',3, 
         '-m',"CC[$model,${prefix}/str_${subject}_t2.mnc,1,2]",
         '-x',$model_mask, 
         '-r','Guass[4,1]', 
         '-t','SyN[0.125,4]',
         '-i','200x200x200x100x0',
         '--number-of-affine-iterations','0x0x0',
         '-o',"${prefix}/nl_${subject}_t2.xfm");
}

if(! -e "${prefix}/nl_${subject}_t2.mnc")
{
  do_cmd('itk_resample','--like',$model,"${prefix}/str_${subject}_t2.mnc",
         '--transform',"${prefix}/nl_${subject}_t2.xfm","${prefix}/nl_${subject}_t2.mnc",
         '--invert_transform','--short');
}

if($qc && ! -e "${prefix}/qc_nl_${subject}.jpg")
{
  do_cmd('minc_qc.pl',"${prefix}/nl_${subject}_t2.mnc","${prefix}/qc_nl_${subject}.jpg",'--mask',$model_bnd,'--image-range',0,1000);
}

# all transforms are inverse apart from linear one
if(! -e "${prefix}/full_${subject}_t2.xfm")
{
  #do_cmd('xfminvert',"${prefix}/lin_${subject}_t2.xfm","${tmpdir}/ilin_${subject}_t2.xfm");
  do_cmd('xfminvert',"${prefix}/str_${subject}_inv.xfm","${tmpdir}/str_${subject}_inv_inv.xfm");
  do_cmd('xfmconcat',"${prefix}/nl_${subject}_t2.xfm",
                     "${tmpdir}/str_${subject}_inv_inv.xfm","${prefix}/full_${subject}_t2.xfm");
}

# warp labels from NL space back into linear space
#if(! -e "${prefix}/lin_levels_${subject}_t2.mnc")
#{
#  do_cmd('itk_resample','--like',"${prefix}/lin_${subject}_t2.mnc",'--transform',"${prefix}/nl_${subject}_t2.xfm",
#         $model_levels,"${prefix}/lin_levels_${subject}_t2.mnc",'--labels','--byte');
#}

# extract spinal cord, and warp it to a straight line
# if(! -e "${prefix}/lin_str_${subject}_t2.mnc")
# {
#   do_cmd('minccalc','-express','A[0]>=4?1:0','-byte',"${prefix}/lin_levels_${subject}_t2.mnc",
#          "${tmpdir}/lin_cord_${subject}_t2.mnc");
#   
#   do_cmd('itk_spine_straighten', "${tmpdir}/lin_cord_${subject}_t2.mnc","${tmpdir}/lin_cord_${subject}_t2.tag", '--smooth', 10,'--vertical');
#   
#   do_cmd('tagtoxfm', '-tps', "${tmpdir}/lin_cord_${subject}_t2.tag","${tmpdir}/lin_cord_${subject}_t2.xfm");
#   
#   unless( -e "${prefix}/lin_cord_${subject}_t2_norm.xfm")
#   {
#     do_cmd('xfm_normalize.pl',"${tmpdir}/lin_cord_${subject}_t2.xfm","${prefix}/lin_cord_${subject}_t2_norm.xfm",'--like',$model2_mask,'--step', 4);
#   }
#   
#   do_cmd('itk_resample',"${prefix}/lin_${subject}_t2.mnc",'--transform',"${prefix}/lin_cord_${subject}_t2_norm.xfm",'--invert_transform',
#          '--like',$model2_mask,"${prefix}/lin_str_${subject}_t2.mnc");
#   
#   do_cmd('itk_resample',"${prefix}/lin_levels_${subject}_t2.mnc",'--transform',"${prefix}/lin_cord_${subject}_t2_norm.xfm",'--invert_transform',
#          '--like',$model2_mask,"${prefix}/lin_str_levels_${subject}_t2.mnc",'--labels','--byte');
# }


if($tags && ! -e "${prefix}/nl_tags_${subject}_t2.tag")
{
  do_cmd('transform_tags',$tags,"${prefix}/nl_${subject}_t2.xfm","${prefix}/nl_tags_${subject}_t2.tag",'invert');
}

#if($qc && ! -e "${prefix}/qc_lin_labels_${subject}.jpg")
#{
  #do_cmd('minc_qc.pl',"${prefix}/lin_${subject}_t2.mnc","${prefix}/qc_lin_labels_${subject}.jpg",'--mask',"${prefix}/lin_levels_${subject}_t2.mnc",'--image-range',0,1000,'--labels-mask');
#  do_cmd('minc_pretty_pic.pl',
#                      "${prefix}/lin_${subject}_t2.mnc", 
#         '--overlay', "${prefix}/lin_levels_${subject}_t2.mnc", 
#                      "${prefix}/qc_lin_labels_${subject}.jpg",
#         '--sagittal', 60, '--coronal', 60,
#         '--max', '--image-range', 0, 2000);
#}

# warp labels from NL space back into native space
if(! -e "${prefix}/native_levels_${subject}_t2.mnc")
{
  do_cmd('itk_resample','--like',"${prefix}/clp_${subject}_t2.mnc",
         '--transform',"${prefix}/full_${subject}_t2.xfm",
         $model_levels,"${prefix}/native_levels_${subject}_t2.mnc",'--labels','--byte');
}

if(! -e "${prefix}/native_cord_${subject}_t2.mnc")
{
  do_cmd('itk_resample',
         "${prefix}/native_levels_${subject}_t2.mnc",
         "${prefix}/native_cord_${subject}_t2.mnc",
         '--lut-string', '4 1;5 1;6 1;7 1;8 1;9 1;10 1;11 1;12 1;13 1;14 1;15 1',
         '--labels','--byte');
}

if(! -e "${prefix}/native_gc_cord_${subject}.mnc")
{
  do_cmd('itk_resample',
         "${prefix}/gc_${subject}_t2.mnc",
         "${prefix}/native_gc_cord_${subject}.mnc",
         '--lut-string', '2 1;1 0',
         '--labels','--byte');
}

if(! -e "${prefix}/str_${subject}_levels.mnc")
{
  do_cmd('itk_resample',
        '--like', "${prefix}/str_${subject}_t2.mnc",
        '--invert','--transform', "${prefix}/str_${subject}.xfm",
        "${prefix}/native_levels_${subject}_t2.mnc", "${prefix}/str_${subject}_levels.mnc",
        '--labels');
}

if($validate)
{
  my $similarity;
  $similarity=`volume_similarity --csv ${prefix}/native_cord_${subject}_t2.mnc $validate`;

  open OUT,">${prefix}/compare_animal_${subject}.txt" or die;
  print OUT "$subject,$similarity";
  close OUT;
  
  $similarity=`volume_similarity --csv ${prefix}/native_gc_cord_${subject}.mnc $validate`;
  open OUT,">${prefix}/compare_gc_${subject}.txt" or die;
  print OUT "$subject,$similarity";
  close OUT;
}

if($qc && ! -e "${prefix}/qc_native_labels_${subject}.jpg")
{
  do_cmd('minc_qc.pl',"${prefix}/clp_${subject}_t2.mnc",
         "${prefix}/qc_native_labels_${subject}.jpg",
         '--mask',"${prefix}/native_levels_${subject}_t2.mnc",
         '--image-range',0,1000,'--labels-mask');
}


if(-e $model_WM && ! -e "${prefix}/native_WM_${subject}_t2.mnc")
{
  do_cmd('itk_resample','--like',"${prefix}/clp_${subject}_t2.mnc",
         '--transform',"${prefix}/full_${subject}_t2.xfm",
         $model_WM,"${prefix}/native_WM_${subject}_t2.mnc",'--order',1,'--short');
  
}

if( -e $model_GM && ! -e "${prefix}/native_GM_${subject}_t2.mnc")
{
  do_cmd('itk_resample','--like',"${prefix}/clp_${subject}_t2.mnc",
         '--transform',"${prefix}/full_${subject}_t2.xfm",
         $model_GM,"${prefix}/native_GM_${subject}_t2.mnc",'--order',1,'--short');
}

if(-e $model_CSF && ! -e "${prefix}/native_CSF_${subject}_t2.mnc")
{
  do_cmd('itk_resample','--like',"${prefix}/clp_${subject}_t2.mnc",
         '--transform',"${prefix}/full_${subject}_t2.xfm",
         $model_CSF,"${prefix}/native_CSF_${subject}_t2.mnc",'--order',1,'--short');
}

if($convert_nii)
{
  if(! -e "${prefix}/native_levels_${subject}_t2.nii.gz")
  {
    do_cmd('itk_convert','--byte','--inv-y',"${prefix}/native_levels_${subject}_t2.mnc","${prefix}/native_levels_${subject}_t2.nii");
    do_cmd('gzip','-9',"${prefix}/native_levels_${subject}_t2.nii");
  }

  if(! -e "${prefix}/native_GM_${subject}_t2.nii.gz")
  {
    do_cmd('itk_convert','--float','--inv-y',"${prefix}/native_GM_${subject}_t2.mnc","${prefix}/native_GM_${subject}_t2.nii");
    do_cmd('gzip','-9',"${prefix}/native_GM_${subject}_t2.nii");
  }


  if(! -e "${prefix}/native_WM_${subject}_t2.nii.gz")
  {
    do_cmd('itk_convert','--float','--inv-y',"${prefix}/native_WM_${subject}_t2.mnc","${prefix}/native_WM_${subject}_t2.nii");
    do_cmd('gzip','-9',"${prefix}/native_WM_${subject}_t2.nii");
  }


  if(! -e "${prefix}/native_CSF_${subject}_t2.nii.gz")
  {
    do_cmd('itk_convert','--float','--inv-y',"${prefix}/native_CSF_${subject}_t2.mnc","${prefix}/native_CSF_${subject}_t2.nii");
    do_cmd('gzip','-9',"${prefix}/native_CSF_${subject}_t2.nii");
  }
}

# warp spinal cord tags to native space
if(! -e "${prefix}/native_cord_${subject}.tag")
{
  do_cmd('transform_tags',$model_cord,"${prefix}/full_${subject}_t2.xfm","${prefix}/native_cord_${subject}.tag");
}

# measure cross-section & curvature 
if(! -e "${prefix}/measure_${subject}.csv")
{
  my @args=('itk_spine_measure_cros_section',
         "${prefix}/clp_${subject}_t2.mnc","${prefix}/native_levels_${subject}_t2.mnc","${prefix}/native_cord_${subject}.tag",
         "${prefix}/measure_${subject}.csv",
         '--extract',"${prefix}/extract_${subject}.mnc", 
         '--extract-seg',"${prefix}/extract_${subject}_seg.mnc",
         '--step',0.2,
         '--samples', 150,
         '--fwhm',0.5,
         '--fwhm-prior',0.5,
         '--curv',1.0,
         '--prop',0.2, 
         '--iter',1,
         '--spline',2,
         '--smooth',2.0,
         '--prior',0.1,
         '--gradient',0.5
        );
  if($validate)
  {
    push @args,'--validate',$validate;
  }
  do_cmd(@args);
}

if(! -e "${prefix}/measure_${subject}_animal.csv")
{ 
  my @args=('itk_spine_measure_cros_section',
         "${prefix}/clp_${subject}_t2.mnc","${prefix}/native_levels_${subject}_t2.mnc","${prefix}/native_cord_${subject}.tag",
         "${prefix}/measure_${subject}_animal.csv",
         '--extract',"${prefix}/extract_${subject}_animal.mnc", 
         '--extract-seg',"${prefix}/extract_${subject}_seg_animal.mnc",
         '--step',0.2,
         '--samples', 150,
         '--fwhm',0.5,
         '--fwhm-prior',0.5,
         '--curv',1.0,
         '--prop',0.2, 
         '--iter',0,
         '--spline',2,
         '--smooth',2.0,
         '--beta',0.1,
        );
  if($validate)
  {
    push @args,'--validate',$validate;
  }
  do_cmd(@args);
}


# measure GM
if(! -e "${prefix}/measure_${subject}_GM.csv")
{ 
  do_cmd('itk_spine_measure_cros_section',
         "${prefix}/clp_${subject}_t2.mnc","${prefix}/native_GM_${subject}_t2.mnc","${prefix}/native_cord_${subject}.tag",
         "${prefix}/measure_${subject}_GM.csv",
         '--step',0.2,
         '--samples', 150,
         '--fwhm',1.0,
         '--curv',1.0,
         '--prop',0.2, 
         '--iter',0,
         '--spline',4,
         '--smooth',4.0,
         '--continious',
        );
}

# measure WM
if(! -e "${prefix}/measure_${subject}_WM.csv")
{ 
  do_cmd('itk_spine_measure_cros_section',
         "${prefix}/clp_${subject}_t2.mnc","${prefix}/native_WM_${subject}_t2.mnc","${prefix}/native_cord_${subject}.tag",
         "${prefix}/measure_${subject}_WM.csv",
         '--step',0.2,
         '--samples', 150,
         '--fwhm',2.0,
         '--curv',1.0,
         '--prop',0.2, 
         '--iter',0,
         '--spline',4,
         '--smooth',4.0,
         '--continious',
        );
}



sub do_cmd {
    print STDOUT "@_\n" if $verbose;
    if(!$fake) {
        system(@_) == 0 or die "DIED: @_\n";
  }
}

sub check_file {
  die("${_[0]} exists!\n") if -e $_[0];
}

sub check_presence {
  my $i;
  foreach $i(@_)
  { 
    die("$i does not exists!\n") unless -e $i;
  }
}

