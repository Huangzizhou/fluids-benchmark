from paraview.simple import *
import numpy as np
import os, re, json, argparse
from multiprocessing import Process

def compute_airfoil_err(fine_path, coarse_path):
    finevtu = XMLUnstructuredGridReader(FileName=[fine_path])

    femvtu = XMLUnstructuredGridReader(FileName=[coarse_path])

    if coarse_path.find('mac') != -1:
        calculator0 = Calculator(Input=femvtu)
        calculator0.ResultArrayName = 'disp'
        calculator0.Function = '-1*iHat-1.5*jHat'

        warpByVector1 = WarpByVector(Input=calculator0, Vectors='disp')

        resampleWithDataset1 = ResampleWithDataset(SourceDataArrays=warpByVector1,
            DestinationMesh=finevtu)
    else:
        resampleWithDataset1 = ResampleWithDataset(SourceDataArrays=femvtu,
            DestinationMesh=finevtu)

    programmableFilter1 = ProgrammableFilter(Input=[resampleWithDataset1, finevtu])
    programmableFilter1.Script = """phi_0 = inputs[0].PointData['solution']
phi_1 = inputs[1].PointData['solution']
output.PointData.append(phi_1 - phi_0, 'difference')"""
    programmableFilter1.RequestInformationScript = ''
    programmableFilter1.RequestUpdateExtentScript = ''
    programmableFilter1.PythonPath = ''

    calculator3 = Calculator(Input=programmableFilter1)
    calculator3.ResultArrayName = 'pos1'
    calculator3.Function = '(0.25-coordsY)*(coordsY+0.2)'

    threshold1 = Threshold(Input=calculator3, Scalars='pos1')
    threshold1.ThresholdRange = [0.0, 100.0]

    calculator4 = Calculator(Input=threshold1)
    calculator4.ResultArrayName = 'pos2'
    calculator4.Function = '(coordsX+0.2)*(1.2-coordsX)'

    threshold2 = Threshold(Input=calculator4, Scalars='pos2')
    threshold2.ThresholdRange = [0.0, 100.0]

    calculator2 = Calculator(Input=threshold2)
    calculator2.ResultArrayName = 'Result'
    calculator2.Function = 'difference.difference'

    integrateVariables1 = IntegrateVariables(Input=calculator2)
    data = paraview.servermanager.Fetch(integrateVariables1)
    numPoints = data.GetNumberOfPoints()
    err_l2 = 0
    for x in range(numPoints):
        err_l2 += data.GetPointData().GetArray('Result').GetValue(x)
    err_l2 = np.sqrt(err_l2)
    return err_l2


def compute_err(fine_path, coarse_path):
    finevtu = XMLUnstructuredGridReader(FileName=[fine_path])

    femvtu = XMLUnstructuredGridReader(FileName=[coarse_path])

    # create a new 'Resample With Dataset'
    resampleWithDataset1 = ResampleWithDataset(SourceDataArrays=femvtu,
        DestinationMesh=finevtu)

    # create a new 'Programmable Filter'
    programmableFilter1 = ProgrammableFilter(Input=[resampleWithDataset1, finevtu])

    # Properties modified on programmableFilter1
    programmableFilter1.Script = """phi_0 = inputs[0].PointData['solution']
phi_1 = inputs[1].PointData['solution']
output.PointData.append(phi_1 - phi_0, 'difference')"""
    programmableFilter1.RequestInformationScript = ''
    programmableFilter1.RequestUpdateExtentScript = ''
    programmableFilter1.PythonPath = ''

    if coarse_path.find('cavity') != -1:
        calculator3 = Calculator(Input=programmableFilter1)
        calculator3.ResultArrayName = 'pos1'
        calculator3.Function = '(0.99 - coordsY) * (coordsY - 0.01)'

        threshold1 = Threshold(Input=calculator3, Scalars='pos1')
        threshold1.ThresholdRange = [0.0, 100.0]

        calculator4 = Calculator(Input=threshold1)
        calculator4.ResultArrayName = 'pos2'
        calculator4.Function = '(0.99 - coordsX) * (coordsX - 0.01)'

        threshold2 = Threshold(Input=calculator4, Scalars='pos2')
        threshold2.ThresholdRange = [0.0, 100.0]

        calculator2 = Calculator(Input=threshold2)
        calculator2.ResultArrayName = 'Result'
        calculator2.Function = 'difference.difference'
    else:
        calculator2 = Calculator(Input=programmableFilter1)
        calculator2.ResultArrayName = 'Result'
        calculator2.Function = 'difference.difference'

    integrateVariables1 = IntegrateVariables(Input=calculator2)
    data = paraview.servermanager.Fetch(integrateVariables1)
    numPoints = data.GetNumberOfPoints()
    err_l2 = 0
    for x in range(numPoints):
        err_l2 += data.GetPointData().GetArray('Result').GetValue(x)
    err_l2 = np.sqrt(err_l2)
    return err_l2


