import subprocess
import numpy as np
def create_geo_file(filename, decimals, height_res, char_len, reservoirWidth, char_len_boundary):
    """
    Creates geo file which serves as input to gmsh for a geometry without any fractures
    :param filename: name of the resulting geo-file
    :param decimals: data is rounded off to this number of decimals
    :param height_res: height of the resulting 1-layer 3D reservoir
    :param char_len: characteristic length of the resulting mesh
    :param box_data: coordinates of the box-data around the fracture network
    :param char_len_boundary: characteristic length of mesh elements at the boundary
    :return:
    """

    x_min = - np.round(reservoirWidth/2)
    y_min = - np.round(reservoirWidth/2)
    x_max = + np.round(reservoirWidth/2)
    y_max = + np.round(reservoirWidth/2)
    box_data = np.array([[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]])
    f = open(filename, "w+")

    f.write('// Geo file which meshes the input mesh from act_frac_sys.\n')
    f.write('// Change mesh-elements size by varying "lc" below.\n\n')

    f.write('lc = {:1.3f};\n'.format(char_len))
    f.write('lc_box = {:1.3f};\n'.format(char_len_boundary))
    f.write('height_res = {:4.3f};\n\n'.format(height_res))

    # Write the box_data (box around fracture network in which we embed the fractures)
    f.write('// Extra points for boundary of domain:\n')
    for ii in range(4):
        # For every corner of the box:
        f.write('Point({:d}) = {{{:8.5f}, {:8.5f}, 0, lc_box}};\n'.format(ii + 1, box_data[ii, 0], box_data[ii, 1]))

    # Add four lines for each side of the box:
    f.write('\n// Extra lines for boundary of domain:\n')
    for ii in range(4):
        f.write('Line({:d}) = {{{:d}, {:d}}};\n'.format(ii + 1, ii + 1, ii + 2 if ii < 3 else 1))

    # Make Curve loop for the boundary:
    f.write('\n// Create line loop for boundary surface:\n')
    f.write('Curve Loop(1) = {1, 2, 3, 4};\n')
    f.write('Plane Surface(1) = {1};\n\n')

    # Extrude model to pseuo-3D:
    f.write('\n// Extrude surface with embedded features\n')
    f.write('Extrude {0, 0, height_res}{ Surface {1}; Layers{1}; Recombine;}\n')
    f.write('Physical Volume("matrix", 9991) = {1};\n')

    # Create mesh and perform coherency check:
    f.write('Mesh 3;  // Generate 3D mesh\n')
    f.write('Coherence Mesh;  // Remove duplicate entities\n')
    f.write('Mesh.MshFileVersion = 2.1;\n')
    f.close()
    return 0

def create_geo_file_buffer(filename, decimals, height_res, char_len, reservoirWidth, char_len_boundary, bufferSize=1000):
    """
    Creates geo file which serves as input to gmsh for a geometry without any fractures
    :param filename: name of the resulting geo-file
    :param decimals: data is rounded off to this number of decimals
    :param height_res: height of the resulting 1-layer 3D reservoir
    :param char_len: characteristic length of the resulting mesh
    :param reservoirWidth: width of the reservoir
    :param char_len_boundary: characteristic length of mesh elements at the boundary
    :param bufferSize: size of the buffer zone around the reservoir
    :return:
    """
    x_min = - np.round((reservoirWidth + 2 * bufferSize) / 2)
    y_min = - np.round((reservoirWidth + 2 * bufferSize) / 2)
    x_max = + np.round((reservoirWidth + 2 * bufferSize) / 2)
    y_max = + np.round((reservoirWidth + 2 * bufferSize) / 2)
    box_data = np.array([[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]])

    f = open(filename, "w+")

    f.write('// Geo file which meshes the input mesh from act_frac_sys.\n')
    f.write('// Change mesh-elements size by varying "lc" below.\n\n')

    f.write('lc = {:1.3f};\n'.format(char_len))
    f.write('lc_box = {:1.3f};\n'.format(char_len_boundary))
    f.write('height_res = {:4.3f};\n\n'.format(height_res))

    # Write the box_data (box around fracture network in which we embed the fractures)
    f.write('// Extra points for boundary of domain:\n')
    for ii in range(4):
        # For every corner of the box:
        f.write('Point({:d}) = {{{:8.5f}, {:8.5f}, 0, lc_box}};\n'.format(ii + 1, box_data[ii, 0], box_data[ii, 1]))

    # Add a point in the center of the box
    f.write('Point(5) = {{{:8.5f}, {:8.5f}, 0, lc}};\n'.format((x_min + x_max) / 2, (y_min + y_max) / 2))

    # Add four lines for each side of the box:
    f.write('\n// Extra lines for boundary of domain:\n')
    for ii in range(4):
        f.write('Line({:d}) = {{{:d}, {:d}}};\n'.format(ii + 1, ii + 1, ii + 2 if ii < 3 else 1))

    # Make Curve loop for the boundary:
    f.write('\n// Create line loop for boundary surface:\n')
    f.write('Curve Loop(1) = {1, 2, 3, 4};\n')
    f.write('Plane Surface(1) = {1};\n\n')

    # Define a Field that varies the mesh size from char_len in the center of the reservoir to char_len_boundary at the boundary
    f.write('Field[1] = Attractor;\n')
    f.write('Field[1].NodesList = {5};\n')  # Use the center point as the attractor
    f.write('Field[2] = Threshold;\n')
    f.write('Field[2].IField = 1;\n')
    f.write('Field[2].LcMin = {:1.3f};\n'.format(char_len))
    f.write('Field[2].LcMax = {:1.3f};\n'.format(char_len_boundary))
    f.write('Field[2].DistMin = 0;\n')
    f.write('Field[2].DistMax = {:1.3f};\n'.format(bufferSize))
    f.write('Background Field = 2;\n')

    # Extrude model to pseuo-3D:
    f.write('\n// Extrude surface with embedded features\n')
    f.write('Extrude {0, 0, height_res}{ Surface {1}; Layers{1}; Recombine;}\n')
    f.write('Physical Volume("matrix", 9991) = {1};\n')

    # Create mesh and perform coherency check:
    f.write('Mesh 3;  // Generate 3D mesh\n')
    f.write('Coherence Mesh;  // Remove duplicate entities\n')
    f.write('Mesh.MshFileVersion = 2.1;\n')
    f.close()
    return 0




