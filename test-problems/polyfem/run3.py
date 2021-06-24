import os, json, subprocess, tempfile, argparse, time
import numpy as np
import mesh as me

# tunnel, visc=1e-3, tend=6  , base_step=150 (quad)
# tunnel, visc=1e-3, tend=6  , base_step=300 (tri)

tend_dict = {"cavity": 2, "tgv": 0.1, "tgv_tet": 0.1, "tunnel": 6, "corner": 8, "airfoil": 4, "Lshape": 6}
visc_dict = {"cavity": 1e-1, "tgv": 1e-2, "tgv_tet": 1e-2, "tunnel": 1e-3, "corner": 1e-3, "airfoil": 2e-4, "Lshape": 2e-4}
base_step_dict = {"cavity": 100, "tgv": 5, "tgv_tet": 5, "tunnel": 300, "corner": 160, "airfoil": 800, "Lshape": 300}
base_h_dict = {"tgv": 0.2, "tgv_tet": 0.2}
skip_dict = {"cavity": 2, "tgv": 5, "tgv_tet": 5, "tunnel": 2, "corner": 2, "airfoil": 8, "Lshape": 4}

work_dir = "/scratch/zh1476/fluid/model-problems"
polyfem_exe = "/scratch/zh1476/fluid/polyfem/build/PolyFEM_bin"
orders = {"split": [1, 1], "flip": [1, 1], "fem": [2, 1]}
formulations = {"split": "OperatorSplitting", "flip": "OperatorSplitting", "fem": "NavierStokes"}
problems = {"cavity": "DrivenCavitySmooth", "tgv": "TaylorGreenVortex", "tgv_tet": "TaylorGreenVortex", "tunnel": "FlowWithObstacle", "corner": "CornerFlow", "airfoil": "Airfoil", "Lshape": "Lshape"}
mesh_path = {"corner": "corner_", "corner_tri": "corner_tri_", "airfoil": "airfoil", "tgv": "cube", "tgv_tet": "cube_tet", "cavity": "cube", "tunnel": "tunnel3", "Lshape": "Lshape"}


def solve(mesh, problem, tend, steps, time_dependent=True, solver="fem", viscosity=1e-3, n_ref=0, skip_frame=1, linear_solver="Pardiso", output="."):
    if output != "":
        if not os.path.exists(output):
            os.mkdir(output)
        os.chdir(output)
    else:
        return

    with open("/home/zh1476/fluid/model-problems/polyfem/run.json", 'r') as f:
        json_data = json.load(f)

    json_data["problem"] = problem
    if problem == "FlowWithObstacle" or problem == "CornerFlow" or problem == "Lshape":
        json_data["has_neumann"] = True
    else:
        json_data["has_neumann"] = False

    json_data["save_time_sequence"] = True
    json_data["mesh"] = mesh
    json_data["output"] = "output.json"
    json_data["problem_params"]["viscosity"] = viscosity
    json_data["params"]["viscosity"] = viscosity
    json_data["n_refs"] = n_ref
    json_data["discr_order"] = orders[solver][0]
    json_data["pressure_discr_order"] = orders[solver][1]
    json_data["tensor_formulation"] = formulations[solver]
    json_data["solver_type"] = linear_solver
    if linear_solver == "SaddlePointSolver" and solver != "fem":
        return
    json_data["rhs_solver_type"] = "Hypre"
    json_data["problem_params"]["time_dependent"] = time_dependent
    if time_dependent:
        json_data["time_steps"] = steps
        json_data["skip_frame"] = skip_frame
        json_data["particle"] = solver == "flip"
        json_data["tend"] = tend
    else:
        json_data["export"]["paraview"] = problem+"_"+solver+"_"+str(n_ref)+".vtu"

    with tempfile.NamedTemporaryFile(suffix=".json",delete=False) as tmp_json:
        with open(tmp_json.name, 'w') as f:
            f.write(json.dumps(json_data, indent=4))
        tempFile = tmp_json.name
        args = [polyfem_exe,
                '--json', tmp_json.name,
                '--cmd']
        subprocess.run(args)

    os.chdir(work_dir)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Solver Type.')
    parser.add_argument("ref", type=int, help="0,1,2")
    parser.add_argument("--solver", "-s", type=str, default="fem", help="fem,split,flip")
    parser.add_argument("--transient", "-t", type=int, default=1, help="")
    parser.add_argument("--problem", "-p", type=str, default="tgv", help="tgv,cavity,corner,tunnel,airfoil")
    parser.add_argument("--visc", "-v", type=float, default=-1)
    parser.add_argument("--stepfactor", "-f", type=int, default=1)
    parser.add_argument("--linsolver", "-l", type=str, default="Pardiso")

    args = parser.parse_args()
    
    ref = args.ref
    my_problem = args.problem
    is_transient = args.transient != 0
    
    visc = visc_dict[my_problem]
    if args.visc >= 0:
        visc = args.visc
    tend = tend_dict[my_problem]
    problem_name = problems[my_problem]

    mesh = os.path.join("/home/zh1476/fluid/model-problems/mesh", mesh_path[my_problem]+str(ref)+'.mesh')

    v, f = me.read_mesh(mesh)
    hmax, hmin = me.compute_h_3d(v, f)
    print("hmax=",hmax,"hmin=",hmin)

    factor = int(round(base_h_dict[my_problem] / hmax))
    steps = base_step_dict[my_problem] * factor * args.stepfactor
    skip = skip_dict[my_problem] * factor * args.stepfactor

    output_folder = os.path.join(work_dir, my_problem+'_3d_'+str(args.solver)+'_ref'+str(ref)+'_steps'+str(steps)+'_visc'+str(visc))
    if not is_transient:
        output_folder = output_folder + '_steady'

    solve(mesh, problem_name, tend, steps, time_dependent=is_transient, solver=args.solver, n_ref=0, 
        linear_solver=args.linsolver, skip_frame=skip, viscosity=visc, output=output_folder)
