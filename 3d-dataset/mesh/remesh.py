import os, subprocess

# extract boundary
for root, _, files in os.walk('mesh'):
    for file in files:
        subprocess.Popen(['python', 'extract_boundary.py',
                          '-i', os.path.join(root, file),
                          '-o', os.path.join('./stl3d_0', file[:-5]+'.stl')])

# meshing
with open('h-tetwild.csv','r') as f:
    lines = f.readlines()[1:]
    for line in lines:
        words = line.split(',')
        mesh = words[0]
        h_max = str(float(words[1]) * 0.6)
        subprocess.Popen(['/home/zizhou/TetWild/build/TetWild',
                        '--input',os.path.join('./stl3d_0',mesh+'.stl'),
                        '-a', h_max,
                        '--output',os.path.join('./tetwild_out',mesh+'_tet.msh')])
