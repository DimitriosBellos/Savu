# Copyright 2014 Diamond Light Source Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. module:: spectrum_crop
   :platform: Unix
   :synopsis: A plugin to crop a spectra

.. moduleauthor:: Aaron D. Parsons <scientificsoftware@diamond.ac.uk>
"""

import logging
from savu.plugins.base_filter import BaseFilter
from savu.plugins.driver.cpu_plugin import CpuPlugin
from savu.plugins.utils import register_plugin, dawn_compatible
import numpy as np
import os
import savu.test.test_utils as tu
from PyMca5.PyMcaPhysics.xrf import McaAdvancedFitBatch

@dawn_compatible
@register_plugin
class Pymca(BaseFilter, CpuPlugin):
    """
    crops a spectrum to a range

    :param config: path to the config file. Default: 'Savu/test_data/data/test_config.cfg'.

    """

    def __init__(self):
        logging.debug("fitting spectrum")
        super(Pymca, self).__init__("Pymca")
        
    def pre_process(self):
        in_dataset, _out_datasets = self.get_datasets()
        in_d1 = in_dataset[0]
        self.sh = in_d1.get_shape()
        self.b = self.setup_fit(np.random.random((1,1,self.sh[-1])))

    def filter_frames(self, data):
        y = np.expand_dims(data,0)
        self.b = self.setup_fit(y)
        self.b._McaAdvancedFitBatch__processStack()
        try:
            stack = np.array(self.b._McaAdvancedFitBatch__images.values())
            op_stack = np.rollaxis(stack,0,3)
        except AttributeError as e:
            op_stack = -np.ones((1,1,self.outputshape[-1]))
            logging.warn("Error in fit:%s",e) 
        op = op_stack[0,0]
        print "shape", op.shape
        return op

    def setup(self):
        logging.debug('setting up the pymca fitting')
        in_dataset, out_datasets = self.get_datasets()
        inshape = in_dataset[0].get_shape()
        spectra_shape = inshape[-1] #  nearly always true.
        rest_shape = inshape[:-1]
        dummy_spectrum = np.random.random((1, 1, spectra_shape))
        c = self.setup_fit(dummy_spectrum)# seed it with junk, zeros made the matrix singular unsurprisingly and this bungles it.
        
        c.processList()#_McaAdvancedFitBatch__processStack()# perform an initial fit to get the shapes
        fit_labels = c._McaAdvancedFitBatch__images.keys() # and then take out the axis labels for the channels
        out_meta_data = out_datasets[0].meta_data
        out_meta_data.set_meta_data("PeakElements",fit_labels)
        print fit_labels
        self.outputshape = rest_shape+(len(fit_labels),) # and this is the shape the thing will be
#         print "input shape is", in_dataset[0].get_shape()
#         print "the output shape in setup is"+str(outputshape)
        
        axis_labels = ['-1.PeakElements.label']
        pattern_list = ['SINOGRAM', 'PROJECTION']
        fitResult = out_datasets[0]

        fitResult.create_dataset(patterns={in_dataset[0]: pattern_list},
                                axis_labels={in_dataset[0]: axis_labels},
                                shape=self.outputshape)
        fitResult.meta_data.set_meta_data('FitAreas',np.array(fit_labels))
        slice_directions = tuple(range(len(rest_shape)))
#         print "slice directions are:"+str(slice_directions)
        fitResult.add_pattern("CHANNEL", core_dir=(-1,),
                        slice_dir=slice_directions)
        
        in_pData, out_pData = self.get_plugin_datasets()
        in_pData[0].plugin_data_setup(self.get_plugin_pattern(), self.get_max_frames())
        out_pData[0].plugin_data_setup('CHANNEL', self.get_max_frames())
        
        
    def get_max_frames(self):
        """
        This filter processes 1 frame at a time

        """
        return 1

    def get_plugin_pattern(self):
        return 'SPECTRUM'

    def nOutput_datasets(self):
        return 1

    def setup_fit(self,y):
        '''
        takes a data shape and returns a fit-primed object
        '''
        outputdir=None # nope
        roifit=0# nope
        roiwidth=y.shape[1] #need this to pretend its an image
        b = McaAdvancedFitBatch.McaAdvancedFitBatch(self.get_conf_path(),
                                                    [y],
                                                    outputdir,
                                                    roifit,
                                                    roiwidth,
                                                    fitfiles=0,
                                                    nosave=True) # prime the beauty
        b.pleaseBreak = 1
        b.processList()
        b.pleaseBreak = 0
        return b
    
    def get_conf_path(self):
        path = self.parameters['config']
        if path.split(os.sep)[0] == 'Savu':
            path = tu.get_test_data_path(path.split('/test_data/data')[1])
        return path
    
    def get_dummyhdf_path(self):
        return tu.get_test_data_path('i18_test_data.nxs')
            