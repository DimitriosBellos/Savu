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
.. module:: FittingTests
   :platform: Unix
   :synopsis: Testing all the fitting

.. moduleauthor:: Aaron Parsons <scientificsoftware@diamond.ac.uk>

"""

import unittest
import tempfile
from savu.test import test_utils as tu
import time as time
from savu.test.framework_tests.plugin_runner_test import \
    run_protected_plugin_runner


class FittingTest(unittest.TestCase):

    def test_simple_fit_XRF(self):
        options = {
            "transport": "hdf5",
            "process_names": "CPU0",
            "data_file": '/dls/i13/data/2015/cm12165-5/processing/AskAaron/mmbig_58905.nxs',#tu.get_test_data_path('mm.nxs'),
            "process_file": '/dls/i13/data/2015/cm12165-5/processing/AskAaron/test/simple_fit_test_XRF.nxs',#tu.get_test_process_path(
                #'simple_fit_test_XRF.nxs'),
            "out_path": tempfile.mkdtemp()
            }
        run_protected_plugin_runner(options)

#     def test_simple_fit_XRD(self):
#  
#         options = {
#             "transport": "hdf5",
#             "process_names": "CPU0",
#             "data_file": tu.get_test_data_path('mm.nxs'),
#             "process_file": tu.get_test_process_path(
#                 'simple_fit_test_XRD.nxs'),
#             "out_path": tempfile.mkdtemp()
#             }
#         run_protected_plugin_runner(options)

if __name__ == "__main__":
    unittest.main()
