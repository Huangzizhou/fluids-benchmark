import os, json, subprocess, tempfile, argparse, time, sys, meshio
import numpy as np
import meshio

def read_mesh(path):
    mesh = meshio.read(path)
    v = mesh.points
    for x in mesh.cells_dict:
        if x == "triangle" or x == "quad":
            f = mesh.cells_dict[x]
            break
    return v, f

def mesh_info(path):
    v, f = read_mesh(path)
    if len(f.shape) == 1:
        f = f.reshape([1,3])
    if f.shape[1] == 3:
        e = np.concatenate((f[:,0:2],f[:,1:3],f[:,np.array([2,0])]), axis=0)
    else:
        e = np.concatenate((f[:,0:2],f[:,1:3],f[:,2:4],f[:,np.array([3,0])]), axis=0)

    e = np.unique(np.sort(e, axis=1), axis=0)
    h_max = 0
    h_min = 1e5
    v_1 = v[e[:,0]]
    v_2 = v[e[:,1]]
    dist = np.sqrt(np.sum((v_1 - v_2)**2, axis=1))

    return np.amax(dist), np.amin(dist), np.sum(dist) / dist.shape[0]


# tunnel, visc=1e-3, tend=6  , base_step=150 (quad)
# tunnel, visc=1e-3, tend=6  , base_step=300 (tri)

tend_dict = {"cavity": 2,
             "tgv": 0.1,
             "tunnel": 6,
             "corner": 8,
             "airfoil": 4, 
             "drag": 1,
             "Lshape": 6}
visc_dict = {"cavity": 1e-1,
             "tgv": 1e-2,
             "tunnel": 1e-3,
             "corner": 1e-3,
             "airfoil": 2e-4,
             "drag": 1e-2,
             "Lshape": 2e-4}

base_h_dict = {"cavity": 0.2, "cavity_tri": 0.1370218238274017 * 2, 
                  "tgv": 0.2, "tgv_tri": 0.1370218238274017 * 2,
                  "tunnel_tri": 0.0696623789964758, "tunnel_quad": 0.3532, 
                  "corner": 0.1, "corner_tri": 0.14124897280413626, 
                  "airfoil": 0.13742698504789894 * 2, 
                  "drag": 0.08459278843282078,
                  "Lshape": 0.1, "Lshape_tri": 0.0353115981775414 * 4}

base_step_dict = {"cavity": 100, "cavity_tri": 100, 
                  "tgv": 10, "tgv_tri": 10,
                  "tunnel_tri": 300, "tunnel_quad":150, 
                  "corner": 160, "corner_tri": 160, 
                  "airfoil": 400, 
                  "drag": 500,
                  "Lshape": 300, "Lshape_tri": 300}
base_skip_dict = {"cavity": 2, "cavity_tri": 2,
             "tgv": 10, "tgv_tri": 10,
             "tunnel_tri": 2, "tunnel_quad": 1, 
             "corner": 2, "corner_tri": 2, 
             "airfoil": 4, 
             "drag": 100,
             "Lshape": 4, "Lshape_tri": 4}

mesh_dir = "/home/zh1476/fluid/model-problems/mesh"
polyfem_exe = "/scratch/zh1476/fluid/polyfem/build/PolyFEM_bin"

orders = {"split": [1, 1], "flip": [1, 1], "fem": [2, 1]}
formulations = {"split": "OperatorSplitting", "flip": "OperatorSplitting", "fem": "NavierStokes"}
problems = {"cavity2": "DrivenCavitySmooth", "cavity_tri2": "DrivenCavitySmooth", 
            "cavity1": "DrivenCavityC0", "cavity_tri1": "DrivenCavityC0", 
            "cavity0": "DrivenCavity", "cavity_tri0": "DrivenCavity", 
            "tgv": "TaylorGreenVortex", "tgv_tri": "TaylorGreenVortex",
            "tunnel_tri": "FlowWithObstacle", "tunnel_quad": "FlowWithObstacle", 
            "corner": "CornerFlow", "corner_tri": "CornerFlow", 
            "airfoil": "Airfoil", 
            "drag": "StokesLaw",
            "Lshape": "Lshape", "Lshape_tri": "Lshape"}
mesh_path = {"corner": "corner_", "corner_tri": "corner_tri_", 
            "airfoil": "airfoil", 
            "drag": "drag",
            "tgv": "quad", "tgv_tri": "tri",
            "cavity": "quad", "cavity_tri": "tri", 
            "tunnel_tri": "tunnel_tri_", "tunnel_quad": "tunnel_quad_", 
            "Lshape": "Lshape", "Lshape_tri": "Lshape_tri"}

