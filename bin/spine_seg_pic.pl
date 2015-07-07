#!/usr/bin/env perl

#----------------------------- MNI Header -----------------------------------
#@NAME       : spine_seg.pl
#@DESCRIPTION: spine picture generator
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

use File::Basename;
use File::Temp qw/ tempfile tempdir /;
use Getopt::Long;
use POSIX qw(floor);
use strict;

my $fake=0;
my $verbose=0;
my $clobber=0;
my $me=basename($0);
my $debug=0;
my @image_range;
my @ovl_range;
my $slices;
my $overlay;
my $separate;
my $out_coronal;
my $out_axial;
my $out_sagittal;
my $mask;
my $scale;
my $max;
my $over;
my $vertical;
my $cyanred=0;
my $lut;
my $discrete;
my $background='black';
my $foreground='white';
my $title;
my $pointsize;
my $tile='1x1';

GetOptions (    
          "verbose"          => \$verbose,
          "clobber"          => \$clobber,
          'image-range=f{2}' => \@image_range,
          'ovl-range=f{2}'   => \@ovl_range,
          "overlay=s"        => \$overlay,
          "mask=s"           => \$mask,
          "scale=n"          => \$scale,
          'separate'         => \$separate,
          'slices=s'         => \$slices,
          'max'              => \$max,
          'over'             => \$over,
          'vertical'         => \$vertical,
          'cyanred'          => \$cyanred,
          'lut=s'            => \$lut,
          'discrete'         => \$discrete,
          'background=s'     => \$background,
          'foreground=s'     => \$foreground,
          'title=s'          => \$title,
          'pointsize=n'      => \$pointsize,
          'tile=s'           => \$tile
          );
          
die <<END  if $#ARGV<1;
Usage: $me <scan_in> <scan_out> 
[ --verbose
  --clobber
  --image-range a b
  --ovl-range a b 
  --overlay <overlay>
  --separate
  --mask <mask for overlay>
  --scale <n>
  --slices <n1>,<n2>...<n3>
  --max - use max to combine images
  --vertical - montage vertically 
  --over put overlay on top of image
  --cyanred use cyan-red for overlay
  --lut <lut table for overlay>
  --discrete <use discrete labels for overlay>
  --background <color>, default black
  --foreground <color>, default white
  --title <title>
  --pointsize <n>
  --tile <AxB>
]
END

my ($in,$out)=@ARGV;

my @slices_=split(',',$slices);

die "Specify --slices " if $#slices_==-1;


unless($separate) {
  check_file($out) unless $clobber;
}
my $tmpdir = &tempdir( "$me-XXXXXXXX", TMPDIR => 1, CLEANUP => 1 );

delete $ENV{MINC_COMPRESS} if $ENV{MINC_COMPRESS};

#produce RGB images
my @args=("minclookup",$in,"$tmpdir/gray.mnc",'-gray','-byte');
push @args,'-min',$image_range[0],'-max',$image_range[1] if $#image_range>0;
do_cmd(@args);

