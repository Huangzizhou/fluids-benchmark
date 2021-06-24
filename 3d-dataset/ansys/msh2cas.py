import os
import subprocess
import tempfile
import argparse

def generate_jou(mesh):
    with tempfile.NamedTemporaryFile(suffix=".cas",delete=False) as tmp_json:
        with open(tmp_json.name, 'w') as f:
            f.write("file read-case "+mesh+"\n")
            f.write("mesh check\n")
            f.write("file write-case "+mesh[:-4]+".cas yes\n")
            f.write("exit\n")
    
    return tmp_json.name


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Solver Type.')
    parser.add_argument("--dir", "-d", type=str, default="", help="")
    parser.add_argument("--file", "-f", type=str, default="", help="")
    args = parser.parse_args()

    if args.dir != "":
        for root, _, files in os.walk(args.folder):
            # msh to cas
            for file in files:
                if file.find(".msh") != -1 and not os.path.exists(os.path.join(root, file[:-3]+'cas')):
                    jou = generate_jou(os.path.join(root, file))
                    subprocess.run(["/scratch/work/public/apps/prince/run-prince-apps.sh", 
                                "/share/apps/ansys/19.0/v190/fluent/bin/fluent", "3ddp", "-g", "-i", jou, "-t0"])
                    try:
                        os.system("rm cleanup*")
                    except:
                        print("\nNothing to remove!\n")
                    os.remove(jou)
    elif args.file != "":
        if args.file.find(".msh") != -1 and not os.path.exists(args.file[:-3]+'cas'):
            jou = generate_jou(args.file)
            subprocess.run(["/scratch/work/public/apps/prince/run-prince-apps.sh", 
                        "/share/apps/ansys/19.0/v190/fluent/bin/fluent", "3ddp", "-g", "-i", jou, "-t0"])
            try:
                os.system("rm cleanup*")
            except:
                print("\nNothing to remove!\n")
            os.remove(jou)