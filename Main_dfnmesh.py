from Input_dfnmesh import input_data_nomesh
from Simulation_darts import run_simulation
import os

# List of all simulations
simulation_names = ['Test4'] 

# Define path to mesh 
base_dir = os.path.dirname(os.path.abspath(__file__))

# Loop through the list of simulations 
for sim_name in simulation_names:

    # Load correct mesh data 
    mesh_path = os.path.join(
        base_dir, 'DFNs', sim_name, 'Meshes', 'DFN001', 'Processed16', 'DFN001_raw_lc_16.msh'
    )

    # Load mesh and aperture data in input data
    Input_data = input_data_nomesh(case_name=sim_name, mesh_file=mesh_path)

    # Run simulation 
    run_simulation(Input_data, platform='cpu')