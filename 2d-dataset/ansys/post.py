from paraview.simple import *
import os
import numpy as np

a = "6.283185307179586"

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
    error = np.sqrt(error)

    return error

def h1_error(path):
    currentcase = EnSightReader(CaseFileName=path)

    gradientOfUnstructuredDataSet1 = GradientOfUnstructuredDataSet(Input=currentcase)

    gradientOfUnstructuredDataSet1.ScalarArray = ['POINTS', 'velocity']
    gradientOfUnstructuredDataSet1.ComputeDivergence = 1

    extractBlock1 = ExtractBlock(Input=gradientOfUnstructuredDataSet1)
    extractBlock1.BlockIndices = [1]

    cal0 = Calculator(Input=extractBlock1)
    cal0.Function = 'Gradients_0 + '+a+'*sin('+a+'*coordsX)*sin('+a+'*coordsY)*exp(-2*'+a+'*'+a+'*0.01*0.1)'
    cal0.ResultArrayName = 'error_0'

    cal1 = Calculator(Input=cal0)
    cal1.Function = 'Gradients_1 - '+a+'*cos('+a+'*coordsX)*cos('+a+'*coordsY)*exp(-2*'+a+'*'+a+'*0.01*0.1)'
    cal1.ResultArrayName = 'error_1'

    cal2 = Calculator(Input=cal1)
    cal2.Function = 'Gradients_3 + '+a+'*cos('+a+'*coordsX)*cos('+a+'*coordsY)*exp(-2*'+a+'*'+a+'*0.01*0.1)'
    cal2.ResultArrayName = 'error_2'

    cal3 = Calculator(Input=cal2)
    cal3.Function = 'Gradients_4 - '+a+'*sin('+a+'*coordsX)*sin('+a+'*coordsY)*exp(-2*'+a+'*'+a+'*0.01*0.1)'
    cal3.ResultArrayName = 'error_3'

    calculator2 = Calculator(Input=cal3)
    calculator2.ResultArrayName = 'error'
    calculator2.Function = 'error_0*error_0+error_1*error_1+error_2*error_2+error_3*error_3'

    integrateVariables1 = IntegrateVariables(Input=calculator2)
    SetActiveSource(integrateVariables1)
    data = paraview.servermanager.Fetch(integrateVariables1)
    numPoints = data.GetNumberOfPoints()
    error = 0
    for x in range(numPoints):
        error += data.GetPointData().GetArray('error').GetValue(x)
    error = np.sqrt(error)

    return error

def l2_error(path):
    currentcase = EnSightReader(CaseFileName=path)

    calculator1 = Calculator(Input=currentcase)
    calculator1.Function = 'velocity-(iHat*cos('+a+'*coordsX)*sin('+a+'*coordsY)-jHat*cos('+a+'*coordsY)*sin('+a+'*coordsX))*exp(-2*'+a+'*'+a+'*0.01*0.1)'

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
    error = np.sqrt(error)

    return error


ref = 1
visc = 1e-2

destination = "fv_ref"+str(ref)+".csv"

with open("time.csv",'r') as g:
    lines = g.readlines()[1:]
    meshes = [line[:-1].split(',')[0] for line in lines]
    times = [float(line[:-1].split(',')[1]) for line in lines]
    memories = [float(line[:-1].split(',')[2]) for line in lines]

idx = 0
errors_l2 = []
errors_h1 = []
errors_div = []
# errors_p = []
for mesh in meshes:
    print(mesh)
    path = os.path.join('/home/zizhou/2d/result',mesh,'step_1.encas')
    if os.path.exists(path):
        err_l2 = l2_error(path)
        errors_l2.append(err_l2)

        err_h1 = h1_error(path)
        errors_h1.append(err_h1)

        err_div = div_error(path)
        errors_div.append(err_div)

        print(err_l2,err_h1,err_div)
    else:
        assert(False)

with open("data.csv",'w') as g:
    g.write('mesh,time,memory,err_l2,err_h1,err_div\n')
    for mesh, time, memory, err_l2, err_h1, err_div in zip(meshes, times, memories, errors_l2, errors_h1, errors_div):
        g.write(mesh+','+repr(time)+','+repr(memory)+','+repr(err_l2)+','+repr(err_h1)+','+repr(err_div)+'\n')