import os, meshio, igl, argparse
import numpy as np
from queue import Queue

def split_quads(f):
    assert(f.shape[1] == 4)
    return np.concatenate((f[:,[0,1,2]],f[:,[2,3,0]]),axis=0)

# return True if same direction
def check_direction(f1, f2):
    e1 = [f1[[0,1]],f1[[1,2]],f1[[2,0]]]
    e2 = [f2[[1,0]],f2[[2,1]],f2[[0,2]]]
    for x in e1:
        for y in e2:
            if np.all(x == y):
                return True

    return False

def fix_surface_normal(f):
    assert(f.shape[1] == 3)
    TT, _ = igl.triangle_triangle_adjacency(f)
    finish_flag = np.zeros(f.shape[0],dtype=bool)
    in_queue_flag = np.zeros(f.shape[0],dtype=bool)
    q = Queue(maxsize=f.shape[0])

    q.put([0,0])
    finish_flag[0] = True
    in_queue_flag[0] = True

    while not q.empty():
        current = q.get()
        assert(finish_flag[current[0]])
        flag = check_direction(f[current[0]], f[current[1]])
        finish_flag[current[1]] = True
        if not flag:
            f[current[1],0], f[current[1],1] = f[current[1],1], f[current[1],0]

        for i_ in range(TT.shape[1]):
            i = TT[current[1], i_]
            if not in_queue_flag[i]:
                q.put([current[1],i])
                in_queue_flag[i] = True

    return f


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Solver Type.')
    parser.add_argument("--input", "-i", type=str, default='/home/zizhou/3d/mesh3d_0/2012SRF_ellipsoid-A_tet.mesh')
    parser.add_argument("--output", "-o", type=str)
    args = parser.parse_args()

    mesh = meshio.read(args.input)

    v = mesh.points
    elem = mesh.cells[0][1]

    if elem.shape[1] == 4:
        shape = 'tet'
    else:
        shape = 'hex'

    # extract boundary faces
    if shape == 'tet':
        f = np.concatenate((elem[:,[0,1,2]],elem[:,[1,2,3]],elem[:,[2,3,0]],elem[:,[0,1,3]]),axis=0)
    else:
        f = np.concatenate((elem[:,[3,2,1,0]],elem[:,[4,5,6,7]],elem[:,[0,1,5,4]],elem[:,[2,3,7,6]],elem[:,[4,7,3,0]],elem[:,[1,2,6,5]]),axis=0)

    boundary_faces = []
    f_sorted = np.sort(f,axis=1)
    indices = np.lexsort(f_sorted.T)
    f_sorted = f_sorted[indices]
    f = f[indices]

    i = 0
    while i < len(f_sorted):
        if i < len(f_sorted) - 1 and np.all(f_sorted[i] == f_sorted[i+1]):
            i += 2
        else:
            boundary_faces.append(f[i])
            i += 1

    boundary_faces = np.array(boundary_faces)

    # extract boundary vertices
    indices = np.unique(boundary_faces)
    mask = np.zeros(v.shape[0], dtype=int)
    mask[indices] = 1
    v = v[indices]
    mapping = np.cumsum(mask) - 1
    boundary_faces = mapping[boundary_faces]

    # save to obj
    if shape == 'hex':
        boundary_faces = split_quads(boundary_faces)
    else:
        boundary_faces = fix_surface_normal(boundary_faces)

    cells = [
        ("triangle", boundary_faces),
    ]

    mesh = meshio.Mesh(v,cells)
    mesh.write(args.output)