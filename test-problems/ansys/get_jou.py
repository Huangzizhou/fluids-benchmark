import os, argparse, sys, meshio
import numpy as np
import numpy.linalg as LA

mesh_folder = "/home/zh1476/fluid/model-problems/ansys/mesh/"

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
skip_dict = {"cavity": 2, "cavity_tri": 2,
             "tgv": 10, "tgv_tri": 10,
             "tunnel_tri": 2, "tunnel_quad": 1, 
             "corner": 2, "corner_tri": 2, 
             "airfoil": 4, 
             "drag": 100,
             "Lshape": 4, "Lshape_tri": 4}
mesh_path = {"corner": "corner_", "corner_tri": "corner_tri_", 
            "airfoil": "airfoil", 
            "drag": "drag",
            "tgv": "tgv_quad", "tgv_tri": "tgv_tri",
            "cavity": "cavity_quad", "cavity_tri": "cavity_tri",
            "tunnel_tri": "tunnel_tri_", "tunnel_quad": "tunnel_quad_", 
            "Lshape": "Lshape", "Lshape_tri": "Lshape_tri"}

def compute_h(v, f):
    if f.shape[1] == 3:
        e = np.concatenate( (f[:, [0, 1]], f[:, [1, 2]], f[:, [0, 2]]) , axis=0 )
    else:
        e = np.concatenate( (f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 3]], f[:, [3, 0]]) , axis=0 )
    edge = v[e[:,0], :] - v[e[:,1], :]
    dist = LA.norm(edge, axis=1)
    return np.amax(dist)

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
    parser.add_argument("--problem", "-p", type=str, default="tunnel_quad")
    parser.add_argument("--cavity", "-c", type=int, default=0, help="0: cavity, 1: C0 cavity, 2: smooth cavity")
    parser.add_argument("--ref", "-r", type=int, default=0, help="0,1,2,3")
    parser.add_argument("--visc", "-v", type=float, default=-1)
    parser.add_argument("--destination", "-d", type=str, default="/scratch/zh1476/fluid/model-problems/results/")
    parser.add_argument("--stepfactor", "-f", type=int, default=1)
    parser.add_argument("--residual", type=float, default=-1)

    parser.add_argument("--extra", action="store_true")
    parser.add_argument("--full-output", action="store_true")

    args = parser.parse_args()

    problem = args.problem.split("_")
    if len(problem) > 1:
        shape = problem[1]
    else:
        shape = "quad"
    problem = problem[0]

    if args.extra:
        case_path = mesh_folder+mesh_path[args.problem]+'extra_'+str(args.ref)+'.cas'
    else:
        case_path = mesh_folder+mesh_path[args.problem]+str(args.ref)+'.cas'

    if args.extra:
        v, f = read_mesh(os.path.join("/home/zh1476/fluid/model-problems/ansys/msh22",mesh_path[args.problem]+'extra_'+str(args.ref)+'.msh'))
        h = compute_h(v, f)
        del v, f
        d_step = int(round((base_h_dict[args.problem] / h) * skip_dict[args.problem]))
        steps = int(d_step / skip_dict[args.problem] * base_step_dict[args.problem])
    else:
        steps = base_step_dict[args.problem] * 2**args.ref
        d_step = skip_dict[args.problem] * 2**args.ref


    steps *= args.stepfactor
    d_step *= args.stepfactor

    if args.full_output:
        d_step = 1
    dt = tend_dict[problem] / steps

    visc = visc_dict[problem]
    if args.visc >= 0:
        visc = args.visc

    destination = os.path.join(args.destination, problem)
    if problem == 'cavity':
        destination += str(args.cavity)
    if args.stepfactor != 1:
        destination = os.path.join(destination, args.problem + "_2d_fv_ref" + str(args.ref) + '_steps' + str(args.stepfactor) + "_visc" + str(visc))
    else:
        destination = os.path.join(destination, args.problem + "_2d_fv_ref" + str(args.ref) + "_visc" + str(visc))
    if args.extra:
        destination += '_extra'

    if os.path.exists(destination):
        os.system("rm -r "+ destination)
    os.system("mkdir -p " + destination)
        
    workdir = destination + '-tmp'

    if os.path.exists(workdir):
        os.system("rm -r " + workdir)
    os.system("mkdir -p " + workdir)
    
    os.system("cp " + os.path.join("./bc",problem,"*.c") + " " + workdir)
    os.system("cp " + case_path+" " + os.path.join(workdir,"run.cas"))

    with open(workdir + "/run.jou", 'w') as f:
        f.write("file read-case run.cas\n")
        
        # compile UDF
        if problem == "tunnel" or problem == "airfoil" or problem == "Lshape":
            f.write("define user-defined compiled-functions compile , , vx-bc.c , ,\n")
        elif problem == "cavity":
            f.write("define user-defined compiled-functions compile , , vx"+str(args.cavity)+".c , ,\n")
        elif problem == "corner":
            f.write("define user-defined compiled-functions compile , , vy-bc.c , ,\n")
        elif problem == "tgv":
            f.write("define user-defined compiled-functions compile , , vx-bc.c vy-bc.c init.c , ,\n")

        if not (problem == "drag"):
            f.write("define user-defined compiled-functions load ,\n")

        # define visc
        f.write("define materials change-create air , yes , 1 no no yes , "+repr(visc)+" no no no\n")

        # set solver and method
        f.write("define models unsteady-2nd-order yes\n")
        f.write("solve set p-v-coup 24\n")
        
        # assign UDF
        if problem == "tgv":
            f.write("define b-c set velocity-inlet , , v-s no yes direc-0 yes yes , x_velocity::libudf direc-1 yes yes , y_velocity::libudf q\n")
            f.write("define user-defined function-hooks init init::libudf \"\" \n")
        elif problem == "cavity" or problem == "tunnel" or problem == "Lshape" or problem == "airfoil":
            f.write("define b-c set velocity-inlet , , v-s no yes direc-0 yes yes , x_velocity::libudf q\n")
        elif problem == "corner":
            f.write("define b-c set velocity-inlet , , v-s no yes direc-1 yes yes , y_velocity::libudf q\n")
        elif problem == "drag":
            f.write("define b-c set velocity-inlet , , v-s no yes direc-1 no 1 q\n")

        f.write("file auto-save data-frequency "+str(d_step)+" root-name tmp\n")
        f.write("solve init init yes yes\n")
        f.write("solve set time-step "+repr(dt)+"\n")

        # set residual
        f.write("solve monitors res con-cri 1e-6 1e-6 1e-6\n")

        if args.residual > 0:
            f.write("solve monitors res con-cri "+repr(args.residual)+" "+repr(args.residual)+" "+repr(args.residual)+"\n")

        f.write("solve dual-time-iterate "+str(steps)+" 200\n")
        f.write("parallel timer usage\n")
        f.write("report/system/proc-stats\n")
        f.write("exit yes\n")

    with open(os.path.join(workdir, "trans.jou"), 'w') as f:
        f.write("file read-case tmp-1.cas\n")
        for i in range(0, int(steps / d_step)):
            idx = d_step * (i + 1)
            f.write("file read-data tmp-1-"+str(idx).zfill(5)+".dat\n")
            f.write("file export ensight-gold "+destination+"/step_"+str(i+1)+" pressure q no , , , no ok\n")
        
        f.write("exit yes\n")

    print(workdir, file=sys.stdout)