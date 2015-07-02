#!/usr/bin/env python


from msct_parser import Parser
import sys
import os
import time
import numpy
import nibabel
from scipy import ndimage
from msct_image import Image
import sct_utils as sct
from sct_orientation import get_orientation
from sct_algorithm import Algorithm


class CreateMask(Algorithm):

    # class constants definition
    OUTPUT_PREFIX = "mask_"
    METHOD_LIST = ['coord', 'point', 'centerline', 'center']
    SHAPE_LIST = ['cylinder', 'box', 'gaussian']
    DEFAULT_SHAPE = "cylinder"
    DEFAULT_METHOD = "center"
    DEFAULT_SIZE = 41

    def __init__(self, input_image, output_file=None, method=DEFAULT_METHOD, method_value=None, shape=DEFAULT_SHAPE, size=DEFAULT_SIZE, verbose=1, rm_tmp_files=1, rm_output_file=0, produce_output=1):
        super(CreateMask, self).__init__(input_image, produce_output, verbose)
        self._output_file = output_file
        self._method = method
        self._method_value = method_value
        self._shape = shape
        self._size = size
        self._rm_tmp_files = rm_tmp_files
        self._result = None
        self._rm_output_file = rm_output_file

    @property
    def output_file(self):
        return self._output_file

    @output_file.setter
    def output_file(self, value):
        self._output_file = value

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, value):
        self._method = value

    @property
    def method_value(self):
        return self._method_value

    @method_value.setter
    def method_value(self, value):
        self._method_value = value

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, value):
        self._shape = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    @property
    def rm_tmp_files(self):
        return self._rm_tmp_files

    @rm_tmp_files.setter
    def rm_tmp_files(self, value):
        self._rm_tmp_files = value

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        self._result = value

    @property
    def rm_tmp_files(self):
        return self._rm_tmp_files

    @rm_tmp_files.setter
    def rm_tmp_files(self, value):
        self._rm_tmp_files = value

    def mask_method(self, nx, ny, nz, nt, px, py, pz, pt, path_tmp):
        raise NotImplementedError("Use a child class of mask to chose which method will be used")

    def execute(self):
        """
        This method creates a mask and returns the result either through a file or as an msct_image Image object

        """
        fsloutput = 'export FSLOUTPUTTYPE=NIFTI; '

        # checking if shape is valid
        if self._shape not in CreateMask.SHAPE_LIST:
            sct.printv('\nERROR in '+os.path.basename(__file__)+': Shape "'+self._shape+'" is not recognized. \n', self.verbose, 'error')

        # checking orientation in RPI
        if not get_orientation(self.input_image) == 'RPI':
            sct.printv('\nERROR in '+os.path.basename(__file__)+': Orientation of input image should be RPI. Use sct_orientation to put your image in RPI.\n', 1, 'error')

        # display input parameters
        sct.printv('\nInput parameters:', self.verbose)
        sct.printv('  data ..................'+self.input_image, self.verbose)
