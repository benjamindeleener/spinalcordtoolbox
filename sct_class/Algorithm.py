#!/usr/bin/env python


class Algorithm(object):

    def __init__(self, input_image, produce_output=1, verbose=1):
        self._input_image = input_image
        self._verbose = verbose
        self._produce_output = produce_output

    @property
    def input_image(self):
        return self._input_image

    @input_image.setter
    def input_image(self, value):
        self._input_image = value

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, value):
        self._verbose = value

    @property
    def produce_output(self):
        return self._produce_output

    @produce_output.setter
    def produce_output(self, value):
        self._produce_output = value

    def execute(self):
        raise NotImplementedError("This method should be implemented in a child class")

