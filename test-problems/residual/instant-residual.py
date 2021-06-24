import numpy as np
from scipy.interpolate import *
import numpy.linalg as LA
import matplotlib.pyplot as plt
import meshio, re, argparse, os, sys, time

tend_dict = {"cavity": 2,
             "tgv": 0.1,
             "tunnel": 6,
             "corner": 8,
             "airfoil": 4, 
             "drag": 1,
             "Lshape": 6}

solvers = ['fem','split','flip','mac','fv']

def tgv_exact(pos, t, visc):
    a = np.pi * 2
    factor = np.exp(-2 * (a**2) * visc * t)
    vx = np.cos(a * pos[:, 0]) * np.sin(a * pos[:, 1]) * factor
    vy = -np.cos(a * pos[:, 1]) * np.sin(a * pos[:, 0]) * factor
    p = -0.25 * (np.cos(pos[:,0]*2*a) + np.cos(pos[:,1]*2*a)) * (factor ** 2)
    return np.concatenate((vx[:,None],vy[:,None]),axis=1), p
    
def tgv_advect(pos, t, visc):
    a = np.pi * 2
    factor = -0.5*a*np.exp(-4*a*a*visc*t)
    vx = np.sin(2*a*pos[:,0]) * factor
    vy = np.sin(2*a*pos[:,1]) * factor
    return np.concatenate((vx[:,None],vy[:,None]),axis=1)
    
def tgv_gradp(pos, t, visc):
    return -tgv_advect(pos, t, visc)

def tgv_dvdt(pos, t, visc):
    a = np.pi * 2
    v, _ = tgv_exact(pos, t, visc)
    return v * (-2*a*a*visc)

def tgv_diffusion(pos, t, visc):
    return tgv_dvdt(pos, t, visc)


def has_zero_frame(folder):
    if folder.find('fv') == -1 and folder.find('mac') == -1:
        return True
    else:
        return False


def compute_h(v, f):
    if f.shape[1] == 3:
        e = np.concatenate( (f[:, [0, 1]], f[:, [1, 2]], f[:, [0, 2]]) , axis=0 )
    else:
        e = np.concatenate( (f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 3]], f[:, [3, 0]]) , axis=0 )
    edge = v[e[:,0], :] - v[e[:,1], :]
    dist = LA.norm(edge, axis=1)
    return np.amin(dist)


def read_data(path):
    solution = []
    pressure = []
    coord = []

    mesh = meshio.read(path)
    solution = mesh.point_data['solution']
    coord = mesh.points
    cells = mesh.cells[0][1]
    pressure = mesh.point_data['pressure']
    
    mesh_size = compute_h(coord, cells)

    coord, ind = np.unique(coord.round(decimals=10), axis=0, return_index=True)
    solution = np.array(solution)[ind,:]
    pressure = np.array(pressure)[ind]
    ind = np.lexsort((coord[:,1],coord[:,0]))
    
    return coord[ind,:2], solution[ind,:2], pressure[ind], mesh_size


def get_indices(folder):
    order = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.find('.vtu') != -1 and file.find('boundary') == -1:
                order.append(float(re.findall(r"\d+\.?\d*", file)[0]))
    return np.sort(np.array(order))


def read_transient_data(folder, id):
    vtu_files = []
    order = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.find('.vtu') != -1 and file.find('boundary') == -1:
                vtu_files.append(file)
                order.append(float(re.findall(r"\d+\.?\d*", file)[0]))
        
    vtu_files = np.array(vtu_files)
    vtu_files = vtu_files[np.argsort(order)]
    if folder.find('fv') == -1 and folder.find('mac') == -1:
        vtu_files = vtu_files[1:]

    T = tend_dict[get_problem(folder)]
    time_arr = np.linspace(0,T,len(vtu_files)+1)[1:]

    id_min = max(id - 8, 0)
    id_max = min(id + 8, len(vtu_files))
    vtu_files = vtu_files[id_min:id_max]
    time_arr = time_arr[id_min:id_max]
    vel = []
    p = []
    for i in range(len(vtu_files)):
        file = vtu_files[i]
        pos, vel_, p_, mesh_size = read_data(os.path.join(root, file))
        # vel_, p_ = tgv_exact(pos, time_arr[i], visc)
        vel.append(vel_)
        p.append(p_)
    vel = np.array(vel)
    # p = np.array(p).reshape([vel.shape[0], vel.shape[1], 1])
    return pos, np.array(vel), np.array(p), mesh_size, time_arr, id - id_min


