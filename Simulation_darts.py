# Section of the Python code where we import all dependencies on third party Python modules/libaries or our own
# libraries (exposed C++ code to Python, i.e. darts.engines && darts.physics)
import os
import numpy as np
import pandas as pd
from Model_darts import Model
from darts.engines import redirect_darts_output
#import shutil
from datetime import datetime
#from darts.tools.plot_darts import plot_temp_darts
#import pickle
from darts.input.input_data import InputData

def run_simulation(idata : InputData, platform : str ='cpu'):
    print('Running simulation for case', idata.geom['case_name'])

    output_directory = 'sol_' + idata.geom['case_name']

    os.makedirs(output_directory, exist_ok=True)

    redirect_darts_output(os.path.join(output_directory, 'simulation.log'))

    m = Model(idata)

    m.init(verbose = True, platform=platform)
    m.set_output(output_folder = output_directory)

    # Specify some other time-related properties (NOTE: all time parameters are in [days])
    size_report_step = 365  # Size of the reporting step
    num_report_steps = 30   # Number of reporting steps (see above)

    output_properties_main = m.physics.vars  # only main variables
    output_properties_with_temperature = output_properties_main + ['temperature']

    timesteps, property_array = m.output.output_properties(output_properties=output_properties_with_temperature,
                                                           ts_idx=0, engine=True)

    # add custom arrays to property_array: fracture index and fracture aperture to be saved to vtk files
    n_fracs = m.reservoir.discretizer.frac_cells_tot
    #frac_index = np.arange(n_fracs).reshape((1, n_fracs))
    if np.isscalar(m.reservoir.frac_aper):
        frac_aper = np.full((1, n_fracs), m.reservoir.frac_aper)
    else:
        frac_aper = np.asarray(m.reservoir.frac_aper).reshape(1, n_fracs)
    custom_arrays = {'frac_aperture': frac_aper} #'frac_index': frac_index
    if n_fracs > 0:
        property_array.update(custom_arrays)

    m.output.output_to_vtk(output_data=[timesteps, property_array], ith_step=0, output_directory=output_directory)

    # m.output.save_data_to_h5(kind = 'reservoir')
    ###m.output.output_to_vtk(ith_step=0, output_directory=output_directory)

    sim_time = 0.
    m.print_range(sim_time, part='cells')
    m.print_range(sim_time, part='fracs')

    # Run over all reporting time-steps:
    for ith_step in range(num_report_steps):
        m.run(size_report_step)
        timesteps, property_array = m.output.output_properties(output_properties=output_properties_with_temperature,
                                                                   ts_idx=ith_step+1, engine=True)
        m.output.output_to_vtk(output_data=[timesteps, property_array], ith_step=ith_step+1, output_directory=output_directory)

        sim_time += size_report_step
        m.print_range(sim_time, part='cells')
        m.print_range(sim_time, part='fracs')

    m.print_timers()
    m.print_stat()

    return m

if __name__ == "__main__":

    t1 = datetime.now()
    print(t1)

    input_data = set_input_data('case_1')
    run_simulation(input_data)

    t2 = datetime.now()
    print((t2 - t1).total_seconds())
