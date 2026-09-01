from Input_dartsmesh import input_data_mesh
from main_gen_mesh import generate_mesh
from Simulation_darts import run_simulation
import os

import numpy as np

# List of all simulations
simulation_names = ['Test1'] 

# Define path to mesh and aperture data
base_dir = os.path.dirname(os.path.abspath(__file__))

# Loop through the list of simulations 
for sim_name in simulation_names:

    # Load correct fracture data 
    fractext_path = os.path.join(
        base_dir, 'DFNs', sim_name, 'fractureCoordinates', '001fractureCoordinates.txt'
    )

    apertext_path = os.path.join(
        base_dir, 'DFNs', sim_name, 'aperture', '001aperture.txt'
    )

    # Load mesh and aperture data in input data
    Input_data = input_data_mesh(case_name=sim_name, fractext=fractext_path, apertxt=apertext_path, domainLengthX=2000, domainLengthY=2000, height=100)

    # Create mesh 
    generate_mesh (Input_data)

    # Run simulation 
    run_simulation(Input_data, platform='cpu')