def get_result(root, file):
    words = file.split('_')
    problem = words[0] if words[0] != 'cavity0' else 'cavity'
    for word in words:
        if word.find('ref') != -1:
            ref = int(re.findall(r"\d+\.?\d*", word)[0])
        if word.find('visc') != -1:
            visc = re.findall(r"\d+\.?\d*", word)[0]
    for solver in solvers:
        if file.find(solver) != -1:
            cur_solver = solver

    if problem == "Lshape":
        fine_path = modify_visc(fine_path_dict[problem], visc)
    else:
        fine_path = fine_path_dict[problem]
    coarse_path = os.path.join(root, file)

    if file.find('airfoil') == -1:
        err_l2 = compute_err(fine_path, coarse_path)
    else:
        err_l2 = compute_airfoil_err(fine_path, coarse_path)

    # with open(os.path.join(root, file[:-4]+'.json')) as f:
    #     json_data = json.load(f)
    #     time = json_data['time_solving']
    #     memory = json_data['peak_memory']

    folder = file[:-4].replace('cavity0','cavity')
    path = os.path.join('./data/refine/json',problem,folder)
    if not os.path.exists(path):
        os.system('mkdir -p '+path)
    with open(os.path.join(path,'error.json'),'w') as g:
        json.dump({'error':err_l2}, g)

    print(','.join(list(map(str, [folder, err_l2]))))



def modify_visc(name, visc):
    words = name.split('_')
    for i in range(len(words)):
        if words[i][:4] == 'visc':
            words[i] = 'visc'+str(visc)
    return '_'.join(words)


fine_path_dict = {
                  "Lshape": "./data/refine/Lshape/Lshape_2d_fem_ref4_visc0.1_steps9600_order3.vtu",
                  "airfoil": "./data/refine/airfoil/airfoil_2d_fem_ref2_visc0.0002_steps3200_order3.vtu",
                  "corner": "./data/refine/corner/corner_2d_fem_ref3_visc0.001_steps5120_order3.vtu",
                  "cavity": "./data/refine/cavity/cavity_2d_fem_ref6_visc0.1_order3_steady.vtu",
                #   "cavity1": "./data/refine/cavity1/cavity_2d_fem_ref6_visc0.1_order3_steady.vtu",
                #   "cavity2": "./data/refine/cavity2/cavity_2d_fem_ref6_visc0.1_order3_steady.vtu",
                  "tunnel": "./data/refine/tunnel/tunnel_quad_2d_fem_ref4_visc0.001_steps2_order3.vtu", # "./data/refine/tunnel/tunnel_tri_2d_fem_ref3_visc0.001_steps4800_order3.vtu"
                 }

solvers = ['fem','split','flip','fv','mac']

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Solver Type.')
    parser.add_argument("--path", "-p", type=str)
    parser.add_argument("--solver", type=str, default='')
    parser.add_argument("--problem", type=str, default='')
    args = parser.parse_args()

    processes = []
    # fine_path = fine_path_dict[problem]
    for root, _, files in os.walk(args.path):
        for file in files:
            if file.find('order3') != -1 or file.find('.vtu') == -1 or file.find('steady') != -1:
                continue
            if args.solver != '' and file.find(args.solver) == -1:
                continue
            if args.problem != '' and file.find(args.problem) == -1:
                continue

            # get_result(root, file)
            processes.append(Process(target=get_result,args=(root, file)))
        # break

    for process in processes:
        process.start()

    for process in processes:
        process.join()