def fit_spatial_derivatives(x, y, velocity, pressure, visc):
    grad_v = np.zeros((2,velocity.shape[0],2))   # grad_v[i, j, :] = grad(vi) at point j
    grad_p = np.zeros((velocity.shape[0],2))       # grad_p[j, :] = grad(p) at point j
    laplacian_v = np.zeros((velocity.shape[0],2))  # laplacian_v[i, :] = laplacian(v) at point i
    
    order = 3
    for i in range(2):
        s = RectBivariateSpline(x, y, velocity[:,i].reshape((x.shape[0],y.shape[0])), kx = order, ky = order)
        tmp = s(x, y, grid=True).reshape(-1)
        dsdx = s(x, y, grid=True, dx=1).reshape(-1)
        dsdy = s(x, y, grid=True, dy=1).reshape(-1)
        grad_v[i,:,:] = np.concatenate((dsdx[:,None],dsdy[:,None]),axis=1)

        dsdx2 = s(x, y, grid=True, dx=2).reshape(-1)
        dsdy2 = s(x, y, grid=True, dy=2).reshape(-1)
        laplacian_v[:,i] = dsdx2 + dsdy2

    s = RectBivariateSpline(x, y, pressure.reshape((x.shape[0],y.shape[0])), kx = order, ky = order)
    grad_p[:,0] = s(x, y, grid=True, dx=1).reshape(-1)
    grad_p[:,1] = s(x, y, grid=True, dy=1).reshape(-1)

    advection = np.zeros(velocity.shape)
    for i in range(2):
        for j in range(velocity.shape[0]):
            advection[j, i] = grad_v[i,j,:].dot(velocity[j,:])

    res = advection + grad_p - laplacian_v * visc
    
    return res, advection, grad_p, laplacian_v * visc


def fit_time_arr_derivatives(time_arr, vel):
    # dvdt = np.zeros(vel.shape)
    # for i in range(vel.shape[1]):
    #     for j in range(vel.shape[2]):
    #         spl = splrep(time_arr, vel[:,i,j], k=5)
    #         dvdt[:, i, j] = splev(time_arr, spl, der=1)

    # return dvdt

    s = CubicSpline(time_arr, vel)
    dvdt = s.derivative()
    return dvdt(time_arr)


def draw_field(x, y, field, path='', data_range=None, title=''):
    fig,ax = plt.subplots()
    if data_range == None:
        data_range = [0, 100]
    vmin, vmax = np.percentile(field,data_range[0]), np.percentile(field,data_range[1])
    levels = np.linspace(vmin, vmax, 100+1)
    contourf_ = ax.contourf(x,y,field.T, levels=levels, vmin=vmin, vmax=vmax)
    plt.axis('equal')
    plt.xlim(x[0],x[-1])
    plt.ylim(y[0],y[-1])
    cbar = fig.colorbar(contourf_)
    ax.title.set_text(title)
    # plt.show()
    if path != '':
        plt.savefig(path)
    plt.close()


def dense_sample_grid(pos, h):
    pos_min = np.amin(pos, axis=0)
    pos_max = np.amax(pos, axis=0)
    N = np.round((pos_max - pos_min) / h)
    new_x = np.linspace(pos_min[0], pos_max[0], N[0] + 1)
    new_y = np.linspace(pos_min[1], pos_max[1], N[1] + 1)
    new_pos = np.concatenate((np.repeat(new_x,new_y.shape[0])[:,None],np.tile(new_y,new_x.shape[0])[:,None]),axis=1)

    return new_x, new_y, new_pos


def dense_sample_field(pos, new_pos, field):
    field_dense = CloughTocher2DInterpolator(pos, field, fill_value=0)
    
    return field_dense(new_pos)


