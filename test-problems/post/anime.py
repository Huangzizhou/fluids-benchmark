import os, argparse
import numpy as np
from paraview.simple import *

def get_files(folder):
    x = []
    y = []
    for root, _, files in os.walk(folder):
        for file in files:
            if solver != "mac":
                if file.find(".vtu") != -1 and file.find("step_") != -1:
                    x.append(os.path.join(root, file))
                    y.append(int(file.split('_')[1][:-4]))
            else:
                if file.find(".vtu") != -1:
                    x.append(os.path.join(root, file))
                    y.append(int(file[:-4]))

    y = np.array(y)
    x = np.array(x)
    x = x[np.argsort(y)]
    return x.tolist()


def anime(problem, solver, folder, vmag):
    input_files = get_files(folder)
    num_frames = len(input_files)

    paraview.simple._DisableFirstRenderCameraReset()

    LoadPlugin('/home/zizhou/paraview/lib/paraview-5.9/plugins/SurfaceLIC/SurfaceLIC.so', remote=False, ns=globals())

    LoadPalette(paletteName='WhiteBackground')

    step_ = XMLUnstructuredGridReader(FileName=input_files)

    # get animation scene
    animationScene1 = GetAnimationScene()

    # get the time-keeper
    timeKeeper1 = GetTimeKeeper()

    # update animation scene based on data timesteps
    animationScene1.UpdateAnimationUsingDataTimeSteps()

    # get active view
    renderView1 = GetActiveViewOrCreate('RenderView')
    # uncomment following to set a specific view size
    renderView1.ViewSize = [1506, 682]

    # get layout
    layout1 = GetLayout()

    # show data in view
    step_Display = Show(step_, renderView1, 'UnstructuredGridRepresentation')

    # trace defaults for the display properties.
    step_Display.Representation = 'Surface'

    # reset view to fit data
    renderView1.ResetCamera()

    # get the material library
    materialLibrary1 = GetMaterialLibrary()

    # show color bar/color legend
    step_Display.SetScalarBarVisibility(renderView1, True)

    # update the view to ensure updated data information
    renderView1.Update()

    # get color transfer function/color map for 'scalar_value_avg'
    scalar_value_avgLUT = GetColorTransferFunction('pressure')

    # get opacity transfer function/opacity map for 'scalar_value_avg'
    scalar_value_avgPWF = GetOpacityTransferFunction('pressure')

    # set scalar coloring
    ColorBy(step_Display, ('POINTS', 'solution', 'Magnitude'))

    # Hide the scalar bar for this color map if no visible data is colored by it.
    HideScalarBarIfNotNeeded(scalar_value_avgLUT, renderView1)

    # rescale color and/or opacity maps used to include current data range
    step_Display.RescaleTransferFunctionToDataRange(True, False)

    # show color bar/color legend
    step_Display.SetScalarBarVisibility(renderView1, True)

    # get color transfer function/color map for 'solution'
    solutionLUT = GetColorTransferFunction('solution')

    # get opacity transfer function/opacity map for 'solution'
    solutionPWF = GetOpacityTransferFunction('solution')

    # Rescale transfer function
    solutionLUT.RescaleTransferFunction(0.0, vmag)

    # Rescale transfer function
    solutionPWF.RescaleTransferFunction(0.0, vmag)

    #### saving camera placements for all active views

    # current camera placement for renderView1
    renderView1.InteractionMode = '2D'

    if problem.find('Lshape') != -1:
        renderView1.CameraPosition = [0.5, 0.1, 1.9701098547724778]
        renderView1.CameraFocalPoint = [0.5, 0.1, 0.0]
        renderView1.CameraParallelScale = 0.2878263584258619
    elif problem.find('airfoil') != -1:
        if solver == 'mac':
            renderView1.CameraPosition = [2.5, 1.5, 10000.0]
            renderView1.CameraFocalPoint = [2.5, 1.5, 0.0]
        else:
            renderView1.CameraPosition = [1.5, 0.0, 10000.0]
            renderView1.CameraFocalPoint = [1.5, 0.0, 0.0]
        renderView1.CameraParallelScale = 1.6457101660189228
    elif problem.find('corner') != -1:
        # renderView1.CameraPosition = [1.0, 0.5, 10000.0]
        # renderView1.CameraFocalPoint = [1.0, 0.5, 0.0]
        # renderView1.CameraParallelScale = 0.6311010395633536
        renderView1.CameraPosition = [2.0, 0.5, 7.96522841660369]
        renderView1.CameraFocalPoint = [2.0, 0.5, 0.0]
        renderView1.CameraParallelScale = 0.9617296018674538
    elif problem.find('cavity') != -1:
        renderView1.CameraPosition = [0.5, 0.5, 10000.0]
        renderView1.CameraFocalPoint = [0.5, 0.5, 0.0]
        renderView1.CameraParallelScale = 0.5843857695756589
    elif problem.find('tunnel') != -1:
        renderView1.CameraPosition = [1.1, 0.205, 4.3232492004724525]
        renderView1.CameraFocalPoint = [1.1, 0.205, 0.0]
        renderView1.CameraParallelScale = 0.6316120245402308
    else:
        assert(False)

    step_Display.SetRepresentationType('Surface LIC')

    step_Display.LICIntensity = 0.3

    # if solver != "fv":
    SaveAnimation(folder+'/anime.png', renderView1, ImageResolution=[1506, 682],
            FrameWindow=[0, num_frames])
    # else:
    #     SaveAnimation(folder+'/anime.png', renderView1, ImageResolution=[1506, 682],
    #         FrameWindow=[1, num_frames])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Solver Type.')
    parser.add_argument("folder", type=str)
    args = parser.parse_args()

    vmags_dict = {'tunnel': 2.5,
                'cavity': 1.2,
                'Lshape': 1.5,
                'airfoil': 1.3,
                'corner': 2.5}

    folder_name = args.folder.split('/')
    if folder_name[-1] == "":
        folder_name = folder_name[-2]
    else:
        folder_name = folder_name[-1]
    problem = folder_name.split('_')[0]

    if folder_name.find("fem") != -1:
        solver = 'fem'
    elif folder_name.find("split") != -1:
        solver = 'split'
    elif folder_name.find("flip") != -1:
        solver = 'flip'
    elif folder_name.find("fv") != -1:
        solver = 'fv'
    elif folder_name.find("mac") != -1:
        solver = 'mac'
    else:
        assert(False)

    anime(problem, solver, args.folder, vmags_dict[problem])
    print(args.folder + " finished!")
