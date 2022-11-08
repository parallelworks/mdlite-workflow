from paraview.simple import *
import sys
import data_IO
import os
import subprocess
import shutil

# For saving plots as pngs
import matplotlib

import numpy as np
import warnings

def getParaviewVersion():
    """ Return paraview version as a double number: e.g. 5.4"""
    PVversionMajor = paraview.servermanager.vtkSMProxyManager.GetVersionMajor() 
    PVversionMinor = paraview.servermanager.vtkSMProxyManager.GetVersionMinor()
    PVversion = PVversionMajor + PVversionMinor/100.0
    return PVversion


def planeNormalFromName(planeName):
    if planeName.lower() == "x":
        normal = [1.0, 0.0, 0.0]
    if planeName.lower() == "y":
        normal = [0.0, 1.0, 0.0]
    if planeName.lower() == "z":
        normal = [0.0, 0.0, 1.0]
    return normal


def setviewposition(position_key, camera):
    center = position_key.split()
    nPoints = len(center)/3
    positionXYZ = []
    for iPoint in range(nPoints):
        positionXYZ.extend(list(camera.GetFocalPoint()))
        for i in range(iPoint*3, 3+iPoint*3):
            if center[i] != "center":
                positionXYZ[i] = float(center[i])
    return positionXYZ


def read_csv(f):
    kpihash = {}
    cols = [l.replace("\n", "") for l in f.readline().split(",")]
    for i, line in enumerate(f):
        data = [l.replace("\n", "") for l in line.split(",")]
        kpihash[data[0]] = {}
        for ii, v in enumerate(data):
            if ii != 0:
                kpihash[data[0]][cols[ii]] = v
    return kpihash


def getfieldsfromkpihash(kpihash):
    cellsarrays = []
    for kpi in kpihash:
        if 'field' in kpihash[kpi]:
            cellsarrays.append(kpihash[kpi]['field'])

    ca = set(cellsarrays)
    cellsarrays = list(ca)
    return cellsarrays


def isfldScalar(arrayInfo):
    numComps = arrayInfo.GetNumberOfComponents()
    if numComps == 1:
        return True
    else:
        return False


def getfldComponentMap(arrayInfo):
    compName2num = {}
    numComps = arrayInfo.GetNumberOfComponents()
    if numComps>1:
        for iComp in range(-1,numComps):
            compName2num[arrayInfo.GetComponentName(iComp)] = iComp
    return compName2num


def getfldCompNumber(arrayInfo, kpiComp):
    compNumberMap = getfldComponentMap(arrayInfo)
    if not kpiComp:
        compNum = 0
    else:
        compNum = compNumberMap[kpiComp]
    return compNum


def getdatarange(datasource, kpifld, kpifldcomp):
    arrayInfo = datasource.PointData[kpifld]
    compNumber = getfldCompNumber(arrayInfo, kpifldcomp)
    datarange = arrayInfo.GetRange(compNumber)
    return datarange


def extractStatsOld(d, kpi, kpifield, kpiComp, kpitype, fp_csv_metrics, ave=[]):
    datarange = getdatarange(d, kpifield, kpiComp)
    if kpitype == "Probe":
        average=(datarange[0]+datarange[1])/2
    elif kpitype == "Line":
        average=ave
    elif kpitype == "Slice":
        # get kpi field value and area - average = value/area
        integrateVariables = IntegrateVariables(Input=d)
        average = getdatarange(integrateVariables, kpifield, kpiComp)[0]\
                 / integrateVariables.CellData['Area'].GetRange()[0]
    elif kpitype == "Volume" or kpitype == "Clip":
        integrateVariables = IntegrateVariables(Input=d)
        average = getdatarange(integrateVariables, kpifield, kpiComp)[0]\
                  / integrateVariables.CellData['Volume'].GetRange()[0]

    fp_csv_metrics.write(",".join([kpi, str(average), str(datarange[0]),str(datarange[1])]) + "\n")


