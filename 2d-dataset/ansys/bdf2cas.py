import os
import subprocess
import tempfile
import argparse

def generate_jou(mesh, ref):
    with tempfile.NamedTemporaryFile(suffix=".cas",delete=False) as tmp_json:
        with open(tmp_json.name, 'w') as f:
            f.write("file import nas bulk /scratch/zh1476/bdf2d_"+str(ref)+"/"+mesh+".bdf\n")
            f.write("file write-case /scratch/zh1476/cas_"+str(ref)+"/"+mesh+".cas\n")
    
    return tmp_json.name


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Solver Type.')
    parser.add_argument("--num", "-n", type=int, default=0, help="0,1,2,3")
    parser.add_argument("--ref", "-r", type=int, default=1, help="0,1,2,3")

    args = parser.parse_args()

    start = args.num * 105
    end = (args.num+1) * 105 - 1
    idx = -1
    with open("../h.csv",'r') as f:
        lines = f.readlines()
        for line in lines:
            idx = idx + 1
            if idx < start or idx > end:
                continue
            line = line[:-1].split(',')
            h = float(line[2])
            mesh = line[0]
            # bdf to cas
            jou = generate_jou(mesh, args.ref)
            if not os.path.exists("/scratch/zh1476/cas_"+str(args.ref)+"/"+mesh+".cas"):
                subprocess.run(["/scratch/work/public/apps/prince/run-prince-apps.sh", 
                            "/share/apps/ansys/19.0/v190/fluent/bin/fluent", "2ddp", "-g", "-i", jou, "-t0"])
                try:
                    os.system("rm cleanup*")
                except:
                    print("\nNothing to remove!\n")
            else:
                print(mesh+" already finished!")
            os.remove(jou)