def compute_residual(problem, pos, vel, p, mesh_size, t_id, time_arr, structured=False, draw=""):
    x, y, pos_ = dense_sample_grid(pos, mesh_size)
    # print(p.shape)
    if not structured:
        vel = dense_sample_field(pos, pos_, vel.transpose([1,0,2])).transpose([1,0,2])
        p = dense_sample_field(pos, pos_, p.transpose([1,0,2])).transpose([1,0,2])
    else:
        assert(np.linalg.norm(pos_ - pos) < 1e-10)

    p = p.reshape(p.shape[:-1])

    # for i in range(len(time_arr)):
        # vel[i,:,:], p[i,:] = tgv_exact(pos_, time_arr[i], visc)

    if problem == "tunnel":
        mask = np.linalg.norm(pos_ - np.array([0.2,0.2]), axis=1)
        vel[:, mask <= 0.05, :] = 0
        p[:, mask <= 0.05] = 0
    elif problem == "corner":
        mask = np.logical_and(pos_[:,0] >= 0.5, pos_[:,1] <= 0.5)
        vel[:, mask, :] = 0
        p[:, mask] = 0
    elif problem == "Lshape":
        mask = np.logical_and(pos_[:,0] <= 0.2, pos_[:,1] <= 0.1)
        vel[:, mask, :] = 0
        p[:, mask] = 0

    # nan_field = np.logical_not(np.all(np.all(np.isfinite(vel), axis=0), axis=1)).reshape(x.shape[0], y.shape[0])
    # print(vel[:,0,:])

    dt = time_arr[1] - time_arr[0]
    h1 = x[1] - x[0]
    h2 = y[1] - y[0]

    # compute point-wise residual
    res, advection, grad_p, diffusion = fit_spatial_derivatives(x, y, vel[t_id,:,:], p[t_id,:], visc)
    dvdt = fit_time_arr_derivatives(time_arr, vel)[t_id,:,:]
    res += dvdt

    if draw != "":
        global folder_name
        draw_field(x, y, np.linalg.norm(advection - tgv_advect(pos_, time_arr[t_id], visc), axis=1).reshape(x.shape[0],y.shape[0]), "./pics/"+ folder_name + "_advect.png")
        draw_field(x, y, np.linalg.norm(grad_p - tgv_gradp(pos_, time_arr[t_id], visc), axis=1).reshape(x.shape[0], y.shape[0]), "./pics/"+ folder_name + "_gradp.png")
        draw_field(x, y, np.linalg.norm(diffusion - tgv_diffusion(pos_, time_arr[t_id], visc), axis=1).reshape(x.shape[0], y.shape[0]), "./pics/"+ folder_name + "_diffusion.png")
        draw_field(x, y, np.linalg.norm(dvdt - tgv_dvdt(pos_, time_arr[t_id], visc), axis=1).reshape(x.shape[0], y.shape[0]), "./pics/"+ folder_name + "_dvdt.png")

    # compute point-wise error
    if problem == "tgv":
        vel_exact, p_exact = tgv_exact(pos_, time_arr[t_id], visc)
        error = np.sum((vel[t_id,:,:] - vel_exact)**2)
    else:
        error = 0
    
    res = np.linalg.norm(res, axis=1)
    if problem == "tunnel":
        mask = np.linalg.norm(pos_ - np.array([0.2,0.2]), axis=1)
        res[mask < 0.07] = 0
    elif problem == "corner":
        mask = np.logical_and(pos_[:,0] >= 0.45, pos_[:,1] <= 0.55)
        res[mask] = 0
    elif problem == "Lshape":
        mask = np.logical_and(pos_[:,0] <= 0.24, pos_[:,1] <= 0.12)
        res[mask] = 0

    res = res.reshape([x.shape[0],y.shape[0]])

    for i in [0, -1]:
        res[i, :] = 0
        res[:, i] = 0

    if draw != "":
        draw_field(x, y, res, draw)

    return res, np.sum(res ** 2) * (h1 * h2), error * (h1 * h2)


def get_problem(folder):
    if folder.find('tgv') != -1:
        return 'tgv'
    elif folder.find('tunnel') != -1:
        return 'tunnel'
    elif folder.find('airfoil') != -1:
        return 'airfoil'
    elif folder.find('corner') != -1:
        return 'corner'
    elif folder.find('cavity') != -1:
        return 'cavity'
    elif folder.find('Lshape') != -1:
        return 'Lshape'


def get_solver(folder):
    if folder.find('fem') != -1:
        return 'fem'
    elif folder.find('split') != -1:
        return 'split'
    elif folder.find('flip') != -1:
        return 'flip'
    elif folder.find('fv') != -1:
        return 'fv'
    elif folder.find('mac') != -1:
        return 'mac'


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='')
    parser.add_argument("path", type=str, help="data folder")
    parser.add_argument("--output", default="tmp.csv", type=str)
    parser.add_argument("--idx", type=int)
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print("Can't find the folder!")
        sys.exit(0)

    folder_name = args.path.split('/')[-1]
    problem_name = get_problem(folder_name)
    visc = folder_name.split('_')
    for word in visc:
        if word.find('visc') != -1:
            visc = word
            break
    visc = float(re.findall(r"\d+\.?\d*", visc)[0])
    solver = get_solver(folder_name)

    folder = args.path
    indices = get_indices(folder)
    if has_zero_frame(folder_name):
        indices = indices[1:]

    if (problem_name == 'tgv' or problem_name == 'cavity') and (folder_name.find('tri') == -1):
        is_structured = True
    else:
        is_structured = False
        
    pos, vel, p, mesh_size, time_arr, t_id = read_transient_data(folder, args.idx)
    if args.idx < len(indices) - 1:
        res, val, err = compute_residual(problem_name, pos, vel, p, mesh_size, t_id, time_arr, structured=is_structured)
    else:
        res, val, err = compute_residual(problem_name, pos, vel, p, mesh_size, t_id, time_arr, structured=is_structured, draw=os.path.join('./pics',folder_name+'.png'))
    if folder.find('tgv') != -1:
        print('[%d / %d] residual = %e, error = %e' % (args.idx+1, len(indices), np.sqrt(val), np.sqrt(err)), flush=True)
    else:
        print('[%d / %d] residual = %e' % (args.idx+1, len(indices), np.sqrt(val)), flush=True)
    
    with open(args.output,'a') as f:
        f.write(','.join([problem_name, solver, str(args.idx), repr(np.sqrt(val))])+'\n')