#        sct.printv('  method ................'+method_type, self.verbose)

        # Extract path/file/extension
        path_data, file_data, ext_data = sct.extract_fname(self.input_image)

        # Get output folder and file name
        if self._output_file is None:
            self._output_file = CreateMask.OUTPUT_PREFIX+file_data+ext_data

        # creating temporary folder
        path_tmp = sct.slash_at_the_end('tmp.'+time.strftime("%y%m%d%H%M%S"), 1)
        os.mkdir(path_tmp)

        # Copying input data to tmp folder and convert to nii
        # NB: cannot use c3d here because c3d cannot convert 4D data.
        sct.printv('\nCopying input data to tmp folder and convert to nii...', self.verbose)
        sct.run('cp '+self.input_image+' '+path_tmp+'data'+ext_data, self.verbose)

        # go to tmp folder
        os.chdir(path_tmp)
        try:
            # convert to nii format
            sct.run('fslchfiletype NIFTI data', self.verbose)

            # Get dimensions of data
            nx, ny, nz, nt, px, py, pz, pt = sct.get_dimension('data.nii')
            sct.printv('  ' + str(nx) + ' x ' + str(ny) + ' x ' + str(nz)+ ' x ' + str(nt), self.verbose)

            # self.mask_method(nx, ny, nz, nt, px, py, pz, pt)

            # in case user input 4d data
            if nt != 1:
                sct.printv('WARNING in '+os.path.basename(__file__)+': Input image is 4d but output mask will 3D.', self.verbose, 'warning')
                # extract first volume to have 3d reference
                sct.run(fsloutput+'fslroi data data -0 1', self.verbose)

            # if method_type == 'coord':
            #     # parse to get coordinate
            #     coord = map(int, method_val.split('x'))
            #
            # if method_type == 'point':
            #     # get file name
            #     fname_point = method_val
            #     # extract coordinate of point
            #     sct.printv('\nExtract coordinate of point...', self.verbose)
            #     # TODO : Running outside script
            #     status, output = sct.run('sct_label_utils -i '+fname_point+' -t display-voxel', self.verbose)
            #     # parse to get coordinate
            #     coord = output[output.find('Position=')+10:-17].split(',')
            #
            # if method_type == 'center':
            #     # set coordinate at center of FOV
            #     coord = round(float(nx)/2), round(float(ny)/2)
            #
            # if method_type == 'centerline':
            #     # get name of centerline from user argument
            #     fname_centerline = 'centerline.nii.gz'
            # else:
            #     # generate volume with line along Z at coordinates 'coord'
            #     sct.printv('\nCreate line...', self.verbose)
            #     fname_centerline = self.create_line('data.nii', coord, nz)

            fname_centerline = self.mask_method(nx, ny, nz, nt, px, py, pz, pt, path_tmp)

            # create mask
            sct.printv('\nCreate mask...', self.verbose)
            try:
                centerline = nibabel.load(fname_centerline)  # open centerline
            except Exception, e:
                sct.printv(e.message,"warning")
            hdr = centerline.get_header()  # get header
            hdr.set_data_dtype('uint8')  # set imagetype to uint8
            data_centerline = centerline.get_data()  # get centerline
            z_centerline = [iz for iz in range(0, nz, 1) if data_centerline[:, :, iz].any()]
            nz = len(z_centerline)
            # get center of mass of the centerline
            cx = [0] * nz
            cy = [0] * nz
            for iz in range(0, nz, 1):
                cx[iz], cy[iz] = ndimage.measurements.center_of_mass(numpy.array(data_centerline[:, :, z_centerline[iz]]))

            # create 2d masks
            file_mask = 'data_mask'
            for iz in range(nz):
                center = numpy.array([cx[iz], cy[iz]])
                mask2d = self.create_mask2d(center, self._shape, self._size, nx, ny)
                # Write NIFTI volumes
                img = nibabel.Nifti1Image(mask2d, None, hdr)
                nibabel.save(img, (file_mask+str(iz)+'.nii'))
            # merge along Z
            cmd = 'fslmerge -z mask '
            for iz in range(nz):
                cmd = cmd + file_mask+str(iz)+' '
            status, output = sct.run(cmd, self.verbose)

            # copy geometry
            sct.run(fsloutput+'fslcpgeom data mask', self.verbose)

        except:
            pass # TODO : Add the exception handler
        # come back to parent folder
        os.chdir('..')

        # Generate output files
        sct.printv('\nGenerate output files...', self.verbose)
        sct.generate_output_file(path_tmp+'mask.nii.gz', self._output_file)

        # Remove temporary files
        if self._rm_tmp_files == 1:
            sct.printv('\nRemove temporary files...', self.verbose)
            sct.run('rm -rf '+path_tmp, self.verbose)

        # to view results
        sct.printv('\nDone! To view results, type:', self.verbose)
        sct.printv('fslview '+self.input_image+' '+self._output_file+' -l Red -t 0.5 &', self.verbose, 'info')
        print

        self._result = Image(self._output_file)

        if self.produce_output == 0:
            try:
                os.remove(self._output_file)
            except OSError:
                sct.printv("WARNING : Couldn't remove output file. Either it is opened elsewhere or "
                           "it doesn't exist.", 0, 'warning')
        else:
            # Complete message
            sct.printv('\nDone! To view results, type:', self.verbose)
            sct.printv("fslview "+self._output_file+" &\n", self.verbose, 'info')

        return self._result


    # create_line
    # ==========================================================================================
    def create_line(self, fname, coord, nz):

        # duplicate volume (assumes input file is nifti)
        sct.run('cp '+fname+' line.nii', self.verbose)
        # set all voxels to zero
        sct.run('isct_c3d line.nii -scale 0 -o line.nii', self.verbose)
        # loop across z and create a voxel at a given XY coordinate
        cmd = 'sct_label_utils -i line.nii -o line.nii -t add -x '
        # for iz in range(nz):
        #     sct.run('sct_label_utils -i line.nii -o line.nii -t add -x '+str(int(coord[0]))+','+str(int(coord[1]))+','+str(iz)+',1', self.verbose)
        for iz in range(nz):
            if iz == nz-1:
                cmd += str(int(coord[0]))+','+str(int(coord[1]))+','+str(iz)+',1'
            else:
                cmd += str(int(coord[0]))+','+str(int(coord[1]))+','+str(iz)+',1:'

        sct.run(cmd, self.verbose)
        return 'line.nii'

    # create_mask2d
    # ==========================================================================================
    def create_mask2d(self, center, shape, size, nx, ny):

        # initialize 2d grid
        xx, yy = numpy.mgrid[:nx, :ny]
        mask2d = numpy.zeros((nx, ny))
        xc = center[0]
        yc = center[1]
        radius = round(float(size+1)/2)  # add 1 because the radius includes the center.

        if shape == 'box':
            mask2d[xc-radius:xc+radius+1, yc-radius:yc+radius+1] = 1

        elif shape == 'cylinder':
            mask2d = ((xx-xc)**2 + (yy-yc)**2 <= radius**2)*1

        elif shape == 'gaussian':
            sigma = float(radius)
            mask2d = numpy.exp(-(((xx-xc)**2)/(2*(sigma**2)) + ((yy-yc)**2)/(2*(sigma**2))))

        # import matplotlib.pyplot as plt
        # plt.imshow(mask2d)
        # plt.show()

        return mask2d

    # create_centerline
    # ==========================================================================================
    def create_centerline(self, coord, nz):
        sct.printv('\nCreate line...', self.verbose)
        return self.create_line('data.nii', coord, nz)

