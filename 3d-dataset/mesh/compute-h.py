import numpy as np
import os, meshio

def read_mesh(path):
    mesh = meshio.read(path)
    return mesh.points, mesh.cells[0][1]


def normalize(v):
    v_min = np.amin(v,axis=0)
    v_max = np.amax(v,axis=0)
    L = np.amax(v_max - v_min)
    v = (v - v_min) / L
    return v


def calc_h(v, e):
    if e.shape[1] == 4:
        edges = np.concatenate((e[:,0:2],e[:,1:3],e[:,2:4],e[:,np.array([3,0])]),axis=0)
    else:
        edges = np.concatenate((e[:,0:2],e[:,1:3],e[:,2:4],e[:,np.array([3,0])],
                                e[:,4:6],e[:,5:7],e[:,6:8],e[:,np.array([7,4])],
                                e[:,np.array([0,4])],e[:,np.array([1,5])],e[:,np.array([2,6])],e[:,np.array([3,7])]),axis=0)

    edges.sort(axis=1)
    edges = np.unique(edges,axis=0)
    start = v[edges[:,0],:]
    end = v[edges[:,1],:]
    dist = np.sum((start-end)**2,axis=1)
    max_d = np.amax(dist)
    min_d = np.amin(dist)

    return np.sqrt(max_d), np.sqrt(min_d), np.sum(np.sqrt(dist)) / dist.shape[0], v.shape[0], e.shape[0], edges.shape[0], np.amax(v,axis=0) - np.amin(v,axis=0)


def ModifyLine(path, new_path):
    content = []
    with open(path, 'r') as f:
        lines = f.readlines()
        for i in range(len(lines)):
            if i > 10:
                content = content + lines[i:]
                break
            line = lines[i]
            pos = line.find("Vertices ")
            if pos == -1:
                content.append(line)
            else:
                content.append("Vertices\n")
                content.append(line[pos+9:])
                content = content + lines[i+1:]
                
    with open(new_path, 'w') as f:
        f.writelines(content)

if __name__ == "__main__":
    h = []
    for root, _, files in os.walk("tetwild_out_1"):
        for file in files:
            if file[-5:] != '.mesh':
                continue
            v,e = read_mesh(os.path.join(root,file))
            h_max, h_min, h_avg, v_n, elem_n, e_n, bbox = calc_h(v, e)
            h.append(",".join([file[:-5], repr(h_max), repr(h_min), repr(h_avg), str(v_n), str(elem_n), str(e_n), repr(bbox[0]), repr(bbox[1]), repr(bbox[2])])+"\n")
            print(h[-1][:-1])

    with open("h.csv","w") as f:
        f.write('mesh,h_max,h_min,h_avg,v_n,elem_n,edge_n\n')
        f.writelines(h)
