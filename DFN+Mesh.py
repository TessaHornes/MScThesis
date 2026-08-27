import pandas as pd
import numpy as np
import os
import sys
from multiprocessing import freeze_support

_conda_scripts = os.path.join(os.path.dirname(sys.executable), 'Scripts')
if os.path.isdir(_conda_scripts) and _conda_scripts not in os.environ.get('PATH', ''):
    os.environ['PATH'] = _conda_scripts + os.pathsep + os.environ.get('PATH', '')

from DFNMeshFiles.mesh.FractureProcessing.mesh_raw_fractures import mesh_raw_fractures

# ==============================================================================
# Stage control
# ==============================================================================
generateDFN   = True  # True → generate DFN txt files with GeoDFN
buildMesh     = False   # True → run gmsh to build .msh from DFN txt files

# ==============================================================================
# DFN settings 
# ==============================================================================
DFN_name = 'Test_aper'

# apertureCalculationParameters = {
#     'method': 'constant',
#     'aperture': 0.005,   
# }

# EDIT - sublinear aperture calculations 
apertureCalculationParameters = {
    'method': 'subLinear',
    'scalingCoefficient': 5e-5,   
    'scalingExponent': 0.5,
}
# End of edit 

set_1 = {
    'I': 0.01,
    'fractureLengthPDF': 'Exponential',
    'fractureLengthPDFParams': {'lambda':0.0083, 'Lmin':5.43, 'Lmax':679},
    'spatialDistributionPDF': 'Uniform',
    'spatialDistributionPDFParams': {'max distance': 2000},
    'orientationDistributionPDF': 'Von-Mises',
    'orientationDistributionPDFParams': {'kappa': 61.42, 'loc':1.57},   
    'bufferZone': {'method': 'constant', 'constant': 2.0},
}

# set_1 = {
#     'I': 0.01,
#     'fractureLengthPDF': 'Exponential',
#     'fractureLengthPDFParams': {'lambda':0.0083, 'Lmin':5.43, 'Lmax':679},
#     'spatialDistributionPDF': 'Uniform',
#     'spatialDistributionPDFParams': {'max distance': 2000},
#     'orientationDistributionPDF': 'Von-Mises',
#     'orientationDistributionPDFParams': {'kappa': 61.42, 'loc':1.57},   
#     'bufferZone': {'method': 'constant', 'constant': 2.0},
# }

# set_2 = {
#     'I': 0.02,
#     'fractureLengthPDF': 'Exponential',
#     'fractureLengthPDFParams': {'lambda':0.0083, 'Lmin':5.43, 'Lmax':679},
#     'spatialDistributionPDF': 'Uniform',
#     'spatialDistributionPDFParams': {'max distance': 2000},
#     'orientationDistributionPDF': 'Von-Mises',
#     'orientationDistributionPDFParams': {'kappa': 30.56, 'loc':0.62},    
#     'bufferZone': {'method': 'constant', 'constant': 2.0},
# }

# set_3 = {
#     'I': 0.04,
#     'fractureLengthPDF': 'Exponential',
#     'fractureLengthPDFParams': {'lambda':0.0083, 'Lmin':5.43, 'Lmax':679},
#     'spatialDistributionPDF': 'Uniform',
#     'spatialDistributionPDFParams': {'max distance': 2000},
#     'orientationDistributionPDF': 'Von-Mises',
#     'orientationDistributionPDFParams': {'kappa': 34.37, 'loc':2.61},    #
#     'bufferZone': {'method': 'constant', 'constant': 2.0},
# }

# set_4 = {
#     'I': 0.04,
#     'fractureLengthPDF': 'Exponential',
#     'fractureLengthPDFParams': {'lambda':0.0083, 'Lmin':5.43, 'Lmax':679},
#     'spatialDistributionPDF': 'Uniform',
#     'spatialDistributionPDFParams': {'max distance': 2000},
#     'orientationDistributionPDF': 'Von-Mises',
#     'orientationDistributionPDFParams': {'kappa': 15.46, 'loc':0.77},    #
#     'bufferZone': {'method': 'constant', 'constant': 2.0},
# }

