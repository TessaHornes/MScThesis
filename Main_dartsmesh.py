from Input_dartsmesh import input_data_mesh
from main_gen_mesh import generate_mesh
from NEW_main_simulation import run_simulation
import os

import numpy as np
import meshio

# List of all simulations
simulation_names = ['ORmaxSDplLDmaxAPmax'] 

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

    # Add fratures to make wells end up in fractures 
    with open(fractext_path, 'a') as f:
        f.write('190 210 210 190\n790 810 810 790\n')

    with open(apertext_path, 'a') as f:
        f.write('0.005\n0.005\n')

    # Load mesh and aperture data in input data
    Input_data = input_data_mesh(case_name=sim_name, fractext=fractext_path, apertxt=apertext_path, domainLengthX=1000, domainLengthY=1000, height=50)

    # Create mesh 
    generate_mesh (Input_data)

    # Import updated aperture file 
    apertext_updated = os.path.join(
        base_dir,
        f'meshes_{sim_name}',
        f'{sim_name}_mergefac_0.86_clean_lc_16_aperture.txt'
    )

    # Load updated aperture data (one value per fracture)
    aper = np.loadtxt(apertext_updated) 

    # Expand to one value per fracture cell, in the order DARTS reads the mesh
    mesh_path = os.path.join(base_dir, f'meshes_{sim_name}', f'{sim_name}_mergefac_0.86_clean_lc_16.msh')
    mesh = meshio.read(mesh_path)

    frac_aper = []
    for tags in mesh.cell_data["gmsh:physical"]:
        for t in tags:
            if 90000 <= t < 90000 + len(aper):
                frac_aper.append(aper[t - 90000])
    frac_aper = np.array(frac_aper)

    Input_data.geom['frac_aper'] = frac_aper

    # Run simulation 
    run_simulation(Input_data, platform='cpu')