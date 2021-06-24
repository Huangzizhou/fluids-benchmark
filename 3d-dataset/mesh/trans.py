import os, argparse

parser = argparse.ArgumentParser(description='Solver Type.')
parser.add_argument("file", type=str)
args = parser.parse_args()

input_folder = '/home/zizhou/3d/tetwild_out_1'
output_dir = '/home/zizhou/3d/ansys3d_1'

# os.chdir("/home/zizhou/OpenFOAM/zizhou-8/run/transfer")
# for root, _, files in os.walk(input_folder):
#     for file in files:
#         if file.find('.mesh') == -1:
#             continue
#         input = os.path.join(root, file)
#         output = os.path.join(output_dir, file[:-5]+'.msh')
#         os.system("gmsh "+input+" -save -format msh22 -o /home/zizhou/OpenFOAM/zizhou-8/run/transfer/"+file.split('.')[0]+'.msh')
#         os.system("gmshToFoam "+file.split('.')[0]+'.msh')
#         # os.system("checkMesh")
#         os.system("rm "+file.split('.')[0]+'.msh')
#         os.system("foamMeshToFluent")
#         os.system("cp ./fluentInterface/transfer.msh "+output)

file = args.file
input = os.path.join(input_folder, file)
workdir = os.path.join('/home/zizhou/OpenFOAM/zizhou-8/run','trans_'+file[:-5])
os.system('cp -r /home/zizhou/OpenFOAM/zizhou-8/run/transfer '+workdir)
output = os.path.join(output_dir, file[:-5]+'.msh')
os.system("gmsh "+input+" -save -format msh22 -o "+os.path.join(workdir,file[:-5]+'.msh'))
os.chdir(workdir)
os.system("gmshToFoam "+file.split('.')[0]+'.msh')
# os.system("checkMesh")
os.system("rm "+file.split('.')[0]+'.msh')
os.system("foamMeshToFluent")
os.system("cp ./fluentInterface/transfer.msh "+output)
os.system('rm -r '+workdir)
