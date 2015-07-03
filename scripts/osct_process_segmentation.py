from msct_base_classes import Algorithm, BaseScript
from msct_parser import Parser
import sys
import sct_utils as sct


class ProcessSegmentation(Algorithm):



    def __init__(self, input_image, process_name, produce_output=1, verbose=1, debug=0, step=1, remove_temp_files=1, volume_output=0, smoothing_param=50, figure_fit=0,
                 fname_csa='csa.txt', name_output='csa_volume.nii.gz', name_method='counting_z_plane', slices='',
                 vertebral_levels='', path_to_template='', type_window='hanning', window_length=50, algo_fitting='hanning'):
        super(ProcessSegmentation, self).__init__(input_image=input_image, produce_output=produce_output, verbose=verbose)
        self._process_name = process_name
        self._debug = debug
        self._step = step  # step of discretized plane in mm default is min(x_scale,py)
        self._remove_temp_files = remove_temp_files
        self._volume_output = volume_output
        self._smoothing_param = smoothing_param  # window size (in mm) for smoothing CSA along z. 0 for no smoothing.
        self._figure_fit = figure_fit
        self._fname_csa = fname_csa  # output name for txt CSA
        self._name_output = name_output  # output name for slice CSA
        self._name_method = name_method  # for compute_CSA
        self._slices = slices
        self._vertebral_levels = vertebral_levels
        self._path_to_template = path_to_template
        self._type_window = type_window  # for smooth_centerline @sct_straighten_spinalcord
        self._window_length = window_length  # for smooth_centerline @sct_straighten_spinalcord
        self._algo_fitting = algo_fitting  # nurbs, hanning

    def execute(self):
        raise NotImplementedError("Please use a concrete implementation of a process : CSAProcess, CenterlineProcess or LengthProcess")

class CSAProcess(ProcessSegmentation):


class ScriptProcessSegmentation(BaseScript):
    def __init__(self):
        super(ScriptProcessSegmentation, self).__init__()

    @staticmethod
    def get_parser():
        # Init parser
        parser = Parser(__file__)

        parser.usage.set_description("This function performs various types of processing from the spinal cord segmentation")
        parser.add_option(name="-i",
                          type_value="image_nifti",
                          description="segmentation image.",
                          mandatory=True,
                          example="t2.nii.gz")
        parser.add_option(name="-p",
                          type_value="multiple_choice",
                          description="type of process to be performed:\n- centerline: extract centerline as binary file\n - length: compute length of the segmentation\n - csa: computes cross-sectional area by counting pixels in each\n  slice and then geometrically adjusting using centerline orientation.\n  Output is a text file with z (1st column) and CSA in mm^2 (2nd column) and\n  a volume in which each slice\'s value is equal to the CSA (mm^2).",
                          mandatory=True,
                          example=['centerline', 'csa', 'length'])
        # optional arguments
        parser.add_option(name="-s",
                          type_value="multiple_choice",
                          description="smooth CSA values with spline.",
                          mandatory=False,
                          example=["0", '1'],
                          default_value=1)
        parser.add_option(name="-b",
                          type_value="multiple_choice",
                          description="outputs a volume in which each slice's value is equal to the CSA in mm^2.",
                          mandatory=False,
                          example=["0", '1'],
                          default_value=0)
        parser.add_option(name="-z",
                          type_value=[[':'], 'int'],
                          description="Slice range to compute the CSA across (requires \"-p csa\").\nExample: 5:23. First slice is 0.", # TODO : Implement an option of the parser in order to parse multiple layer of lists
                          mandatory=False,
                          example="[5:23]")
        parser.add_option(name="-l",
                          type_value=[[':'], 'int'],
                          description="Vertebral levels to compute the CSA across (requires \"-p csa\").",
                          mandatory=False,
                          example="[5:23]")
        parser.add_option(name="-t",
                          type_value="string",
                          description="Path to warped template. Typically: ./label/template.\n Only use with flag -l",
                          mandatory=False,
                          example="./label/template")
        parser.add_option(name="-w",
                          type_value="string",
                          description="Smoothing window size. Only used with \'centerline\'",
                          mandatory=False,
                          example=["0", '1'])
        parser.add_option(name="-o",
                          type_value="file_output",
                          description="name of the output volume if -b 1.",
                          mandatory=False,
                          example="csa_volume.nii.gz",
                          default_value="csa_volume.nii.gz")
        parser.add_option(name="-r",
                          type_value="multiple_choice",
                          description="remove temporary files.",
                          mandatory=False,
                          example=["0", '1'],
                          default_value=1)
        parser.add_option(name="-a",
                          type_value="multiple_choice",
                          description="remove temporary files.",
                          mandatory=False,
                          example=["hanning", 'nurbs'],
                          default_value="hanning")

        return parser

    def main(self):
        parser = self.get_parser()

        arguments = parser.parse(sys.argv[1:])

        # assigning variables to arguments
        input_filename = arguments["-i"]
        process = arguments["-p"]

        sc_process = ProcessSegmentation(input_image=input_filename, process_name=process)

        if "-m" in arguments:
            sc_process.name_method = arguments["-m"]
        if "-b" in arguments:
            sc_process.volume_output = int(arguments["-b"])
        if "-l" in arguments:
            sc_process.vertebral_levels = arguments["-l"]
        if "-r" in arguments:
            sc_process.remove_temp_files = int(arguments["-r"])
        if "-s" in arguments:
            sc_process.smoothing_param = int(arguments["-s"])
        if "-f" in arguments:
            sc_process.figure_fit = int(arguments["-f"])
        if "-o" in arguments:
            sc_process.name_output = arguments["-o"]
        if "-t" in arguments:
            sc_process.name_output = arguments["-t"]
        if "-z" in arguments:
            sc_process.name_output = arguments["-z"]
        if "-v" in arguments:
            sc_process.verbose = int(arguments["-v"])
        if "-a" in arguments:
            sc_process.verbose = str(arguments["-a"])

        sc_process.execute()

if __name__ == "__main__":
    script = ScriptProcessSegmentation()
    script.main()