def extractStats(dataSource, kpi, kpifield, kpiComp, kpitype, fp_csv_metrics):
    # If kpifield is a vector, add a calculater on top and extract the component of the vector
    # as a scalar
    
    arrayInfo = dataSource.PointData[kpifield]
    if isfldScalar(arrayInfo):
        statVarName = kpifield
    else:
        # create a new 'Calculator'
        statVarName = kpifield + '_' + kpiComp
        calc1 = Calculator(Input=dataSource)
        calc1.ResultArrayName = statVarName
        if kpiComp == 'Magnitude':
            calc1.Function = 'mag('+kpifield+')'
        else:
            calc1.Function = calc1.ResultArrayName
        UpdatePipeline()
        dataSource = calc1

    # create a new 'Descriptive Statistics'
    dStats = DescriptiveStatistics(Input=dataSource, ModelInput=None)
    
    dStats.VariablesofInterest = [statVarName]
    UpdatePipeline()

    dStatsDataInfo = dStats.GetDataInformation()
    dStatsStatsInfo = dStatsDataInfo.GetRowDataInformation()
    numStats = dStatsDataInfo.GetRowDataInformation().GetNumberOfArrays()

    for iStat in range(numStats):
        statName = dStatsStatsInfo.GetArrayInformation(iStat).GetName()
        statValue = dStatsStatsInfo.GetArrayInformation(iStat).GetComponentRange(0)[0]
        if  statName == 'Maximum':
            maxaximum = statValue
        elif statName == 'Minimum' :
            minimum = statValue
        elif statName == 'Mean':
            average = statValue
        elif statName == 'Standard Deviation':
            stanDev = statValue

    fp_csv_metrics.write(",".join([kpi, str(average), str(minimum), str(maxaximum), str(stanDev)]) + "\n")


def correctfieldcomponent(datasource, metrichash):
    """
    Set "fieldComponent" to "Magnitude" if the component of vector/tensor fields is not given. For scalar fields set 
    "fieldComponent" to an empty string.
    """
    kpifld = metrichash['field']
    arrayInfo = datasource.PointData[kpifld]
    if isfldScalar(arrayInfo):
        metrichash['fieldComponent'] = ''
    else:
        if not 'fieldComponent' in metrichash:
            metrichash['fieldComponent'] = 'Magnitude'
    return metrichash


def getReaderTypeFromfileAddress(dataFileAddress):
    if dataFileAddress.endswith('system/controlDict'):
        readerType = 'openFOAM'
    else:
        try:
            filename, file_extension = os.path.splitext(dataFileAddress)
            readerType = file_extension.replace('.', '')
        except:
            print('Error: Reader type cannot be set. Please check data file address')
            sys.exit(1)

    return readerType


def readDataFile(dataFileAddress, dataarray):

    readerType = getReaderTypeFromfileAddress(dataFileAddress)
    print readerType
    if readerType == 'exo':
        # Read the results file : create a new 'ExodusIIReader'
        dataReader = ExodusIIReader(FileName=dataFileAddress)

        dataReader.ElementBlocks = ['PNT', 'C3D20 C3D20R', 'COMPOSITE LAYER C3D20', 'Beam B32 B32R',
                                    'CPS8 CPE8 CAX8 S8 S8R', 'C3D8 C3D8R', 'TRUSS2', 'TRUSS2',
                                    'CPS4R CPE4R S4 S4R', 'CPS4I CPE4I', 'C3D10', 'C3D4', 'C3D15',
                                    'CPS6 CPE6 S6', 'C3D6', 'CPS3 CPE3 S3',
                                    '2-node 1d network entry elem', '2-node 1d network exit elem',
                                    '2-node 1d genuine network elem']

        # only load the data that is needed
        dataReader.PointVariables = dataarray
    elif readerType == 'openFOAM':
        # create a new 'OpenFOAMReader'
        dataReader = OpenFOAMReader(FileName=dataFileAddress)

        dataReader.MeshRegions = ['internalMesh']

        dataReader.CellArrays = dataarray

    elif readerType == 'vtk':
        dataReader = LegacyVTKReader(FileNames=[dataFileAddress])
        
    elif readerType == 'stl':
        dataReader = STLReader(FileNames=[dataFileAddress])

    return dataReader