# set_test = {
#     'I': 1,
#     'fractureLengthPDF': 'Power-law',
#     'fractureLengthPDFParams': {'alpha':0.34,'Lmin': 5.43, 'Lmax':679},
#     'spatialDistributionPDF': 'Power-law',
#     'spatialDistributionPDFParams': {'alpha':0.27,'min distance': 0.75, 'max distance':2000},
#     'orientationDistributionPDF': 'Von-Mises',
#     'orientationDistributionPDFParams': {'kappa': 15.46, 'loc':0.77},   
#     'bufferZone': {'method': 'constant', 'constant': 2.0},
# }

dfn_sets          = [set_1]
domainLengthX     = 1000   # m
domainLengthY     = 1000   # m
numOfRealizations = 1

# ==============================================================================
# Simulation settings
# ==============================================================================
Simulation_name = 'Test_aper'

problem_type = 'fracture'   # 'fracture' or 'lineSource'
char_len_list = [16]   # small (fine), medium, large (coarse), options are 16, 32, 64, takes an array 


def main():
    # ── Stage 1: DFN generation ────────────────────────────────────────────────
    if problem_type == 'fracture':
        DFN_directory = 'DFNs/' + DFN_name + '/Text'

        # EDIT - add aperture path
        Aperture_directory = 'DFNs/' + DFN_name + '/aperture' 
        # End of edit 

        if generateDFN:
            from DFNMeshFiles.dfn_generator import generate_and_save
            print(f'[Stage 1] Generating DFN "{DFN_name}" with GeoDFN...')
            generate_and_save(
                dfn_name=DFN_name,
                domainLengthX=domainLengthX,
                domainLengthY=domainLengthY,
                sets=dfn_sets,
                apertureCalculationParameters=apertureCalculationParameters,
                numOfRealizations=numOfRealizations,
                base_dir='DFNs',
                savePic=True,
            )
            print('[Stage 1] DFN generation complete.')
        else:
            print(f'[Stage 1] Skipped — using existing DFN files in {DFN_directory}')

        dfn_files = [f for f in os.listdir(DFN_directory) if f.endswith('.txt')]

    else:
        dfn_files = ['lineSource']

    # ── Stage 2: mesh generation ──────────
    for dfn_file in dfn_files:
        results = {}

        for char_len in char_len_list:

            if problem_type == 'lineSource':
                outputDir = 'LineSource/' + Simulation_name
                os.makedirs(outputDir, exist_ok=True)
                meshProperties = {'charLength': char_len, 'bufferSize': 0}
                m = LineSourceModel(inputs=inputs, simulationParams=simulationParams,
                                    meshProperties=meshProperties, bound_cond=bound_cond,
                                    outputDir=outputDir)

            else:
                DFN_textName = dfn_file.split('.')[0]
                output_dir_mesh = ('DFNs/' + DFN_name + '/Meshes/' +
                                    DFN_textName + '/Processed' + str(char_len))

                # ── Stage 2: mesh building ─────────────────────────────────
                if buildMesh:
                    print(f'[Stage 2] Building mesh for {DFN_textName} (char_len={char_len})...')
                    os.makedirs(output_dir_mesh, exist_ok=True)
                    frac_data_raw = np.genfromtxt(os.path.join(DFN_directory, dfn_file))

                    # EDIT - define boundary surfaces 
                    boundary_surfaces = np.array([[0, 0], [domainLengthX, 0], [domainLengthX, domainLengthY], [0, domainLengthY]])
                    # End of edit 

                    mesh_raw_fractures(
                        frac_data_raw, char_len,
                        output_dir=output_dir_mesh,
                        filename_base=DFN_textName,
                        height_res=100, apertures_raw=None,
                        box_data=boundary_surfaces, margin=25, mesh_raw=True,
                        decimals=7, tolerance_zero=1e-10, tolerance_intersect=1e-10,
                        calc_intersections_before=True,
                        num_partition_x=4, num_partition_y=4,
                        partition_fractures_in_segms=True,
                        matrix_perm=1, char_len_mult=1,
                        char_len_boundary=None, main_algo_iters=1,
                    )

                    print('[Stage 2] Mesh building complete.')
                else:
                    print(f'[Stage 2] Skipped — using existing mesh in {output_dir_mesh}')

                mesh_name = DFN_textName + '_raw_lc_' + str(char_len) + '.msh'
                mesh_path = output_dir_mesh + '/' + mesh_name
                if not os.path.exists(mesh_path):
                    print(f'Mesh file {mesh_name} not found in {output_dir_mesh}. Skipping...')
                    continue

if __name__ == "__main__":
    freeze_support()
    main()