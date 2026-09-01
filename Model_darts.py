from darts.engines import value_vector, sim_params, well_control_iface
from darts.nonlinear_solvers import NewtonSolver, ChopSpec
from darts.models.cicd_model import CICDModel
from darts.models.darts_model import DartsModel
from darts.physics.base.physics import PhysicsBase
from darts.physics.iapws_physics import IAPWSPhysics
from darts.physics.base.property_container import PropertyContainer
from dartsflash.mixtures import DARTSFlash, CompData, EoS, IAPWS
from darts.physics.properties.eos_properties import EoSDensity, EoSEnthalpy
from darts.physics.properties.basic import ConstFunc, PhaseRelPerm
from darts.physics.properties.viscosity import MaoDuan2009
from darts.reservoirs.unstruct_reservoir import UnstructReservoir
from darts.engines import ms_well
import os
import numpy as np
import meshio
from darts.input.input_data import InputData

def fmt(x):
    return '{:.3}'.format(x)

# Here the Model class is defined (child-class from DartsModel) in which most of the data and properties for the
# simulation are defined, e.g. for the reservoir/physics/sim_parameters/etc.
class Model(DartsModel):
    def __init__(self, idata : InputData):
        # base class constructor
        super().__init__()
        self.idata = idata
        input_data = idata.geom

        # Measure time spend on reading/initialization
        self.timer.node["initialization"].start()

        self.bound_cond = idata.geom['well_loc_type']

        # Some permeability input data for the simulation
        poro = idata.rock.porosity  # Matrix porosity [-]
        self.inj_well_coords = idata.geom['inj_well_coords']
        self.prod_well_coords = idata.geom['prod_well_coords']

        if input_data['mesh_filename'] is None:
            fname = '_' + idata.geom['mesh_prefix'] + '_' + str(idata.geom['char_len']) + '.msh'
            mesh_file = os.path.join('meshes_' + idata.geom['case_name'], idata.geom['case_name'] + fname)
        else:
            mesh_file = input_data['mesh_filename']

        # Gmsh can subdivide one physical fracture segment into several cells.
        # Map each segment aperture to all cells carrying that segment's tag.
        msh = meshio.read(mesh_file)
        c = msh.cell_data_dict['gmsh:physical']
        frac_tag_start = idata.geom['frac_tag_start']
        frac_geom_type = 'quad'
        if idata.geom['mesh_type'] == '3D' and 'triangle' in c:
            frac_geom_type = 'triangle'

        frac_aper = idata.geom['frac_aper']
        if not np.isscalar(frac_aper):
            segment_apertures = np.asarray(frac_aper).reshape(-1)
            cell_tags = c[frac_geom_type]
            fracture_cell_tags = cell_tags[cell_tags >= frac_tag_start]
            segment_indices = fracture_cell_tags - frac_tag_start
            if segment_indices.size and segment_indices.max() >= segment_apertures.size:
                raise ValueError(
                    f'Mesh references fracture segment {segment_indices.max()}, but only '
                    f'{segment_apertures.size} segment apertures were supplied.'
                )
            frac_aper = segment_apertures[segment_indices]

        if idata.rock.perm_file is not None: # set heterogeneous permeability from a file
            permx = self.get_perm_unstr_from_struct_grid(idata.rock.perm_file, self.input_data)
            permy = permx
            permz = permx * 0.1
        else: # set homogeneous permeability
            permx = idata.rock.permx
            permy = idata.rock.permy
            permz = idata.rock.permz

        # initialize reservoir
        self.reservoir = UnstructReservoir(timer=self.timer, mesh_file=mesh_file,
                                           permx=permx, permy=permy, permz=permz,
                                           poro=poro,
                                           rcond=idata.rock.conductivity,
                                           hcap=idata.rock.heat_capacity,
                                           frac_aper=frac_aper)

        # parameters for fracture aperture computation depending on principal stresses
        if 'Sh_max' in idata.stress:
            self.reservoir.sh_max = idata.stress['Sh_max']
            self.reservoir.sh_min = idata.stress['Sh_min']
            self.reservoir.sh_max_azimuth = idata.stress['SHmax_azimuth']
            self.reservoir.sigma_c = idata.stress['sigma_c']

        # 'MeshIt':  # 3D mesh from meshIt software, the tags are hardcoded below according to MeshIt conventions
        matrix_tags = idata.geom['matrix_tags']
        bnd_xy_tags = [3, 4, 5, 6]
        bnd_tags = [1, 2] + bnd_xy_tags

        n_fractures = (np.unique(c[frac_geom_type]) >= frac_tag_start).sum()

        self.reservoir.physical_tags['matrix'] = matrix_tags
        self.reservoir.physical_tags['fracture'] = [frac_tag_start + i for i in range(n_fractures)]
        self.reservoir.physical_tags['boundary'] = bnd_tags  # order: Z- (bottom); Z+ (top) ; Y-; X+; Y+; X-

        # discretize
        self.reservoir.init_reservoir(verbose=True)

        # set boundary volume XY
        if idata.geom['bondary_volume_xy'] > 0:
            import datetime
            t1 = datetime.datetime.now()
            boundary_cells = []
            boundary_cells += self.reservoir.discretizer.find_cells(bnd_xy_tags, 'face')
            t2 = datetime.datetime.now()
            print('Time to find boundary cells:', (t2 - t1).total_seconds(), 'sec.')

            boundary_cells = np.array(boundary_cells) + self.reservoir.discretizer.frac_cells_tot
            bnd_vol = idata.geom['bondary_volume_xy']
            self.reservoir.discretizer.volume_all_cells[boundary_cells] = bnd_vol  # for vtk output
            np.array(self.reservoir.mesh.volume, copy=False)[boundary_cells] = bnd_vol

        # initialize physics
        self.cell_property = ['pressure', 'enthalpy', 'temperature']

        self.set_iapws_physics(p_step=self.idata.obl.p_step,
                               p_origin=self.idata.obl.p_origin,
                               t_step=self.idata.obl.t_step,
                               t_origin=self.idata.obl.t_origin,
                               is_ph=False)

        # End timer for model initialization:
        self.timer.node["initialization"].stop()

    def set_solver(self):
        """Configure nonlinear and linear solvers after platform initialization."""
        self.set_sim_params(first_ts=1e-6, mult_ts=1.5, max_ts=60)
        super().set_solver()
        self.nonlinear_solver = NewtonSolver(
            tolerance=1e-4,
            max_iterations=20,
            chop=ChopSpec(mode='local', factor=1),
        )
        self.linear_solver.spec.tolerance = 1e-5
        self.linear_solver.spec.max_iterations = 40

    def set_iapws_physics(self, p_step, p_origin, t_step, t_origin, is_ph: bool, cache=False):
        """Drop-in replacement for legacy Geothermal(...) using compositional + IAPWS PT-flash.
        Single-component water; phases are vapor ('V') and liquid ('L').
        State spec is PT so engine.X layout is [P, T, ...] and the OBL grid is sampled on (P, T).
        The adaptive interpolator is defined by per-axis step + origin and extends on demand.
        """
        components = ["H2O"]
        phases = ['V', 'L']
        zero = 1e-12
        comp_data = CompData(components=components, setprops=True)

        # state_spec=PH -> OBL axes are [pressure, enthalpy]; state_spec=PT -> [pressure, temperature]
        self.physics = IAPWSPhysics(
            phases, self.timer,
            state_spec=PhysicsBase.StateSpecification.PH if is_ph else PhysicsBase.StateSpecification.PT,
            axes_step=[p_step, t_step],
            axes_origin=[p_origin, t_origin],
            cache=cache,
        )

        mixture = IAPWS(iapws_ideal=True, ice_phase=False)
        if is_ph:
            # PHFlash -> PXFlash(ENTHALPY) under the hood (dartsflash wrapper). Bound the
            # PXFlash temperature root-finding to the IAPWS liquid range: the default
            # t_min=100 K lets the solver sample far below the ice point, where IAPWS-95
            # density bisection diverges ("LIQUID MINIMUM BISECTION not converged").
            mixture.init_flash(flash_type=DARTSFlash.FlashType.PHFlash,
                                t_min=273.15, t_max=575., t_init=350.)
        else:
            mixture.init_flash(flash_type=DARTSFlash.FlashType.PTFlash)
        self.physics.set_mixture(mixture)

        """ Set property container and define properties """
        pc = PropertyContainer(phases_name=phases, components_name=components,
                               Mw=comp_data.Mw, eps_z=zero)
        self.physics.add_property_region(pc)

        pc.flash_ev = self.physics.get_flash_ev()

        pc.density_ev = {
            'V': EoSDensity(eos=mixture.eos["IAPWS"], root_flag=EoS.RootFlag.MAX),
            'L': EoSDensity(eos=mixture.eos["IAPWS"], root_flag=EoS.RootFlag.MIN),
        }
        pc.viscosity_ev = {
            'V': ConstFunc(0.01),                  # cP, steam
            'L': MaoDuan2009(components),          # cP, liquid water (pressure/temperature-dependent)
        }
        pc.enthalpy_ev = {
            'V': self.physics.get_enthalpy_ev_from_flash(phase_idx=0),
            'L': self.physics.get_enthalpy_ev_from_flash(phase_idx=1),
        }
        pc.rel_perm_ev = {
            'V': PhaseRelPerm("gas", swc=0.0),
            'L': PhaseRelPerm("oil", swc=0.0),
        }
        pc.conductivity_ev = {
            'V': ConstFunc(0.0),
            'L': ConstFunc(172.8),                 # kJ/m/day/K, matches geothermal default
        }
        # output_props exposes derived T (K) via the property interpolator
        pc.output_props = {'temperature': lambda: pc.temperature}

        return pc

    def print_range(self, time, part='cells'):
        depth = np.array(self.reservoir.mesh.depth, copy=True)
        start, end = self.get_mat_frac_range(part)
        if start == end:  # no fractures
            return
        D = depth[start:end]
        P = self.get_pressure(part)
        T = self.get_temperature(part)
        suf = '(MAT)'  # matrix cells
        if part == 'full':
            suf = '(MAT+FRAC)'  # matrix+fracture cells
        elif part == 'fracs':
            suf = '(FRAC)'  # matrix+fracture cells
        print('Time', fmt(time/365.25), ' years; ', time, 'days, '
              'D_range:', fmt(D.min()), '-', fmt(D.max()), 'm; ',
              'P_range:', fmt(P.min()), '-', fmt(P.max()), 'bars; ',
              'T_range:', fmt(T.min()), '-', fmt(T.max()), 'K', suf)

    def set_initial_conditions(self):
        if self.idata.initial.type == 'gradient':
            # Specify reference depth, values and gradients to construct depth table in super().set_initial_conditions()
            input_depth = [0., np.amax(self.reservoir.mesh.depth)]
            input_distribution = {'pressure': [1., 1. + input_depth[1] * self.idata.initial.pressure_gradient / 1000],
                                  'temperature': [293.15, 293.15 + input_depth[
                                      1] * self.idata.initial.temperature_gradient / 1000]
                                  }
            return self.physics.set_initial_conditions_from_depth_table(self.reservoir.mesh,
                                                                        input_distribution=input_distribution,
                                                                        input_depth=input_depth)
        elif self.idata.initial.type == 'uniform':
            input_distribution = {'pressure': self.idata.initial.initial_pressure,
                                  'temperature': self.idata.initial.initial_temperature}
            return self.physics.set_initial_conditions_from_array(self.reservoir.mesh,
                                                                  input_distribution=input_distribution)

    def well_is_inj(self, wname : str):  # determine well control by its name
        return "I" in wname

    def set_well_controls(self):
        wctrl = self.idata.well_data.controls
        inj_rate = wctrl.inj_rate
        prod_rate = wctrl.prod_rate

        pressure = self.get_pressure('full')
        temperature = self.get_temperature('full')

        for i, w in enumerate(self.reservoir.wells):
            well_top_perf_idx = self.well_perf_loc[w.name][0]
            if self.well_is_inj(w.name):
                if inj_rate is None:  # BHP control
                    inj_bhp = pressure[well_top_perf_idx] + wctrl.delta_p_inj
                    inj_temp = temperature[well_top_perf_idx] - wctrl.delta_temp
                    self.physics.set_well_controls(wctrl=w.control, control_type=well_control_iface.BHP,
                                                   is_inj=True, target=inj_bhp, inj_composition=[],
                                                   inj_temp=inj_temp)
                else:
                    inj_temp = 300.
                    # Rate Control
                    self.physics.set_well_controls(wctrl=w.control,
                                                   control_type=well_control_iface.VOLUMETRIC_RATE,
                                                   is_inj=True, target=inj_rate, phase_name='L',
                                                   inj_composition=[], inj_temp=inj_temp)
                    # BHP Constraint
                    self.physics.set_well_controls(wctrl=w.constraint, control_type=well_control_iface.BHP,
                                                   is_inj=True, target=wctrl.inj_bhp_constraint,
                                                   inj_composition=[], inj_temp=inj_temp)
            else:
                if prod_rate is None:  # BHP control
                    prod_bhp = pressure[well_top_perf_idx] - wctrl.delta_p_prod
                    self.physics.set_well_controls(wctrl=w.control, control_type=well_control_iface.BHP,
                                                   is_inj=False, target=prod_bhp)
                else:
                    # Rate Control
                    self.physics.set_well_controls(wctrl=w.control,
                                                   control_type=well_control_iface.VOLUMETRIC_RATE,
                                                   is_inj=False, target=-np.abs(prod_rate), phase_name='L')
                    # BHP Constraint
                    self.physics.set_well_controls(wctrl=w.constraint, control_type=well_control_iface.BHP,
                                                   is_inj=False, target=wctrl.prod_bhp_constraint)

        return 0

    def get_mat_frac_range(self, part):
        # order: fracture, matrix
        if part == 'full':
            start = 0
            end = self.reservoir.discretizer.frac_cells_tot + self.reservoir.discretizer.mat_cells_tot
        elif part == 'cells':
            start = self.reservoir.discretizer.frac_cells_tot
            end = self.reservoir.discretizer.frac_cells_tot + self.reservoir.discretizer.mat_cells_tot
        elif part == 'fracs':
            start = 0
            end = self.reservoir.discretizer.frac_cells_tot
        return [start, end]

    def get_pressure(self, part='cells'):
        nvars = 2
        start, end = self.get_mat_frac_range(part)
        Xn = np.array(self.physics.engine.X, copy=True)
        P = Xn[nvars*start:nvars*end:nvars]
        return P

    def get_temperature(self, part='cells'):
        # State spec is PT, so engine.X layout is [P, T, P, T, ...] (n_vars=2).
        # Temperature is the second variable; just take stride-2 starting at offset 1.
        nvars = 2
        start, end = self.get_mat_frac_range(part)
        Xn = np.array(self.physics.engine.X, copy=True)
        T = Xn[nvars*start + 1:nvars*end:nvars]
        return T

    def calc_well_loc(self):
        #TODO use idx = self.reservoir.find_cell_index(wc)
        # Store number of control volumes (NOTE: in case of fractures, this includes both matrix and fractures):
        self.nb = self.reservoir.discretizer.volume_all_cells.size
        self.num_frac = self.reservoir.discretizer.frac_cells_tot
        self.num_mat = self.reservoir.discretizer.mat_cells_tot
        if self.bound_cond == 'wells_in_frac':
            offset = 0
            left_int = 0
            right_int = self.num_frac
        elif self.bound_cond == 'wells_in_mat':
            offset = self.num_frac
            left_int = self.num_frac
            right_int = self.num_frac + self.num_mat
        elif self.bound_cond == 'wells_in_nearest_cell':
            offset = 0
            left_int = 0
            right_int = self.num_frac + self.num_mat
        else:
            raise('error: wrong self.bound_cond')

        # Find closest mesh elements to well traj points, assuming it is vertical
        step_z_perf = 1.  # [m] should be smaller that cell dz
        self.well_perf_loc = dict()
        well_coords = self.idata.geom['well_coords']
        centroids_3d = self.reservoir.discretizer.centroids_all_cells[left_int:right_int]
        for wname in well_coords.keys():  # process each well
            coord = well_coords[wname]
            # find mesh cells which
            z1, z2 = coord[2], coord[3]
            z_points = np.arange(z1, z2, step_z_perf)
            if z_points.size == 0: # z1==z2, just one perf
                z_points = np.array([z1])
            ids = set()
            for z in z_points:  # find a cell with the closest center
                cell = ((centroids_3d[:, 0] - coord[0]) ** 2 + (centroids_3d[:, 1] - coord[1]) ** 2 + (
                            centroids_3d[:, 2] - z) ** 2).argmin()
                ids.add(int(cell))
            ids_1 = list(ids)

            # sort perforations by depth
            perf_depths = centroids_3d[ids_1, 2]
            perf_sorted_indices = np.argsort(perf_depths)
            ids_1 = np.array(ids_1)[perf_sorted_indices]

            # store into a dictionary
            self.well_perf_loc[wname] = ids_1


    def set_wells(self, well_index=100):
        """
        Class method which initializes the wells (adding wells and their perforations to the reservoir)
        :return:
        """
        self.calc_well_loc()

        for wname in self.well_perf_loc.keys():
            self.reservoir.add_well(wname)
            for k in range(self.well_perf_loc[wname].size):
                self.reservoir.add_perforation(wname, res_cell_idx=self.well_perf_loc[wname][k],
                                               well_index=well_index, well_indexD=0, verbose=True)


    def get_perm_unstr_from_struct_grid(self, perm_file, input_data):
        # Set non-uniform permeability
        if perm_file != None:
            [xx, yy, perm_rect_2d] = np.load(perm_file, allow_pickle=True)
            perm_rect_1d = perm_rect_2d.flatten()  # TODO: check XY-order
            cntr = self.discretizer.centroids_all_cells[self.discretizer.fracture_cell_count:]
            z_middle = input_data['z_top'] + input_data['height_res'] * 0.5  # middle depth of the reservoir
            rect_grid = np.vstack((xx.flatten(), yy.flatten(), np.zeros(xx.flatten().shape) + z_middle)).transpose()
            perm_unstr = np.zeros(cntr.size)
            c_idx = 0
            for c in cntr:
                dist_to_point = np.linalg.norm(c - rect_grid, axis=1)
                cell_id = np.argmin(dist_to_point)
                perm_from_rect = perm_rect_1d.flatten()[cell_id]
                perm_unstr[c_idx] = perm_from_rect
                c_idx += 1
            return perm_unstr
