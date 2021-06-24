import os
import json
import subprocess
import tempfile
import argparse

def read_json(path):
    with open(path,'r') as f:
        json_data = json.load(f)

    if json_data == None:
        return None
    if json_data["formulation"] == "OperatorSplitting":
        if json_data["args"]["particle"] == True:
            solver = "flip"
        else:
            solver = "split"
    else:
        solver = "fem"

    mesh = json_data["args"]["mesh"].split("/")
    for word in mesh:
        if word.find('.msh') != -1:
            mesh = word.split(".")[0]
            break
    # mesh = json_data["args"]["mesh"]
    
    return [solver, mesh, json_data["params"]["viscosity"], 
            json_data["err_l2"], json_data["time_solving"],
            json_data["mesh_size"]]


def solve(mesh, h, solver, n_ref=0, CFL=0.05, viscosity=1e-2, tend=0.1):
    orders = {"split": [1, 1], "flip": [1, 1], "fem": [2, 1]}
    formulations = {"split": "OperatorSplitting", "flip": "OperatorSplitting", "fem": "NavierStokes"}
    polyfem_exe = "/scratch/zh1476/fluid/polyfem/build/PolyFEM_bin"
    
    output_path = os.path.join('./logs', solver + "_" + mesh.split('.')[0] + "_" + str(n_ref) + ".json")

    if os.path.exists(output_path):
        return
    
    with open("run.json", 'r') as f:
        json_data = json.load(f)

    json_data["output"] = output_path
    json_data["tend"] = tend
    json_data["problem_params"]["viscosity"] = viscosity
    json_data["params"]["viscosity"] = viscosity
    json_data["mesh"] = os.path.join("/scratch/zh1476/msh2d_0", mesh)
    json_data["n_refs"] = n_ref
    json_data["time_steps"] = int(tend / h / CFL * 2**n_ref)
    json_data["particle"] = solver == "flip"
    json_data["discr_order"] = orders[solver][0]
    json_data["pressure_discr_order"] = orders[solver][1]
    json_data["tensor_formulation"] = formulations[solver]

    with tempfile.NamedTemporaryFile(suffix=".json",delete=False) as tmp_json:
        with open(tmp_json.name, 'w') as f:
            f.write(json.dumps(json_data, indent=4))
        tempFile = tmp_json.name
        args = [polyfem_exe,
                '--json', tmp_json.name,
                '--cmd']
        subprocess.run(args)
    os.remove(tempFile)

    # data = read_json(output_path)
    # os.remove(output_path)
    # if data == None:
    #     return
    # data = ','.join([str(e) for e in data]) + '\n'
    # with open(solver + "_ref" + str(n_ref) + ".csv", 'a') as f:
    #     f.write(data)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Solver Type.')
    parser.add_argument("--solver", "-s", type=str, default="fem", help="fem,split,flip")
    parser.add_argument("--ref", "-r", type=int, default=0, help=" ")
    parser.add_argument("--num", "-n", type=int, default=0, help="0,1,2,3")

    args = parser.parse_args()
    start = args.num * 50
    end = (args.num+1) * 50 - 1
    idx = -1
    with open(os.path.join("/home/zh1476/fluid/fluid2d/h.csv"), 'r') as file_:
        lines = file_.readlines()[1:]
        for line in lines:
            idx = idx + 1
            if idx < start or idx > end:
                continue
            line = line[:-1].split(',')
            solve(line[0], float(line[1]), args.solver, n_ref=args.ref)
