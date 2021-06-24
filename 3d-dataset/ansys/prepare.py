import os
import subprocess
import tempfile
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Solver Type.')
    # parser.add_argument("--ref", "-r", type=int, default=0, help="0,1,2,3")
    parser.add_argument("--destination", "-d", type=str, default="/scratch/zh1476/3d-dataset-ansys")

    args = parser.parse_args()
    CFL = 0.1
    tend = 0.05
    visc = 1e-2

    # if not os.path.exists(args.destination):
        # os.system("mkdir -p " + args.destination)

    mesh_list = []
    steps_list = []
    dt_list = []
    with open("/home/zh1476/fluid/fluid3d/h-tetwild-1.csv",'r') as f:
        lines = f.readlines()[1:]
        for line in lines:
            line = line[:-1].split(',')
            h = float(line[1])
            mesh_list.append(line[0] + '.cas')
            steps_list.append(int(tend / h / CFL))
            dt_list.append(tend / steps_list[-1])

    for mesh, steps, dt in zip(mesh_list, steps_list, dt_list):
        workdir = os.path.join(args.destination, mesh[:-4])
        # if os.path.exists(workdir):
        #     os.system("rm -r " + workdir)
        # os.system("mkdir -p " + workdir)

        os.system("cp *.c " + workdir)
        os.system("cp " + os.path.join('/scratch/zh1476/ansys3d_1', mesh) + " " + os.path.join(workdir, "run.cas"))

        with open(os.path.join(workdir, 'run.jou'), 'w') as f:
            f.write("file read-case run.cas\n")
            f.write("define b-c zone-type defaultfaces velocity-inlet\n")
            f.write("define user-defined compiled-functions compile , , vx-bc.c vy-bc.c vz-bc.c init.c , ,\n")
            f.write("define user-defined compiled-functions load ,\n")

            f.write("define materials change-create air , yes , 1 no no yes , "+repr(visc)+" no no no\n")

            f.write("define models unsteady-2nd-order yes\n")
            f.write("solve set p-v-coup 24\n")

            f.write("define b-c set velocity-inlet , , v-s no yes direc-0 yes yes , x_velocity::libudf direc-1 yes yes , y_velocity::libudf direc-2 yes yes , z_velocity::libudf q\n")
            f.write("define user-defined function-hooks init init::libudf \"\" \n")

            f.write("file auto-save data-frequency "+str(steps)+" root-name tmp\n")
            f.write("solve init init yes yes\n")
            f.write("solve set time-step "+repr(dt)+"\n")

            f.write("solve monitors res con-cri 1e-6 1e-6 1e-6 1e-6\n")

            f.write("solve dual-time-iterate "+str(steps)+" 400\n")
            f.write("parallel timer usage\n")
            f.write("report/system/proc-stats\n")
            f.write("exit yes\n")
        print(mesh)

        # with open(os.path.join(workdir, 'trans.jou'), 'w') as f:
        #     f.write("file read-case tmp-1.cas\n")
        #     for root, _, files in os.walk(workdir):
        #         for file in files:
        #             if file[-4:] == '.dat':
        #                 f.write("file read-data "+os.path.join(root, file)+"\n")
        #                 print(os.path.join(root, file))
        #                 break
        #     f.write("file export ensight-gold "+workdir+"/step_1 pressure q no , , , no ok\n")
        #     f.write("exit yes\n")