def getTimeSteps():
    # get animation scene
    animationScene1 = GetAnimationScene()

    # update animation scene based on data timesteps
    animationScene1.UpdateAnimationUsingDataTimeSteps()

    timeSteps = []
    if type(animationScene1.TimeKeeper.TimestepValues)== int or type(animationScene1.TimeKeeper.TimestepValues)== float:
        timeSteps.append(animationScene1.TimeKeeper.TimestepValues)       
    else:
        timeSteps = list(animationScene1.TimeKeeper.TimestepValues)

    return timeSteps


def setFrame2latestTime(renderView1):

    TimeSteps = getTimeSteps()

    latesttime = TimeSteps[-1]
    print("Setting view to latest Time: " + str(latesttime))

    renderView1.ViewTime = latesttime
    return renderView1


def initRenderView (dataReader, viewSize, backgroundColor):
    # get active view
    renderView1 = GetActiveViewOrCreate('RenderView')

    try:
        renderView1 = setFrame2latestTime(renderView1)
    except:
        pass

    # set the view size
    renderView1.ViewSize = viewSize
    renderView1.Background = backgroundColor

    # show data in view
    readerDisplay = Show(dataReader, renderView1)

    # reset view to fit data
    renderView1.ResetCamera()

    return renderView1, readerDisplay


def colorMetric(d, metrichash):
    display = GetDisplayProperties(d)
    kpifld = metrichash['field']
    kpifldcomp = metrichash['fieldComponent']
    ColorBy(display, ('POINTS', kpifld, kpifldcomp))

    Render()
    UpdateScalarBars()
    ctf = GetColorTransferFunction(kpifld)
    try:
        ctf.ApplyPreset(metrichash["colorscale"], True)
    except:
        pass
    try:
        if data_IO.str2bool(metrichash["invertcolor"]):
            ctf.InvertTransferFunction()
    except:
        pass
    
    try:
        datarange = getdatarange(d, kpifld, kpifldcomp)
        min = datarange[0]
        max = datarange[1]
        if metrichash["min"] != "auto":
             min = float(metrichash["min"])
        if metrichash["max"] != "auto":
             max = float(metrichash["max"])
        ctf.RescaleTransferFunction(min, max)
        if int(metrichash["discretecolors"]) > 0:
            ctf.Discretize = 1
            ctf.NumberOfTableValues = int(metrichash["discretecolors"])
        else:
            ctf.Discretize = 0
    except:
        pass

    renderView1 = GetActiveViewOrCreate('RenderView')
    ctfColorBar = GetScalarBar(ctf, renderView1)

    ctfColorBar.Orientation = "Horizontal"

    # Properties modified on uLUTColorBar
    if 'barTitle' in metrichash:
        ctfColorBar.Title = metrichash["barTitle"]
    if 'ComponentTitle' in metrichash:
        ctfColorBar.ComponentTitle = metrichash["ComponentTitle"]
    if 'FontColor' in metrichash:
        ctfColorBar.TitleColor = data_IO.read_floats_from_string(metrichash["FontColor"])
        ctfColorBar.LabelColor = data_IO.read_floats_from_string(metrichash["FontColor"])
    else:
        ctfColorBar.TitleColor = [0, 0, 0]
        ctfColorBar.LabelColor = [0, 0, 0]
    if 'FontSize' in metrichash:
        ctfColorBar.TitleFontSize = int(metrichash["FontSize"])
        ctfColorBar.LabelFontSize = int(metrichash["FontSize"])
    if 'LabelFormat' in metrichash:
        ctfColorBar.LabelFormat = metrichash["LabelFormat"]
        ctfColorBar.RangeLabelFormat = metrichash["LabelFormat"]

    imgtype=metrichash['image'].split("_")[0]
    PVversion = getParaviewVersion()
    if (imgtype!="iso"):
        # center
        if PVversion < 5.04:
            ctfColorBar.Position = [0.25,0.05]
            ctfColorBar.Position2 = [0.5,0] # no such property in PV 5.04
        else:
            ctfColorBar.WindowLocation = 'LowerCenter'
    else:
        # left
        if PVversion < 5.04:
            ctfColorBar.Position = [0.05,0.025]
            ctfColorBar.Position2 = [0.4,0] # no such property in PV 5.04
        else:
            ctfColorBar.WindowLocation = 'LowerLeftCorner'

    #if individualImages == False:
    #    display.SetScalarBarVisibility(renderView1, False)


