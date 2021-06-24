import os, argparse, sys, meshio
import numpy as np
import numpy.linalg as LA

mesh_folder = "/home/zh1476/fluid/model-problems/ansys/mesh/"

mesh_path = {"tgv_hex": "cube", "tgv_tet": "cube_tet"}

tet_h_list = [0.21128425864274755, 0.16985750046290163, 0.0849287502314555, 0.0424643751157322, 0.0424643751157322 / 2]

tend = 0.1
visc = 1e-2
base_step = 5
base_h = 0.2

def read_mesh(path):
    mesh = meshio.read(path)
    v = mesh.points
    for x in mesh.cells_dict:
        if x == "triangle" or x == "quad":
            f = mesh.cells_dict[x]
            break
    return v, f

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Solver Type.')
    parser.add_argument("--problem", "-p", type=str, default="tgv_hex")
    parser.add_argument("--ref", "-r", type=int, default=0, help="0,1,2,3")
    parser.add_argument("--visc", "-v", type=float, default=-1)
    parser.add_argument("--destination", "-d", type=str, default="/scratch/zh1476/fluid/model-problems/ansys/")
    parser.add_argument("--stepfactor", "-f", type=int, default=1)
    parser.add_argument("--residual", type=float, default=-1)

    parser.add_argument("--extra", action="store_true")
    parser.add_argument("--full-output", action="store_true")

    args = parser.parse_args()

    problem = args.problem.split("_")
    shape = problem[1]
    problem = problem[0]

    case_path = mesh_folder+mesh_path[args.problem]+str(args.ref)+'.cas'

    if shape == "hex":
        steps = base_step * 2**args.ref * args.stepfactor
    else:
        steps = int(base_step * base_h / tet_h_list[args.ref] * args.stepfactor)
    dt = tend / steps

    if args.stepfactor != 1:
        destination = os.path.join(args.destination, args.problem + "_3d_fv_ref" + str(args.ref) + '_steps' + str(steps) + "_visc" + str(visc))
    else:
        destination = os.path.join(args.destination, args.problem + "_3d_fv_ref" + str(args.ref) + "_visc" + str(visc))

    if os.path.exists(destination):
        os.system("rm -r "+ destination)
    os.system("mkdir -p " + destination)
        
    if args.stepfactor != 1:
        workdir = os.path.join(args.destination, "run-" + args.problem + "_3d_fv_ref" + str(args.ref) + '_steps' + str(steps) + "_visc" + str(visc))
    else:
        workdir = os.path.join(args.destination, "run-" + args.problem + "_3d_fv_ref" + str(args.ref) + "_visc" + str(visc))

    if os.path.exists(workdir):
        os.system("rm -r " + workdir)
    os.system("mkdir -p " + workdir)
    
    os.system("cp /home/zh1476/fluid/model-problems/ansys/bc/tgv3/*.c " + workdir)
    os.system("cp " + case_path+" " + os.path.join(workdir,"run.cas"))

    with open(workdir + "/run.jou", 'w') as f:
        f.write("file read-case run.cas\n")
        if shape == 'hex':
            f.write("define b-c zone-type defaultFaces velocity-inlet\n")
        else:
            f.write("define b-c zone-type patch0 velocity-inlet\n")
        
        # compile UDF
        f.write("define user-defined compiled-functions compile , , vx-bc.c vy-bc.c vz-bc.c init.c , ,\n")
        f.write("define user-defined compiled-functions load ,\n")

        # define visc
        f.write("define materials change-create air , yes , 1 no no yes , "+repr(visc)+" no no no\n")

        # set solver and method
        f.write("define models unsteady-2nd-order yes\n")
        f.write("solve set p-v-coup 24\n")
        
        # assign UDF
        if problem == "tgv":
            f.write("define b-c set velocity-inlet , , v-s no yes direc-0 yes yes , x_velocity::libudf direc-1 yes yes , y_velocity::libudf direc-2 yes yes , z_velocity::libudf q\n")
            f.write("define user-defined function-hooks init init::libudf \"\" \n")

        f.write("file auto-save data-frequency "+str(steps)+" root-name tmp\n")
        f.write("solve init init yes yes\n")
        f.write("solve set time-step "+repr(dt)+"\n")

        # set residual
        f.write("solve monitors res con-cri 1e-6 1e-6 1e-6 1e-6\n")

        if args.residual > 0:
            f.write("solve monitors res con-cri "+repr(args.residual)+" "+repr(args.residual)+" "+repr(args.residual)+"\n")

        f.write("solve dual-time-iterate "+str(steps)+" 100\n")
        f.write("parallel timer usage\n")
        f.write("report/system/proc-stats\n")
        f.write("exit yes\n")

    with open(workdir + "/trans.jou", 'w') as f:
        f.write("file read-case tmp-1.cas\n")
        f.write("file read-data tmp-1-"+str(steps).zfill(5)+".dat\n")
        f.write("file export ensight-gold "+destination+"/step_1 pressure q no , , , no ok\n")
        f.write("exit yes\n")

    print(workdir, file=sys.stdout)