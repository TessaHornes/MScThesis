import os
import itertools
from multiprocessing import freeze_support

import pandas as pd
import numpy as np
import os
import sys
from multiprocessing import freeze_support

_conda_scripts = os.path.join(os.path.dirname(sys.executable), 'Scripts')
if os.path.isdir(_conda_scripts) and _conda_scripts not in os.environ.get('PATH', ''):
    os.environ['PATH'] = _conda_scripts + os.pathsep + os.environ.get('PATH', '')

from DFNMeshFiles.mesh.FractureProcessing.mesh_raw_fractures import mesh_raw_fractures

# Define parameters and settings 
paramA_values = ['ORmin', 'ORmax']
paramB_values = ['SDun', 'SDpl']
paramC_values = ['LDmin', 'LDmax']
paramD_values = ['APmin', 'APmax']
 
param_combinations = list(itertools.product(
    paramA_values, paramB_values, paramC_values, paramD_values
))
 
# paramA: orientation 
paramA_lookup = {
    'ORmin': {#'a1': {'kappa': 54.23, 'loc': 1.54}, 
           'a2': {'kappa': 26.10, 'loc': 0.66},
           'a3': {'kappa': 49.35, 'loc': 2.64}, 
           'a4': {'kappa': 37.46, 'loc': 0.73}},
    'ORmax': {#'a1': {'kappa': 34.44, 'loc': 1.52}, 
           'a2': {'kappa': 16.90, 'loc': 0.67},
           'a3': {'kappa': 15.66, 'loc': 2.61}, 
           'a4': {'kappa': 11.78, 'loc': 0.79}},
}
 
# paramB: spatial distribution 
paramB_lookup = {
    'SDun': {'distB': 'Uniform', #'b1': {'max distance': 2000}, 
           'b2': {'max distance': 1000}, 'b3': {'max distance': 1000}, 'b4': {'max distance': 1000}},
    'SDpl': {'distB': 'Power-law',
           # 'b1': {'alpha': 0.32, 'min distance': 2.0, 'max distance': 1000},  
           'b2': {'alpha': 0.21, 'min distance': 2.0, 'max distance': 1000},   
           'b3': {'alpha': 0.18, 'min distance': 2.0, 'max distance': 1000}, 
           'b4': {'alpha': 0.20, 'min distance': 2.0, 'max distance': 1000}},
}
 
# paramC: length distribution 
paramC_lookup = {
    'LDmin': {'distC': 'Exponential', 'inputC': {'lambda':0.008, 'Lmin':25, 'Lmax':680.09}},
    'LDmax': {'distC': 'Exponential', 'inputC': {'lambda':0.006, 'Lmin':25, 'Lmax':944.32}},
}
 
# paramD: aperture 
paramD_lookup = {
    'APmin': {'methodD': 'constant', 'inputD': {'aperture': 0.0001}},   
    'APmax': {'methodD': 'constant', 'inputD': {'aperture': 0.005}},
}

# Copy the simulation loop from the DFN+Mesh.py file and set the right parameters 
for paramA, paramB, paramC, paramD in param_combinations:
 
    Simulation_name = paramA + paramB + paramC + paramD
    DFN_name = Simulation_name

    generateDFN   = True
 
    a = paramA_lookup[paramA]
    b = paramB_lookup[paramB]
    c = paramC_lookup[paramC]
    d = paramD_lookup[paramD]

    apertureCalculationParameters = {
        'method': d['methodD'],
        **d['inputD'],   
    } 

    # set_1 = {
    #     'I': 0.80,
    #     'fractureLengthPDF': c['distC'],
    #     'fractureLengthPDFParams': c['inputC'],
    #     'spatialDistributionPDF': b['distB'],
    #     'spatialDistributionPDFParams': b['b1'],
    #     'orientationDistributionPDF': 'Von-Mises',
    #     'orientationDistributionPDFParams': a['a1'],   
    #     'bufferZone': {'method': 'constant', 'constant': 2.0},
    # }

    set_2 = {
        'I': 0.10,
        'fractureLengthPDF': c['distC'],
        'fractureLengthPDFParams': c['inputC'],
        'spatialDistributionPDF': b['distB'],
        'spatialDistributionPDFParams': b['b2'],
        'orientationDistributionPDF': 'Von-Mises',
        'orientationDistributionPDFParams': a['a2'],    
        'bufferZone': {'method': 'constant', 'constant': 2.0},
    }

    set_3 = {
        'I': 0.08,
        'fractureLengthPDF': c['distC'],
        'fractureLengthPDFParams': c['inputC'],
        'spatialDistributionPDF': b['distB'],
        'spatialDistributionPDFParams': b['b3'],
        'orientationDistributionPDF': 'Von-Mises',
        'orientationDistributionPDFParams': a['a3'],    
        'bufferZone': {'method': 'constant', 'constant': 2.0},
    }

    set_4 = {
        'I': 0.07,
        'fractureLengthPDF': c['distC'],
        'fractureLengthPDFParams': c['inputC'],
        'spatialDistributionPDF': b['distB'],
        'spatialDistributionPDFParams': b['b4'],
        'orientationDistributionPDF': 'Von-Mises',
        'orientationDistributionPDFParams': a['a4'],    
        'bufferZone': {'method': 'constant', 'constant': 2.0},
    }


    dfn_sets          = [set_2, set_3, set_4]
    domainLengthX     = 1000   # m
    domainLengthY     = 1000   # m
    numOfRealizations = 1
    Simulation_name = paramA + paramB + paramC + paramD
    DFN_name = Simulation_name

    problem_type = 'fracture'   # 'fracture' or 'lineSource'
    char_len_list = [16]   # small (fine), medium, large (coarse), options are 16, 32, 64, takes an array 

    def main():
        # ── Stage 1: DFN generation ────────────────────────────────────────────────
        if problem_type == 'fracture':
            DFN_directory = 'DFNs/' + DFN_name + '/Text'

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

    if __name__ == "__main__":
        freeze_support()
        main()