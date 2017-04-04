'''
run_savu
This is a refactor of the code that used to be contained in dawn.
It's used to mock up a runner for individual savu plugins from a python shell.
It is currently very early in development and will be subject to massive refactor in the future.
'''
from savu.data.experiment_collection import Experiment
from savu.data.meta_data import MetaData
from savu.plugins.utils import load_plugin
import os, sys
import numpy as np
from copy import deepcopy as copy
import time

def runSavu(path2plugin, params, metaOnly, inputs, persistence):
    '''
    path2plugin  - is the path to the user script that should be run
    params - are the savu parameters
    metaOnly - a boolean for whether the data is kept in metadata or is passed as data
    inputs      - is a dictionary of input objects 
    '''
    t1 = time.time()
    sys_path_0_lock = persistence['sys_path_0_lock']
    sys_path_0_set = persistence['sys_path_0_set']
    plugin_object = persistence['plugin_object']
    axis_labels = persistence['axis_labels']
    axis_values = persistence['axis_values']
    string_key = persistence['string_key']
    parameters = persistence['parameters']
    aux = persistence['aux']
    sys_path_0_lock.acquire()
    try:
        result = copy(inputs)

        scriptDir = os.path.dirname(path2plugin)
        sys_path_0 = sys.path[0]
        if sys_path_0_set and scriptDir != sys_path_0:
            raise Exception("runSavu attempted to change sys.path[0] in a way that "
                            "could cause a race condition. Current sys.path[0] is {!r}, "
                            "trying to set to {!r}".format(sys_path_0, scriptDir))
        else:
            sys.path[0] = scriptDir
            sys_path_0_set = True
        
        if not plugin_object:
            parameters = {}
                # slight repack here
            for key in params.keys():
                val = params[key]["value"]
                if type(val)==type(''):
                    val = val.replace('\n','').strip()
                parameters[key] = val
            print "initialising the object"
            plugin_object, axis_labels, axis_values = process_init(path2plugin, inputs, parameters)
#             print "axis labels",axis_labels
#             print "axis_values", axis_values
#             print plugin_object
            chkstring =  [any(isinstance(ix, str) for ix in axis_values[label]) for label in axis_labels]
            if any(chkstring): # are any axis values strings we instead make this an aux out
                metaOnly = True
#                 print "AXIS LABELS"+str(axis_values)
                string_key = axis_labels[chkstring.index(True)]
                aux = dict.fromkeys(axis_values[string_key])
                print aux.keys()
            else:
                string_key = axis_labels[0]# will it always be the first one?
            if not metaOnly:
                if len(axis_labels) == 1:
                    result['xaxis']=axis_values[axis_labels[0]]
                    result['xaxis_title']=axis_labels[0]
                if len(axis_labels) == 2:
                    print "set the output axes"
                    x = axis_labels[0]
                    result['xaxis_title']=x
                    y = axis_labels[1]
                    result['yaxis_title']=y
                    result['yaxis']=axis_values[y]
                    result['xaxis']=axis_values[x]
        else:
            pass
    finally:
        sys_path_0_lock.release()

    if plugin_object.get_max_frames()>1: # we need to get round this since we are frame independant
        data = np.expand_dims(inputs['data'], 0)
    else:
        data = inputs['data']
        
    if not metaOnly: 
        result['data'] = plugin_object.filter_frames([data])[0]
        
    elif metaOnly:
        print "metadata only operation"
        result['data'] = inputs['data']
#         print type(result['data'])
        out_array = plugin_object.filter_frames([data])
        print out_array
        k=0
#         print aux.keys()
        for key in aux.keys():
            print "assigning the dict in aux"
#             print out_array
            aux[key]=np.array([out_array[k]])# wow really
            k+=1
        result['auxiliary'] = aux
    print "ran the python part fine"
    t2 = time.time()
    print "time to runSavu = "+str((t2-t1))
    return result



