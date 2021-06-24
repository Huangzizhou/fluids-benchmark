import meshio, os, argparse, sys, time
import resource
import numpy as np

def myhex(m):
    return hex(m)[2:]

def signed_area(points):
    if points.shape[0] > 3:
        points = points[:3,:]
    return np.linalg.det(np.concatenate((points, np.ones([3,1])), axis=1))

def read_mesh(path):
    mesh = meshio.read(path)
    # print(mesh)
    v = mesh.points
    for x in mesh.cells_dict:
        if x == "triangle" or x == "quad":
            f = mesh.cells_dict[x]
            break
    return v, f

parser = argparse.ArgumentParser(description='Solver Type.')
parser.add_argument("--input", "-i", type=str, help="path to the input mesh")
parser.add_argument("--output", "-o", type=str, help="path to the output mesh")
# parser.add_argument("--problem", "-p", type=str, help="problem name")
args = parser.parse_args()

start_time = time.time()

# read mesh file
input = args.input
if args.output.find('.msh') != -1:
    output = args.output
else:
    print("Invalid output folder!!")
    exit(0)

v, f = read_mesh(input)
v = v[:,:2]

if signed_area(v[f[0,:],:]) < 0:
    f = f[:,::-1]

# find the adjacent faces of each edge
if f.shape[1] == 3:
    e = np.concatenate((f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]), axis=0).astype(int)
elif f.shape[1] == 4:
    e = np.concatenate((f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 3]], f[:, [3, 0]]), axis=0).astype(int)

tmp = np.sort(e, axis=1)
ind = np.lexsort((tmp[:,1],tmp[:,0]))
tmp = tmp[ind,:]
diff = np.logical_not(np.all(tmp[1:,:] == tmp[:-1,:], axis=1))
diff = np.insert(diff, 0, True)
e = np.concatenate((e, np.tile(np.arange(f.shape[0]), f.shape[1])[:,None]), axis=1).astype(int)
e = e[ind,:] + 1

data = np.zeros([diff.sum(), 4], dtype=int)
data[:, :3] = e[diff, :]
ind = np.nonzero(np.logical_not(diff))[0]
cum = np.cumsum(diff[:ind[-1]])
data[cum[ind - 1] - 1, 3] = e[ind, 2]

del cum, ind, e, tmp, diff

# set bc type
bc_dict = {'velocity': 10, 'neumann': 36, 'wall': 3, 'interior': 2, 'pressure': 5}
def set_bc(center, problem):
    eps = 1e-8
    if problem == "Lshape":
        if center[0] < eps:
            return 'velocity'
        elif center[0] > 1 - eps:
            return 'pressure'
        else:
            return 'wall'
    elif problem == "corner":
        if center[1] < eps:
            return 'velocity'
        elif center[0] > 4 - eps:
            return 'pressure'
        else:
            return 'wall'
    elif problem == "tgv":
        return 'velocity'
    elif problem == "cavity":
        if center[1] > 1 - eps:
            return 'velocity'
        else:
            return 'wall'
    elif problem == "airfoil":
        if center[0] < -1 + eps or center[0] > 4 - eps or center[1] < -1.5 + eps or center[1] > 1.5 - eps:
            return 'velocity'
        else:
            return 'wall'
    elif problem == "tunnel":
        if center[0] < eps:
            return 'velocity'
        elif center[0] > 2.2 - eps:
            return 'pressure'
        else:
            return 'wall'
    elif problem == "drag":
        if center[0] < eps or center[0] > 1 - eps or center[1] < eps or center[1] > 1 - eps:
            return 'velocity'
        else:
            return 'wall'

problems = ['Lshape','corner','tgv','airfoil','tunnel','cavity','drag']
problem = ""
for p in problems:
    if input.find(p) != -1:
        problem = p
        break
if problem == "":
    print('Problem not exists for '+input.split('/')[-1]+'!')
    exit(0)
    
bc_type_list = np.zeros(data.shape[0], dtype=int)
mask = data[:, 3] != 0
bc_type_list[mask] = bc_dict['interior']
ind = np.nonzero(np.logical_not(mask))[0]
centers = (v[data[ind, 0] - 1, :] + v[data[ind, 1] - 1, :]) / 2
for i, center in zip(ind, centers):
    bc_type_list[i] = bc_dict[set_bc(center, problem)]

del centers
        
order = np.argsort(bc_type_list)
data = data[order,:]
bc_type_list = bc_type_list[order]

del order

# write data to fluent msh file

cell_type = 1 if f.shape[1] == 3 else 3

content = ["(2 2)\n","(12 (0 1 "+myhex(f.shape[0])+" 0))\n", \
           "(13 (0 1 "+myhex(data.shape[0])+" 0))\n", \
           "(10 (0 1 "+myhex(v.shape[0])+" 0 2))\n", \
           "(12 (1 1 "+myhex(f.shape[0])+" 1 "+str(cell_type)+"))\n"]

num_type = 1
last_total = 0
idx = 0
while idx < len(data):
    faces = [" "]
    bc_type = bc_type_list[idx]
    faces.append(' '.join(list(map(myhex,data[idx]))) + '\n')
    while idx+1 < len(data) and bc_type == bc_type_list[idx+1]:
        idx += 1
        faces.append(' '.join(list(map(myhex,data[idx]))) + '\n')
    faces[0] = "(13 ("+str(num_type)+" "+myhex(last_total+1)+" "+myhex(idx+1)+" "+myhex(bc_type)+" 2)(\n"
    faces.append("))\n")
    last_total = idx+1
    idx += 1
    content = content + faces
    
    
vertices = ["(10 (1 1 "+myhex(v.shape[0])+" 1 2)(\n"]
for p in v:
    vertices.append(' '.join(list(map(repr, p)))+'\n')
vertices.append("))\n")

with open(output,'w') as f:
    f.writelines(content)
    f.writelines(vertices)

print(output)
print('Time:',time.time()-start_time)
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024., 'MB')