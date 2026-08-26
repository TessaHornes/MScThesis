from darts.input.input_data import InputData

def input_data_nomesh(case_name, mesh_file):
    idata = InputData(type_hydr='thermal', type_mech='none', init_type='gradient')
    idata.geom = dict()
    ###########################################################################################################

    idata.geom['frac_tag_start'] = 90000  
    idata.geom['frac_geom_type'] = 'quad'
    idata.geom['matrix_tags'] = [9991] 
    idata.geom['mesh_type'] = '2.5D'

    idata.geom['case_name'] = case_name
    idata.geom['mesh_filename'] = mesh_file 

    # well locations
    idata.geom['inj_well_coords'] = [[50, 50, 50]]  # X, Y, Z (only one perforation)
    idata.geom['prod_well_coords'] = [[1950, 1950, 50]]

    idata.geom['well_coords'] = dict()

    idata.geom['well_coords']['I1'] = [50., 50., 30, 60]  # X, Y, Z1, Z2
    idata.geom['well_coords']['P1'] = [1950., 1950., 30, 60]  # X, Y, Z1, Z2

    # will be passed to UnstructuredDiscretizer
    idata.geom['frac_aper'] = 1e-3  # (initial) fracture aperture [m]

    # well in the matrix cells or in the fractures
    idata.geom['well_loc_type'] = 'wells_in_nearest_cell'  # could be in the matrix or in the fracture, depending on the location
    #idata.geom['well_loc_type'] = 'wells_in_frac'  # put the well into the closest fracture
    #idata.geom['well_loc_type'] = 'wells_in_mat'  # put the well into the closest matrix cell

    # to mimic an infinite reservoir
    idata.geom['bondary_volume_xy'] = 1e+15  # [m^3]

    idata.rock.porosity = 0.089
    idata.rock.permx = 0.01  # [mD]
    idata.rock.permy = 0.01  # [mD]
    idata.rock.permz = 1e-5  # [mD]
    idata.rock.perm_file = None  # if want to read the permeability from a file

    idata.rock.compressibility = 2.3e-5  # [1/bars]
    idata.rock.compressibility_ref_p = 1  # [bars]
    idata.rock.compressibility_ref_T = 273.15  # [K]

    idata.rock.heat_capacity = 2200. # [kJ/m3/K]
    idata.rock.conductivity = 275.6  # [kJ/m/day/K]

    # Fluid properties are wired directly in Model.set_iapws_physics via compositional + IAPWS.

    # uniform initial pressure and temperature
    idata.initial.type ='uniform'
    idata.initial.initial_pressure = 147.  # bar
    idata.initial.initial_temperature = 320.15  # K

    # well controls
    class InputDataWellControls():  # an empty class - to group custom well control input data
        def __init__(self):
            pass
    idata.well_data.controls = InputDataWellControls()
    wctrl = idata.well_data.controls  #short name
    wctrl.prod_rate = None  # m3/day. if None, well will work under BHP control
    wctrl.inj_rate = None   # m3/day. if None, well will work under BHP control
    wctrl.delta_temp = 40   # bars. inj_temp = initial_temp - delta_temp
    wctrl.delta_p_inj  = 30  # bars. inj_bhp = initial_pressure + delta_p_inj
    wctrl.delta_p_prod = 30  # bars. inj_prod = initial_pressure - delta_p_prod
    wctrl.prod_bhp_constraint = 50 # bars
    wctrl.inj_bhp_constraint = 450 # bars

    # principal stress, MPa.
    # Set to None if don't want to recompute fracture apertures by initial stresses
    idata.stress = dict()
    idata.stress['Sh_min'] = None #50
    idata.stress['Sh_max'] = None # 90
    idata.stress['Sv'] = None # 120
    idata.stress['SHmax_azimuth'] = None #0  # [°] from X, counter-clockwise
    idata.stress['sigma_c'] = None #100

    # gradient
    idata.initial.reference_depth_for_pressure = 0  # [m]
    idata.initial.pressure_gradient = 100  # [bar/km]
    idata.initial.pressure_at_ref_depth = 1  # [bars]

    idata.initial.reference_depth_for_temperature = 0  # [m]
    idata.initial.temperature_gradient = 30  # [K/km]
    idata.initial.temperature_at_ref_depth = 273.15 + 10 # [K]

    idata.obl.p_step = 5.0
    idata.obl.p_origin = 0.5
    # PT flash: OBL temperature axis (K). t_origin sits at the IAPWS liquid
    # floor (273.15 K) so sampling stays above the ice region; t_step reproduces
    # the legacy ~128-point grid over [273.15, 575] K.
    idata.obl.t_step = 2.377
    idata.obl.t_origin = 273.15

    return idata