def process_init(path2plugin, inputs, parameters):
    parameters['in_datasets'] = [inputs['dataset_name']]
    parameters['out_datasets'] = [inputs['dataset_name']]
    plugin = load_plugin(path2plugin.strip('.py'))
    plugin.exp = setup_exp_and_data(inputs, inputs['data'], plugin)
    plugin._set_parameters(parameters)
    plugin._set_plugin_datasets()
    plugin.setup()
    axis_labels = plugin.get_out_datasets()[0].get_axis_label_keys()
    foo = [type(ix) for ix in axis_labels]
    print "axis label types", foo
    axis_labels.remove('idx') # get the labels
    axis_values = {}
    plugin._clean_up() # this copies the metadata!
    for label in axis_labels:
        axis_values[label] = plugin.get_out_datasets()[0].meta_data.get_meta_data(label)
#         print label, axis_values[label].shape
    plugin.base_pre_process()
    plugin.pre_process()
    print "I went here"
    return plugin, axis_labels, axis_values

def setup_exp_and_data(inputs, data, plugin):
    exp = DawnExperiment(get_options())
    data_obj = exp.create_data_object('in_data', inputs['dataset_name'])
    data_obj.data = None
    if len(inputs['data_dimensions'])==1:
#         print data.shape
        if inputs['xaxis_title'] is None or inputs['xaxis_title'].isspace():
            inputs['xaxis_title']='x'
            inputs['xaxis'] = np.arange(inputs['data'].shape[0])
        data_obj.set_axis_labels('idx.units', inputs['xaxis_title'] + '.units')
        data_obj.meta_data.set_meta_data('idx', np.array([1]))
        data_obj.meta_data.set_meta_data(str(inputs['xaxis_title']), inputs['xaxis'])
        data_obj.add_pattern(plugin.get_plugin_pattern(), core_dir=(1,), slice_dir=(0, ))
        data_obj.add_pattern('SINOGRAM', core_dir=(1,), slice_dir=(0, )) # good to add these two on too
        data_obj.add_pattern('PROJECTION', core_dir=(1,), slice_dir=(0, ))
    if len(inputs['data_dimensions'])==2:
        if inputs['xaxis_title'] is None  or inputs['xaxis_title'].isspace():
            print "set x"
            inputs['xaxis_title']='x'
            inputs['xaxis'] = np.arange(inputs['data'].shape[0])
        if inputs['yaxis_title'] is None or inputs['yaxis_title'].isspace():
            print "set y"
            inputs['yaxis_title']='y'
            size_y_axis = inputs['data'].shape[1]
            inputs['yaxis'] = np.arange(size_y_axis)
        data_obj.set_axis_labels('idx.units', inputs['xaxis_title'] + '.units', inputs['yaxis_title'] + '.units')
        data_obj.meta_data.set_meta_data('idx', np.array([1]))
        data_obj.meta_data.set_meta_data(str(inputs['xaxis_title']), inputs['xaxis'])
        data_obj.meta_data.set_meta_data(str(inputs['yaxis_title']), inputs['yaxis'])
        data_obj.add_pattern(plugin.get_plugin_pattern(), core_dir=(1,2,), slice_dir=(0, ))
        data_obj.add_pattern('SINOGRAM', core_dir=(1,2,), slice_dir=(0, )) # good to add these two on too
        data_obj.add_pattern('PROJECTION', core_dir=(1,2,), slice_dir=(0, ))
    data_obj.set_shape((1, ) + data.shape) # need to add for now for slicing...
    data_obj.get_preview().set_preview([])
    return exp

class DawnExperiment(Experiment):
    def __init__(self, options):
        self.index={"in_data": {}, "out_data": {}, "mapping": {}}
        self.meta_data = MetaData(get_options())
        self.nxs_file = None

def get_options():
    options = {}
    options['transport'] = 'hdf5'
    options['process_names'] = 'CPU0'
    options['data_file'] = ''
    options['process_file'] = ''
    options['out_path'] = ''
    options['inter_path'] = ''
    options['log_path'] = ''
    options['run_type'] = ''
    options['verbose'] = 'True'
    return options




