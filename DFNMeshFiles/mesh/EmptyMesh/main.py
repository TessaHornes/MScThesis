import numpy as np
from multiprocessing import freeze_support
from .emptyMesh import EmptyMesh
from math import pi
import os

def main():
    # File names and directories:
    output_dir = '01MeshFile'
    margin= np.sqrt(pi*2000*2000)
    # Input parameters for cleaning procedure
    char_len_list=[100]
    for char_len in char_len_list:
        #char_len = char_len  # characteristic length for cleaning and mesh generation [m]
        filename_base = 'Mesh05Eli'+ str(char_len)

        EmptyMesh(char_len, output_dir=output_dir, filename_base=filename_base, box_data=None, margin=margin, height_res=40,
                  char_len_boundary=None)

if __name__ == "__main__":
    freeze_support()
    main()
