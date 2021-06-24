from paraview.simple import *
import os, json
import numpy as np
from multiprocessing import Process

T = 0.05

def div_error(path):
    currentcase = EnSightReader(CaseFileName=path)

    gradientOfUnstructuredDataSet1 = GradientOfUnstructuredDataSet(Input=currentcase)

    gradientOfUnstructuredDataSet1.ScalarArray = ['POINTS', 'velocity']
    gradientOfUnstructuredDataSet1.ComputeDivergence = 1

    extractBlock1 = ExtractBlock(Input=gradientOfUnstructuredDataSet1)
    extractBlock1.BlockIndices = [1]

    calculator2 = Calculator(Input=extractBlock1)
    calculator2.ResultArrayName = 'error'
    calculator2.Function = 'Divergence*Divergence'

    integrateVariables1 = IntegrateVariables(Input=calculator2)
    SetActiveSource(integrateVariables1)
    data = paraview.servermanager.Fetch(integrateVariables1)
    numPoints = data.GetNumberOfPoints()
    error = 0
    for x in range(numPoints):
        error += data.GetPointData().GetArray('error').GetValue(x)
    error = np.sqrt(abs(error))

    return error


def h1_error(path):
    currentcase = EnSightReader(CaseFileName=path)

    gradientOfUnstructuredDataSet1 = GradientOfUnstructuredDataSet(Input=currentcase)

    gradientOfUnstructuredDataSet1.ScalarArray = ['POINTS', 'velocity']
    gradientOfUnstructuredDataSet1.ComputeDivergence = 1

    extractBlock1 = ExtractBlock(Input=gradientOfUnstructuredDataSet1)
    extractBlock1.BlockIndices = [1]

    cal0 = Calculator(Input=extractBlock1)
    cal0.Function = 'Gradients_0 - (exp(coordsZ)*sin(coordsY+coordsX) - exp(coordsX)*sin(coordsZ+coordsY))*exp(-0.01 * '+str(T)+')'
    cal0.ResultArrayName = 'error_0'

    cal1 = Calculator(Input=cal0)
    cal1.Function = 'Gradients_1 - (exp(coordsZ)*sin(coordsY+coordsX) - exp(coordsX)*cos(coordsZ+coordsY))*exp(-0.01 * '+str(T)+')'
    cal1.ResultArrayName = 'error_1'

    cal2 = Calculator(Input=cal1)
    cal2.Function = 'Gradients_2 - (-exp(coordsZ)*cos(coordsY+coordsX) - exp(coordsX)*cos(coordsZ+coordsY))*exp(-0.01 * '+str(T)+')'
    cal2.ResultArrayName = 'error_2'

    cal3 = Calculator(Input=cal2)
    cal3.Function = 'Gradients_3 - (- exp(coordsY)*cos(coordsZ+coordsX) - exp(coordsX)*cos(coordsZ+coordsY))*exp(-0.01 * '+str(T)+')'
    cal3.ResultArrayName = 'error_3'

    cal4 = Calculator(Input=cal3)
    cal4.Function = 'Gradients_4 - (exp(coordsX)*sin(coordsY+coordsZ) - exp(coordsY)*sin(coordsZ+coordsX))*exp(-0.01 * '+str(T)+')'
    cal4.ResultArrayName = 'error_4'

    cal5 = Calculator(Input=cal4)
    cal5.Function = 'Gradients_5 - (exp(coordsX)*sin(coordsY+coordsZ) - exp(coordsY)*cos(coordsZ+coordsX))*exp(-0.01 * '+str(T)+')'
    cal5.ResultArrayName = 'error_5'

    cal6 = Calculator(Input=cal5)
    cal6.Function = 'Gradients_6 - (exp(coordsY)*sin(coordsZ+coordsX) - exp(coordsZ)*cos(coordsX+coordsY))*exp(-0.01 * '+str(T)+')'
    cal6.ResultArrayName = 'error_6'

    cal7 = Calculator(Input=cal6)
    cal7.Function = 'Gradients_7 - (-exp(coordsZ)*cos(coordsY+coordsX) - exp(coordsY)*cos(coordsZ+coordsX))*exp(-0.01 * '+str(T)+')'
    cal7.ResultArrayName = 'error_7'

    cal8 = Calculator(Input=cal7)
    cal8.Function = 'Gradients_8 - (exp(coordsY)*sin(coordsZ+coordsX) - exp(coordsZ)*sin(coordsX+coordsY))*exp(-0.01 * '+str(T)+')'
    cal8.ResultArrayName = 'error_8'

    calculator2 = Calculator(Input=cal8)
    calculator2.ResultArrayName = 'error'
    calculator2.Function = 'error_0*error_0+error_1*error_1+error_2*error_2+error_3*error_3+error_4*error_4+error_5*error_5+error_6*error_6+error_7*error_7+error_8*error_8'

    integrateVariables1 = IntegrateVariables(Input=calculator2)
    SetActiveSource(integrateVariables1)
    data = paraview.servermanager.Fetch(integrateVariables1)
    numPoints = data.GetNumberOfPoints()
    error = 0
    for x in range(numPoints):
        error += data.GetPointData().GetArray('error').GetValue(x)
    error = np.sqrt(abs(error))

    return error


def l2_error(path):
    currentcase = EnSightReader(CaseFileName=path)

    calculator1 = Calculator(Input=currentcase)
    calculator1.Function = 'velocity+(iHat*(exp(coordsX)*sin(coordsY+coordsZ)+exp(coordsZ)*cos(coordsX+coordsY))+jHat*(exp(coordsY)*sin(coordsX+coordsZ)+exp(coordsX)*cos(coordsZ+coordsY))+kHat*(exp(coordsZ)*sin(coordsX+coordsY)+exp(coordsY)*cos(coordsX+coordsZ)))*exp(-0.01 * '+str(T)+')'

    calculator2 = Calculator(Input=calculator1)
    calculator2.ResultArrayName = 'Result2'
    calculator2.Function = 'Result.Result'

    integrateVariables1 = IntegrateVariables(Input=calculator2)
    SetActiveSource(integrateVariables1)
    data = paraview.servermanager.Fetch(integrateVariables1)
    numPoints = data.GetNumberOfPoints()
    error = 0
    for x in range(numPoints):
        error += data.GetPointData().GetArray('Result2').GetValue(x)
    error = np.sqrt(abs(error))

    return error


def write_data(root, dir):
    path = os.path.join(root,dir,'step_1.encas')
    if os.path.exists(path):
        err_l2 = l2_error(path)
        err_h1_semi = h1_error(path)
        err_h1 = np.sqrt(err_l2**2 + err_h1_semi**2)

        with open(os.path.join(root, dir, 'output.json'),'r') as f:
            json_data = json.load(f)

        with open("data.csv",'a') as f:
            f.write(dir+','+repr(json_data["time_solving"])+','+repr(json_data["peak_memory"])+','+repr(err_l2)+','+repr(err_h1)+','+repr(err_h1_semi)+'\n')


visc = 1e-2

with open("data.csv",'w') as g:
    g.write('mesh,time,memory,err_l2,err_h1,err_h1_semi\n')

jobs = []

for root, dirs, files in os.walk('/home/zizhou/3d/result'):
    for dir in dirs:
        print(dir)
        os.system('cp /home/zizhou/3d/result/step_1.encas '+os.path.join(root, dir))
        # write_data(root, dir)
        jobs.append(Process(target=write_data,args=(root, dir)))
    break

for job in jobs:
    job.start()

for job in jobs:
    job.join()