if($overlay)
{
  #do_cmd('mincresample',$overlay,'-like',$in,"$tmpdir/overlay.mnc",'-float');
  @args=("minclookup",$overlay,"$tmpdir/overlay_rgb.mnc",'-byte');

  if($cyanred)
  { 
    push @args,'-lut_string',"0.000 0.8 1.0 1.0;0.125 0.4 0.9 1.0;0.250 0.0 0.6 1.0;\
0.375 0.0 0.2 0.5;0.500 0.0 0.0 0.0;0.625 0.5 0.0 0.0;0.750 1.0 0.4 0.0;\
0.825 1.0 0.8 0.4;1.000 1.0 0.8 0.8";

  } elsif($lut) {
    
    push @args,'-lookup_table',$lut;
    push @args,'-discrete' if $discrete;
    
  } else {
    push @args,'-spectral';
  }

  push @args,'-min',$ovl_range[0],'-max',$ovl_range[1] if $#ovl_range>0;
  do_cmd(@args);
  
  #mix colors
  
  if($over) {
    if($#ovl_range>0)
    {
      do_cmd('minccalc','-express',"A[0]>$ovl_range[0]?1:0",'-byte',$overlay,"$tmpdir/ovl_mask.mnc");
      do_cmd('minclookup','-gray',"$tmpdir/ovl_mask.mnc","$tmpdir/ovl_mask_g.mnc",'-min',0,'-max',1);
      do_cmd('minccalc','-express','A[2]>0.5?A[1]:A[0]',
           "$tmpdir/gray.mnc","$tmpdir/overlay_rgb.mnc","$tmpdir/ovl_mask_g.mnc","$tmpdir/gray_.mnc");
    } else {
      print STDERR "Use --ovl-range with --over!\n";
    }
  } elsif($max) {
    do_cmd('mincmath','-max',"$tmpdir/gray.mnc","$tmpdir/overlay_rgb.mnc","$tmpdir/gray_.mnc");
  } else {
    do_cmd('mincaverage',"$tmpdir/gray.mnc","$tmpdir/overlay_rgb.mnc","$tmpdir/gray_.mnc");
  }
  do_cmd('mv',"$tmpdir/gray_.mnc","$tmpdir/gray.mnc");
}


my $s;

my @out_s;

for $s(@slices_)
{
  # produce individual slices
  @args=('mincpik',"$tmpdir/gray.mnc","$tmpdir/axial_$s.miff",'-axial','-slice',$s);
  push @args,'-scale',$scale if $scale;
  do_cmd(@args);
  push @out_s,"$tmpdir/axial_$s.miff";
}

if($separate)
{
  for $s(@slices_)
  {
    do_cmd('convert',"$tmpdir/axial_$s.miff","${out}_$s.png");
  }
} else {
  my $geo='+0+0';

  my @args=('montage','-depth',8,#'-texture','rose:',
          '-tile',$tile,
          '-geometry',$geo,'-gravity','North',
          '-background' ,$background,
          '-bordercolor',$background,
          '-mattecolor',$background,
          '-fill',$foreground,
          '-stroke',$foreground,
         @out_s);
  push @args,'-pointsize',$pointsize if $pointsize;
  push @args,'-title',$title if $title;
  push @args,$out;
  
  do_cmd(@args);
}

#####################################################################
sub do_cmd { 
    print STDOUT "@_\n" if $verbose;
    if(!$fake){
      system(@_) == 0 or die "DIED: @_\n";
    }
}

sub check_file {
  if($_[0] && -e $_[0])
  {
    die("${_[0]} exists!\n");
    return 0;
  }    
  return 1;
}

sub equalize_height {
  my @in=@_;
  my @h;    
  my $i;

  for($i=0;$i<=$#in;$i+=1)
  {
    chomp($h[$i]=`identify -format '%h' $in[$i] `);
  }
  
  my @hh = sort {$b <=> $a} @h;
  my $mh=$hh[0];
  
  for($i=0;$i<=$#in;$i+=1)
  {
    my $w=($mh-$h[$i])/2;
    next if $w<=0;
    do_cmd('convert','-bordercolor','black','-border',"1x${w}",$in[$i],$in[$i]);
  }
}

sub equalize_width {
  my @in=@_;
  my @h;    
  my $i;

  for($i=0;$i<=$#in;$i+=1)
  {
    chomp($h[$i]=`identify -format '%w' $in[$i] `);
  }
  
  my @hh = sort {$b <=> $a} @h;
  my $mh=$hh[0];
  
  for($i=0;$i<=$#in;$i+=1)
  {
    my $w=($mh-$h[$i])/2;
    next if $w<=0;
    do_cmd('convert','-bordercolor','black','-border',"${w}x1",$in[$i],$in[$i]);
  }
}