def createSlice(metrichash, dataReader, dataDisplay):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    opacity=float(metrichash['opacity'])
    bodyopacity=float(metrichash['bodyopacity'])
    dataDisplay.Opacity = bodyopacity
    dataDisplay.ColorArrayName = ['POINTS', '']
    slicetype = "Plane"
    plane = metrichash['plane']

    s = Slice(Input=dataReader)
    s.SliceType = slicetype
    s.SliceType.Origin = setviewposition(metrichash['position'], camera)
    s.SliceType.Normal = planeNormalFromName(plane)
    sDisplay = Show(s, renderView1)
    sDisplay.ColorArrayName = [None, '']
    sDisplay.SetRepresentationType('Surface')
    sDisplay.DiffuseColor = [0.0, 1.0, 0.0]
    sDisplay.Specular = 0
    sDisplay.Opacity = opacity
    colorMetric(s, metrichash)
    return s


def createStreamTracer(metrichash, data_reader, data_display):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    opacity = float(metrichash['opacity'])
    bodyopacity = float(metrichash['bodyopacity'])
    data_display.Opacity = bodyopacity
    data_display.ColorArrayName = ['POINTS', '']

    seedPosition = setviewposition(metrichash['position'], camera)
    if metrichash['seedType'].lower() == 'line':
        streamTracer = StreamTracer(Input=data_reader,
                                    SeedType='High Resolution Line Source')
        streamTracer.SeedType.Point1 = seedPosition[0:3]
        streamTracer.SeedType.Point2 = seedPosition[3:6]
        streamTracer.SeedType.Resolution = int(metrichash['resolution'])

    elif metrichash['seedType'].lower() == 'plane':
        # create a new 'Point Plane Interpolator' for seeding the stream lines
        pointPlaneInterpolator = PointPlaneInterpolator(Input=data_reader, Source='Bounded Plane')
        pointPlaneInterpolator.Source.Center = setviewposition(metrichash['center'], camera)
        pointPlaneInterpolator.Source.BoundingBox = seedPosition
        pointPlaneInterpolator.Source.Normal = planeNormalFromName(metrichash['plane'])
        pointPlaneInterpolator.Source.Resolution = int(metrichash['resolution'])
        UpdatePipeline()
        streamTracer = StreamTracerWithCustomSource(Input=data_reader,
                                                    SeedSource=pointPlaneInterpolator)


    kpifld = metrichash['field'] #!!!!!!!
    streamTracer.Vectors = ['POINTS', kpifld]
    
    streamTracer.IntegrationDirection = metrichash['integralDirection'] # 'BACKWARD', 'FORWARD' or  'BOTH'
    streamTracer.IntegratorType = 'Runge-Kutta 4'
    # To do : Add a default value based on domain size ?
    streamTracer.MaximumStreamlineLength = float(metrichash['maxStreamLength'])


    ##
    # create a new 'Tube'
    tube = Tube(Input=streamTracer)
    tube.Radius = float(metrichash['tubeRadius'])
    # show data in view
    tubeDisplay = Show(tube, renderView1)
    # trace defaults for the display properties.
    tubeDisplay.Representation = 'Surface'
    tubeDisplay.ColorArrayName = [None, '']
    tubeDisplay.EdgeColor = [0.0, 0.0, 0.0]
    tubeDisplay.DiffuseColor = [0.0, 1.0, 0.0]
    tubeDisplay.Specular = 0
    tubeDisplay.Opacity = opacity

    metrichash['field'] = metrichash['colorByField']
    if 'colorByFieldComponent' in metrichash:
        metrichash['fieldComponent'] = metrichash['colorByFieldComponent']
    metrichash = correctfieldcomponent(streamTracer, metrichash)
    colorMetric(tube, metrichash)
    try:
        if metrichash['image'].split("_")[1] == "solo":
            Hide(data_reader, renderView1)
    except:
        pass
    return tube


