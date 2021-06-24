import os
import numpy as np
import numpy.linalg as lg

def read_msh(mesh):
    verts = []
    faces = []
    with open(mesh,'r') as f:
        lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            i += 1
            if line.find("$Nodes") != -1:
                num_v = int(lines[i][:-1])
                break

        i += 1
        while i < len(lines):
            line = lines[i]
            if line.find("$EndNodes") != -1:
                break
            i += 1
            numbers = line[:-1].split(' ')[1:]
            verts.append(list(map(np.float64, numbers)))
        
        while i < len(lines):
            line = lines[i]
            i += 1
            if line.find('$Elements') != -1:
                break
        
        i += 1
        while i < len(lines):
            line = lines[i]
            if line.find("$EndElements") != -1:
                break
            i += 1
            numbers = line[:-1].split(" ")

            # quad
            if numbers[1] == '3':
                faces.append(list(map(int, numbers[-4:])))
            # tri
            elif numbers[1] == '2':
                faces.append(list(map(int, numbers[-3:])))
    
    return np.array(verts), np.array(faces) - 1


def triangle_area(vert):
    return np.abs(lg.det(np.concatenate((vert,np.array([[1,1,1]]).T),axis=1))) / 2


def mesh_check(path):
    v, f = read_msh(path)
    if f.size == f.shape[0]:
        print("only 1 element")
        return False
    shape = f.shape[1]
    v = v[:,:-1]
    for face in f:
        vert = v[face,:]
        # flipped
        center = np.sum(vert, axis=0) / shape
        angles = []
        for j in range(shape):
            temp = vert[j,:] - center
            temp = temp / np.sqrt(np.sum(temp**2))
            angles.append(np.angle(complex(temp[0],temp[1])))
        min_angle = np.argmin(np.array(angles))
        for j in range(shape - 1):
            if angles[(min_angle + j)%shape] >= angles[(min_angle + j + 1)%shape]:
                return False
        if angles[(min_angle - 1)%shape] - angles[min_angle] >= 2 * np.pi:
            return False

    # convex
    if shape == 3:
        return True
    for face in f:
        vert = v[face,:]
        S012 = triangle_area(vert[np.array([0,1,2]),:])
        S230 = triangle_area(vert[np.array([2,3,0]),:])
        S013 = triangle_area(vert[np.array([1,3,0]),:])
        S123 = triangle_area(vert[np.array([2,3,1]),:])
        min_area = min(S012,S230,S013,S123)
        max_area = max(S012,S230,S013,S123)
        if np.abs(S012+S230-S013-S123) > 1e-12 or min_area < 0.01 * max_area:
            return False
    
    return True


def mesh_info(path):
    v, f = read_msh(path)
    if len(f.shape) == 1:
        f = f.reshape([1,3])
    if f.shape[1] == 3:
        e = np.concatenate((f[:,0:2],f[:,1:3],f[:,np.array([2,0])]), axis=0)
    else:
        e = np.concatenate((f[:,0:2],f[:,1:3],f[:,2:4],f[:,np.array([3,0])]), axis=0)

    e = np.unique(np.sort(e, axis=1), axis=0)
    h_max = 0
    h_min = 1e5
    v_1 = v[e[:,0]]
    v_2 = v[e[:,1]]
    dist = np.sqrt(np.sum((v_1 - v_2)**2, axis=1))

    return np.amax(dist), np.amin(dist), np.sum(dist) / dist.shape[0], v.shape[0], f.shape[0], e.shape[0]


if __name__ == '__main__':

    destination = '/home/zh1476/fluid/fluid2d/h_ref1.csv'
    folder_path = "/scratch/zh1476/msh2d_1"
    with open(destination,'w') as f:
        f.write("mesh,h_max,h_min,h_avg,vertices,elements,edges\n")

    for root, _, files in os.walk(folder_path):
        for file_ in files:
            path = os.path.join(root, file_)
            h_max, h_min, h_avg, v_num, f_num, e_num = mesh_info(path)
            with open(destination,'a') as f:
                f.write(','.join([file_, repr(h_max), repr(h_min), repr(h_avg), str(v_num), str(f_num), str(e_num)])+'\n')
            print(file_)

    # with open('/home/zh1476/h_.csv','r') as f:
    #     content = f.readlines()
    
    # for i in range(len(content)):
    #     os.system("echo "+str(i)+"...")
    #     line = content[i][:-1].split(',')
    #     if not mesh_check(os.path.join(folder_path, line[0])):
    #         del content[i]
    #         os.system("echo fail on "+line[0])

    # with open('/home/zh1476/h_filtered.csv','a') as f:
    #     f.writelines(content)