class CreateMaskFromCoordinates(CreateMask):
    def __init__(self, input_image, output_file=None, method_value=None, shape=CreateMask.DEFAULT_SHAPE, size=CreateMask.DEFAULT_SIZE, verbose=1, rm_tmp_files=1, rm_output_file=0, produce_output=1):
        super(CreateMaskFromCoordinates, self).__init__(input_image=input_image, output_file=output_file, method_value=method_value, shape=shape, size=size, verbose=verbose, rm_tmp_files=rm_tmp_files, rm_output_file=rm_output_file, produce_output=produce_output)

    def mask_method(self, nx, ny, nz, nt, px, py, pz, pt, path_tmp):
        coord = map(int, self.method_value.split('x'))
        return self.create_centerline(coord, nz)


class CreateMaskFromPoint(CreateMask):
    def __init__(self, input_image, output_file=None, method_value=None, shape=CreateMask.DEFAULT_SHAPE, size=CreateMask.DEFAULT_SIZE, verbose=1, rm_tmp_files=1, rm_output_file=0, produce_output=1):
        super(CreateMaskFromPoint, self).__init__(input_image=input_image, output_file=output_file, method_value=method_value, shape=shape, size=size, verbose=verbose, rm_tmp_files=rm_tmp_files, rm_output_file=rm_output_file, produce_output=produce_output)

    def mask_method(self, nx, ny, nz, nt, px, py, pz, pt, path_tmp):
        # get file name
        fname_point = self.method_value
        # extract coordinate of point
        sct.printv('\nExtract coordinate of point...', self.verbose)
        # TODO : Running outside script
        status, output = sct.run('sct_label_utils -i '+fname_point+' -t display-voxel', self.verbose)
        # parse to get coordinate
        coord = output[output.find('Position=')+10:-17].split(',')
        return self.create_centerline(coord, nz)


class CreateMaskAtCenter(CreateMask):
    def __init__(self, input_image, output_file=None, method_value=None, shape=CreateMask.DEFAULT_SHAPE, size=CreateMask.DEFAULT_SIZE, verbose=1, rm_tmp_files=1, rm_output_file=0, produce_output=1):
        super(CreateMaskAtCenter, self).__init__(input_image=input_image, output_file=output_file, method_value=method_value, shape=shape, size=size, verbose=verbose, rm_tmp_files=rm_tmp_files, rm_output_file=rm_output_file, produce_output=produce_output)

    def mask_method(self, nx, ny, nz, nt, px, py, pz, pt, path_tmp):
        coord = round(float(nx)/2), round(float(ny)/2)
        return self.create_centerline(coord, nz)