def createClip(metrichash, data_reader, data_display):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    opacity = float(metrichash['opacity'])
    bodyopacity = float(metrichash['bodyopacity'])
    data_display.Opacity = bodyopacity
    data_display.ColorArrayName = ['POINTS', '']
    cliptype = "Plane"
    plane = metrichash['plane']
    if 'invert' in metrichash.keys():
        invert = data_IO.str2bool(metrichash['invert'])
    else:
        invert = 0

    s = Clip(Input=data_reader)
    s.ClipType = cliptype
    s.ClipType.Origin = camera.GetFocalPoint()
    s.InsideOut = invert
    s.ClipType.Origin = setviewposition(metrichash['position'],camera)
    s.ClipType.Normal = planeNormalFromName(plane)
    sDisplay = Show(s, renderView1)
    sDisplay.ColorArrayName = [None, '']
    sDisplay.SetRepresentationType('Surface')
    sDisplay.DiffuseColor = [0.0, 1.0, 0.0]
    sDisplay.Specular = 0
    sDisplay.Opacity = opacity
    colorMetric(s, metrichash)
    try:
        if metrichash['image'].split("_")[1] == "solo":
            Hide(data_reader, renderView1)
    except:
        pass
    return s


def createProbe(metrichash, data_reader):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    p = ProbeLocation(Input=data_reader, ProbeType='Fixed Radius Point Source')
    p.PassFieldArrays = 1
    #p.ProbeType.Center = [1.2176899909973145, 1.2191989705897868, 1.5207239668816328]
    p.ProbeType.Center = setviewposition(metrichash['position'], camera)
    p.ProbeType.NumberOfPoints = 1
    p.ProbeType.Radius = 0.0
    ps = Sphere(Radius=0.025, ThetaResolution=32)
    ps.Center = setviewposition(metrichash['position'], camera)
    psDisplay = Show(ps, renderView1)
    psDisplay.DiffuseColor = [1.0, 0.0, 0.0]
    psDisplay.Opacity = 0.8
    return p


def createVolume(metrichash, data_reader):
    bounds = [float(x) for x in metrichash['position'].split(" ")]
    renderView1 = GetActiveViewOrCreate('RenderView')
    c = Clip(Input=data_reader)
    c.ClipType = 'Box'
    # (xmin,xmax,ymin,ymax,zmin,zmax)
    #c.ClipType.Bounds = [0.1, 3, 0.1, 2.3, 0.15, 2.3]
    c.ClipType.Bounds = bounds
    c.InsideOut = 1
    cDisplay = Show(c, renderView1)
    cDisplay.ColorArrayName = ['Points', metrichash['field']]
    cDisplay.SetRepresentationType('Surface')
    cDisplay.DiffuseColor = [1.0, 1.0, 0.0]
    cDisplay.Specular = 0
    cDisplay.Opacity = 0.1
    return c

def createBasic(metrichash, dataReader, dataDisplay):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')
    bodyopacity=float(metrichash['bodyopacity'])
    dataDisplay.Opacity = bodyopacity
    dataDisplay.SetRepresentationType('Surface With Edges')

    if not (metrichash['field'] == 'None'):
        colorMetric(dataReader, metrichash)
    else:
        ColorBy(dataDisplay, ('POINTS', ''))
    return dataReader

def plotLine(infile, imageName) :
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    warnings.filterwarnings('ignore')

    header = np.genfromtxt(infile, delimiter=',', names=True).dtype.names
    data = np.genfromtxt(infile, delimiter=',', skip_header=1)

    x = data[:, 0]
    y = data[:, 1]

    plt.figure(figsize=(10, 6))
    plt.plot(x, y)

    locs, labels = plt.yticks()
    plt.yticks(locs, map(lambda x: "%g" % x, locs))

    plt.xlabel('Point')
    plt.ylabel(header[1])
    # plt.title(infile.replace(".csv", "").replace("plot_", "") + ' Plot')
    plt.grid(True)
    plt.savefig(imageName)


