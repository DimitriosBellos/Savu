'''
This tests the functions required by dawn. If these test break, the dawn integration will certainly fail.
'''

import unittest


class DawnCompatibleTest(unittest.TestCase):
    
    def test_populate_plugins(self):
        from savu.plugins import utils as pu
        pu.populate_plugins()

    def test_dawn_plugins_found(self):
        from savu.plugins import utils as pu
        pu.populate_plugins()
        self.assertGreater(len(pu.dawn_plugins), 0)
   
    def test_dawn_plugin_params_found(self):
        from savu.plugins import utils as pu
        pu.populate_plugins()
        self.assertTrue(isinstance(pu.dawn_plugin_params[pu.dawn_plugins.keys()[0]], dict))
  
    def test_load_plugin(self):
        from savu.plugins import utils as pu
        pu.populate_plugins()
        from savu.plugins.utils import dawn_plugins
        plugin_path = pu.dawn_plugins[dawn_plugins.keys()[0]]['path2plugin'].split('.py')[0]
        inst = pu.load_plugin(plugin_path)
        sl = inst.__dict__['slice_list']
        exp = inst.__dict__['exp']
        
    

if __name__=='__main__':
    unittest.main()
