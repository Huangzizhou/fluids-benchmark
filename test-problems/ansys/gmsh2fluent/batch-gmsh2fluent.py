import os

for root, _, files in os.walk('/home/zh1476/fluid/model-problems/ansys/msh22'):
    for file in files:
        if (file.find('.msh') != -1) and (not os.path.exists(os.path.join('/home/zh1476/fluid/model-problems/ansys/mesh', file))):
            print(os.path.join(root, file))
            # os.system('cp '+os.path.join(root, file)+' '+os.path.join(root, 'drag'+file[6:]))
            os.system('python gmsh2fluent.py -i '+os.path.join(root, file)+' -o '+os.path.join('/home/zh1476/fluid/model-problems/ansys/mesh', file))