def createLine(metrichash, data_reader, outputDir=".", caseNumber=""):
    resolution = int(metrichash['resolution'])
    try:
        image = metrichash['image']
    except:
        image = None

    point = [x for x in metrichash['position'].split()]

    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    if point[0] == "center":
        point[0] = camera.GetFocalPoint()[0]
    if point[3] == "center":
        point[3] = camera.GetFocalPoint()[0]
    if point[1] == "center":
        point[1] = camera.GetFocalPoint()[1]
    if point[4] == "center":
        point[4] = camera.GetFocalPoint()[1]
    if point[2] == "center":
        point[2] = camera.GetFocalPoint()[2]
    if point[5] == "center":
        point[5] = camera.GetFocalPoint()[2]
    
    point1=[float(point[0]),float(point[1]),float(point[2])]
    point2=[float(point[3]),float(point[4]),float(point[5])]
    l = PlotOverLine(Input=data_reader, Source='High Resolution Line Source')
    l.PassPartialArrays = 1
    l.Source.Point1 = point1
    l.Source.Point2 = point2
    l.Source.Resolution = resolution
    lDisplay = Show(l, renderView1)
    lDisplay.DiffuseColor = [1.0, 0.0, 0.0]
    lDisplay.Specular = 0
    lDisplay.Opacity = 1

    # Get the line data
    pl = servermanager.Fetch(l)

    kpifld = metrichash['field']
    kpiComp = metrichash['fieldComponent']
    if (image == "plot"):
        if not (os.path.exists(outputDir)):
            os.makedirs(outputDir)
        if caseNumber:
            metrichash['imageName'] = metrichash['imageName'].format(int(caseNumber))
        imageFullPath = outputDir + '/' + metrichash['imageName']
        imageName, imageExtension = os.path.splitext(imageFullPath)
        csvFileName = imageName + ".csv"
        f=open(csvFileName,"w")
        f.write("point,"+kpifld)
        if kpiComp:
            f.write("_" + kpiComp)
        f.write("\n")

    METRIC_INDEX=0
    for a in range(0,pl.GetPointData().GetNumberOfArrays()):
        if kpifld == pl.GetPointData().GetArrayName(a):
            METRIC_INDEX = a
    sum=0
    num=pl.GetPointData().GetArray(METRIC_INDEX).GetNumberOfTuples()
    # Get the component numbers from the input of line filter (data_reader) (?)
    compNumber = getfldCompNumber(data_reader.PointData[kpifld], kpiComp)
    for t in range(0,num):
        dataPoint = pl.GetPointData().GetArray(METRIC_INDEX).GetTuple(t)[compNumber]
        if str(float(dataPoint)).lower() != "nan":
            sum += dataPoint
        if image == "plot":
            f.write(",".join([str(t), str(dataPoint)])+"\n")
    if image == "plot":
        f.close()
        plotLine(csvFileName, imageFullPath)
    ave = sum/pl.GetPointData().GetArray(METRIC_INDEX).GetNumberOfTuples()
    return l