def solve(mesh, resolution, problem, tend, steps, time_dependent=True, solver="fem", order=2, viscosity=1e-3, n_ref=0, skip_frame=1, linear_solver="Pardiso", output="."):
    if not os.path.exists(output):
        os.system('mkdir -p '+output)
    os.chdir(output)

    with open("/home/zh1476/fluid/model-problems/polyfem/run.json", 'r') as f:
        json_data = json.load(f)

    json_data["problem"] = problem
    if problem == "FlowWithObstacle" or problem == "CornerFlow" or problem == "Lshape":
        json_data["has_neumann"] = True

    if resolution > 0:
        json_data["uniform_grid"] = {"dim": 2, "X": 1, "Y": 1, "Xn": resolution, "Yn": resolution}
    else:
        json_data["mesh"] = mesh

    # if os.path.exists(os.path.join(output,"output.json")):
        # return

    json_data["output"] = "output.json"
    json_data["problem_params"]["viscosity"] = viscosity
    json_data["params"]["viscosity"] = viscosity
    json_data["n_refs"] = n_ref
    if solver != "fem":
        json_data["discr_order"] = orders[solver][0]
        json_data["pressure_discr_order"] = orders[solver][1]
    else:
        json_data["discr_order"] = order
        json_data["pressure_discr_order"] = order - 1
        json_data["BDF_order"] = order + 1
        # if order > 2:
        json_data["vismesh_rel_area"] = 1e-6
    json_data["tensor_formulation"] = formulations[solver]
    json_data["solver_type"] = linear_solver
    json_data["rhs_solver_type"] = 'Hypre'
    json_data["problem_params"]["time_dependent"] = time_dependent
    if time_dependent:
        json_data["time_steps"] = steps
        json_data["skip_frame"] = skip_frame
        json_data["particle"] = solver == "flip"
        json_data["tend"] = tend
    else:
        json_data["export"]["paraview"] = problem+"_"+solver+"_"+str(n_ref)+".vtu"

    # print(json.dumps(json_data, sort_keys=True, indent=4))
    run_json = os.path.join(output, 'run.json')

    with open(run_json, 'w') as f:
        f.write(json.dumps(json_data, indent=4))

    print(output, file=sys.stdout)

    # args = [polyfem_exe,
    #         '--json', run_json,
    #         '--cmd']
    # subprocess.run(args)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Solver Type.')
    parser.add_argument("ref", type=int, help="number of refinement")
    parser.add_argument("--order", "-o", type=int, default=2, help="order of velocity in fem")
    parser.add_argument("--resolution", type=int, default=0, help="mesh resolution")
    parser.add_argument("--solver", "-s", type=str, default="fem", help="fem,split,flip")
    parser.add_argument("--problem", "-p", type=str, default="tgv", help="tgv,cavity,corner,tunnel,airfoil")
    parser.add_argument("--cavity", "-c", type=int, default=0, help="0: cavity, 1: C0 cavity, 2: smooth cavity")
    parser.add_argument("--visc", "-v", type=float, default=-1, help="viscosity")
    parser.add_argument("--stepfactor", "-f", type=int, default=1, help="extra refinement in time")
    parser.add_argument("--destination", "-d", type=str, default="/scratch/zh1476/fluid/model-problems/results")

    parser.add_argument("--extra", action="store_true")
    parser.add_argument("--full-output", action="store_true")
    parser.add_argument("--steady", action="store_true")
    
    parser.set_defaults(plotquad=False)

    args = parser.parse_args()
    
    if args.problem == "tgv":
        ref = 0
        extra_ref = args.ref
    else:
        ref = args.ref
        extra_ref = 0

    visc = visc_dict[args.problem.split('_')[0]]
    if args.visc >= 0:
        visc = args.visc
    tend = tend_dict[args.problem.split('_')[0]]
    if args.problem.find('cavity') != -1:
        problem_name = problems[args.problem+str(args.cavity)]
    else:
        problem_name = problems[args.problem]

    if args.extra:
        mesh = os.path.join(mesh_dir, mesh_path[args.problem]+'extra_'+str(ref)+'.msh')
        v, f = read_mesh(mesh)
        h, h_min, h_avg = mesh_info(mesh)
        skip = int(round((base_h_dict[args.problem] / h) * base_skip_dict[args.problem]))
        steps = int(skip / base_skip_dict[args.problem] * base_step_dict[args.problem])
    else:
        mesh = os.path.join(mesh_dir, mesh_path[args.problem]+str(ref)+'.msh')
        steps = base_step_dict[args.problem] * 2**args.ref
        skip = base_skip_dict[args.problem] * 2**args.ref

    output_folder = os.path.join(args.destination, args.problem.split('_')[0])
    if args.problem.find('cavity') != -1:
        output_folder += str(args.cavity)
    if args.resolution == 0:
        output_folder = os.path.join(output_folder, args.problem+'_2d_'+str(args.solver)+'_ref'+str(args.ref)+'_visc'+str(visc))
    else:
        output_folder = os.path.join(output_folder, args.problem+'_2d_'+str(args.solver)+'_N'+str(args.resolution)+'_visc'+str(visc))
        h = 1. / args.resolution
        skip = int(round((base_h_dict[args.problem] / h) * base_skip_dict[args.problem]))
        steps = int(skip / base_skip_dict[args.problem] * base_step_dict[args.problem])

    if args.stepfactor != 1:
        steps *= args.stepfactor
        skip *= args.stepfactor
        output_folder += '_steps'+str(args.stepfactor)

    if args.order != 2 and args.solver == "fem":
        output_folder += '_order'+str(args.order)
    
    if args.extra:
        output_folder += '_extra'
        
    if args.steady:
        output_folder = output_folder + '_steady'

    if args.full_output:
        skip = 1

    solve(mesh, args.resolution, problem_name, tend, steps, time_dependent=(not args.steady), solver=args.solver, order=args.order, n_ref=extra_ref, 
    linear_solver='Pardiso', skip_frame=skip, viscosity=visc, output=output_folder)