class CreateMaskFromCenterline(CreateMask):
    def __init__(self, input_image, output_file=None, method_value=None, shape=CreateMask.DEFAULT_SHAPE, size=CreateMask.DEFAULT_SIZE, verbose=1, rm_tmp_files=1, rm_output_file=0, produce_output=1):
        super(CreateMaskFromCenterline, self).__init__(input_image=input_image, output_file=output_file, method_value=method_value, shape=shape, size=size, verbose=verbose, rm_tmp_files=rm_tmp_files, rm_output_file=rm_output_file, produce_output=produce_output)

    def mask_method(self, nx, ny, nz, nt, px, py, pz, pt, path_tmp):
        sct.check_file_exist(self.method_value, self.verbose)
        sct.run('isct_c3d '+self.method_value+' -o centerline.nii.gz')
        return "centerline.nii.gz"


if __name__ == "__main__":
    # Initialize parser,
    parser = Parser(__file__)

    parser.usage.set_description('Creates a mask with a specific method and shape and returns it as a file')
    parser.add_option(name="-i",
                      type_value="image_nifti",
                      description="input image.",
                      mandatory=True,
                      example="t2.nii.gz")
    parser.add_option(name="-m",
                      type_value='str',
                      description="""method to generate mask and associated value.\ncoord: X,Y coordinate of center of mask. E.g.: coord,20x15\npoint: volume that contains a single point. E.g.: point,label.nii.gz\ncenter: mask is created at center of FOV. In that case, "val" is not required.\ncenterline: volume that contains centerline. E.g.: centerline,my_centerline.nii")""",
                      mandatory=False,
                      default_value=CreateMask.DEFAULT_METHOD)
    parser.add_option(name="-s",
                      type_value="int",
                      description="size in voxel. Odd values are better (for mask to be symmetrical).If shape=gaussian, size corresponds to sigma",
                      mandatory=False,
                      default_value=CreateMask.DEFAULT_SIZE,
                      example="41")
    parser.add_option(name="-f",
                      type_value="str",
                      description="shape of the mask.",
                      mandatory=False,
                      default_value=CreateMask.DEFAULT_SHAPE,
                      example="gaussian")
    parser.add_option(name="-o",
                      type_value="file_output",
                      description="output image.",
                      mandatory=False,
                      example="test.nii.gz")
    parser.add_option(name="-r",
                      type_value="multiple_choice",
                      description="Remove temporary files.",
                      mandatory=False,
                      default_value=1,
                      example=['0', '1'])
    parser.add_option(name="-v",
                      type_value="multiple_choice",
                      description="Verbose",
                      mandatory=False,
                      default_value=0,
                      example=['0', '1'])

    # Fetching script arguments
    arguments = parser.parse(sys.argv[1:])

    input_filename = arguments["-i"]

    if "-m" in arguments:
        method_list = arguments["-m"].replace(' ', '').split(',')
        if method_list[0] == "center":
            mask = CreateMaskAtCenter(input_filename)
        elif method_list[0] == "centerline":
            mask = CreateMaskFromCenterline(input_filename)
        elif method_list[0] == "point":
            mask = CreateMaskFromPoint(input_filename)
        elif method_list[0] == "coord":
            mask = CreateMaskFromCoordinates(input_filename)
        else:
            sct.printv("Mask method invalid", "error")
        if len(method_list) == 2:
            mask.method_value = method_list[1]
        elif len(method_list) > 2:
            sct.printv("Seperate the method by its values with only 1 coma.", "warning")

    # Handling arguments
    if "-o" in arguments:
        mask.output_file = arguments["-o"]
    if "-f" in arguments:
        mask.shape = arguments["-f"]
    if "-s" in arguments:
        mask.size = arguments["-s"]
    if "-r" in arguments:
        mask.rm_tmp_files = arguments["-r"]
    if "-v" in arguments:
        mask.verbose = arguments["-v"]

    mask.execute()