def adjustCamera(view, renderView1, metrichash):
    camera=GetActiveCamera()
    if view.startswith("iso"):
        camera.SetFocalPoint(0, 0, 0)
        if (view == "iso-flipped"):
            camera.SetPosition(0, 1, 0)
        else:
            camera.SetPosition(0, -1, 0)
        renderView1.ResetCamera()
        # adjust for scale margin
        camera.SetFocalPoint(camera.GetFocalPoint()[0],camera.GetFocalPoint()[1],camera.GetFocalPoint()[2]-0.0025)
        #camera.SetPosition(camera.GetPosition()[0],camera.GetPosition()[1],camera.GetPosition()[2]-1)
        camera.Elevation(45)
        camera.Azimuth(45)
    elif view == "+X" or view == "+x" or view == "back": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(1,0,0)
        renderView1.ResetCamera()
    elif view == "-X" or view == "-x" or view == "front": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(-1,0,0)
        renderView1.ResetCamera()
    elif view == "+Y" or view == "+y" or view == "right": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,1,0)
        renderView1.ResetCamera()
    elif view == "-Y" or view == "-y" or view == "left": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,-1,0)
        renderView1.ResetCamera()
    elif view == "+Z" or view == "+z" or view == "top": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,0,1)
        renderView1.ResetCamera()
        #        camera.Roll(90)
    elif view == "-Z" or view == "-z" or view == "bottom": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,0,-1)
        renderView1.ResetCamera()
        #       camera.Roll(-90)
    elif view == "customize":
        renderView1.InteractionMode = '3D'
        renderView1.CameraPosition   = data_IO.read_floats_from_string(metrichash["CameraPosition"])
        renderView1.CameraFocalPoint = data_IO.read_floats_from_string(metrichash["CameraFocalPoint"])
        renderView1.CameraViewUp = data_IO.read_floats_from_string(metrichash["CameraViewUp"])
        renderView1.CameraParallelScale = float(metrichash["CameraParallelScale"])
        renderView1.CameraParallelProjection = int(metrichash["CameraParallelProjection"])


def makeAnimation(outputDir, kpi, magnification, animationName, deleteFrames=True):
    animationFramesDir = outputDir + '/animFrames'
    if not (os.path.exists(animationFramesDir)):
        os.makedirs(animationFramesDir)

    WriteAnimation(animationFramesDir + "/out_" + kpi + ".png", Magnification=magnification, FrameRate=15.0,
                   Compression=False)

    subprocess.call(["convert", "-delay", "15",  "-loop",  "0", "-limit", "memory", "2MB", "-limit", "map","2MB","-verbose",
                     animationFramesDir + "/out_" + kpi + ".*.png",
                     outputDir + "/" + animationName])

    if deleteFrames:
        shutil.rmtree(animationFramesDir)


def exportx3d(outputDir,kpi, metricObj, dataReader, renderBody, blenderContext):

    blenderFramesDir = outputDir + kpi + '_blender'

    if not (os.path.exists(blenderFramesDir)):
        os.makedirs(blenderFramesDir)

    try:
        TimeSteps = getTimeSteps()
        firstTimeStep = TimeSteps[0]
        renderView1 = GetActiveViewOrCreate('RenderView')
        renderView1.ViewTime = firstTimeStep
        for num, time in enumerate(TimeSteps):
            name_solo = blenderFramesDir + '/' + str(num) + '_solo.x3d'
            Show(metricObj, renderView1)
            Hide(dataReader, renderView1)
            ExportView(name_solo, view=renderView1)
            if renderBody == "true":
                name_body = blenderFramesDir + '/' + str(num) + '_body.x3d'
                Show(dataReader, renderView1)
                Hide(metricObj, renderView1)
                ExportView(name_body, view=renderView1)
            animationScene1 = GetAnimationScene()
            animationScene1.GoToNext()
    except:
        renderView1 = GetActiveViewOrCreate('RenderView')
        name_body = blenderFramesDir + '/' + 'body.x3d'
        Show(dataReader, renderView1)
        ExportView(name_body, view=renderView1)
        
    if blenderContext != None and len(blenderContext) > 0:
        for i in blenderContext:
            dataReaderTmp = readDataFile(i, None)
            renderViewTmp = CreateView('RenderView')
            readerDisplayTmp = Show(dataReaderTmp, renderViewTmp)
            name_body = blenderFramesDir + '/' + os.path.splitext(os.path.basename(i))[0] + '.x3d'
            ExportView(name_body, view=renderViewTmp)

    # tar the directory
    data_IO.tarDirectory(blenderFramesDir + ".tar", blenderFramesDir)
    shutil.rmtree(blenderFramesDir)

def saveSTLfile(renderView,filename,magnification,quality):
    adjustCamera("iso", renderView, None, "false")
    SaveScreenshot(filename, magnification=magnification, quality=quality)
    
