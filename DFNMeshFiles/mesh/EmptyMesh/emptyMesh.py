import sys

import os
import numpy as np
from .create_geo_file import create_geo_file, generate_mesh

def EmptyMesh(char_len, output_dir='', filename_base='output', box_data=None, margin=25, height_res=50, char_len_boundary=None):
    """
    Create an empty mesh with only a bounding box.
    :param char_len: minimum allowable distance between any two vertices in the domain (characteristic length) [m]
    :param output_dir: directory of the output (cleaned) fracture network and potential .geo and .msh results
    :param filename_base: base name used for all the output files
    :param box_data: coordinates of the bounding box (in order, from bottom left --> bottom right --> top right --> top left) [m]
    :param margin: margin around the fracture network, used in case no bounding box is given
    :param height_res: height of the resulting 1-layer 3D reservoir [m]
    :param char_len_mult: multiplier for mesh characteristic length
    :param char_len_boundary: characteristic mesh length on the boundary (before multiplier)
    :return: None
    """
    if char_len_boundary is None:
        char_len_boundary = char_len

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if box_data is None:
        x_min = - margin
        y_min = - margin
        x_max = + margin
        y_max = + margin
        box_data = np.array([[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]])

    # Filenames for meshing:
    filename_geo = os.path.join(output_dir, filename_base + '.geo')

    print('START creating geo-file for empty network (input for gmsh)')
    create_geo_file(filename=filename_geo, decimals=5,
                    height_res=height_res, char_len=char_len, box_data=box_data,
                    char_len_boundary=char_len_boundary)
    print('DONE creating geo-file for empty network (input for gmsh)\n')

    print('Preprocessing succesfully finished')
    print('-----------------------------------')

    geo_file = filename_geo

    msh_file = os.path.join(output_dir, filename_base + '.msh')
    generate_mesh(geo_file, msh_file)

    return 0