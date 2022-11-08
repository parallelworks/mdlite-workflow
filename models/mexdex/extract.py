from paraview.simple import *
import json
import sys
import pvutils
import metricsJsonUtils
import data_IO
import os

print(sys.argv)
if len(sys.argv) < 5:
    print("Number of provided arguments: ", len(sys.argv) - 1)
    print("Usage: pvpython extract.py  <dataFile>  <desiredMetrics.json> <outputDir> "
          "<outputMetrics.csv> [caseNumber]")
    sys.exit()


dataFileAddress = sys.argv[1]
kpiFileAddress = sys.argv[2]
outputDir = sys.argv[3]
metricFile = sys.argv[4]
caseNumber = data_IO.setOptionalSysArgs(sys.argv, "", 5)

# Image settings:
magnification = 1
viewSize = [700, 600]
backgroundColor = [1, 1, 1]   # set background color to white

# Read the desired outputs/metrics from the csv file:
kpihash = metricsJsonUtils.readKPIJsonFile(kpiFileAddress)[0]

print(kpihash)

# disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# Read data file
data2Read = pvutils.getfieldsfromkpihash(kpihash)
dataReader = pvutils.readDataFile(dataFileAddress, data2Read)

# Initialize renderView and display
renderView1, readerDisplay = pvutils.initRenderView(dataReader, viewSize,
                                                    backgroundColor)

print("Generating KPIs")

# Set the default values for missing fields in the kpihash
for kpi in kpihash:
    kpihash[kpi] = metricsJsonUtils.setKPIFieldDefaults(kpihash[kpi], kpi)
    if not (kpihash[kpi]['field'] == 'None'):
        kpihash[kpi] = pvutils.correctfieldcomponent(dataReader, kpihash[kpi])

fp_csv_metrics = data_IO.open_file(metricFile, "w")
fp_csv_metrics.write(",".join(['metric','ave','min','max','sd'])+"\n")

renderView1.InteractionMode = '2D'
renderView1.OrientationAxesVisibility = 0

for kpi in kpihash:
    if not data_IO.str2bool(kpihash[kpi]['IsParaviewMetric']):
        continue
    metrichash = kpihash[kpi]
    kpitype = metrichash['type']
    kpifield = metrichash['field']
    kpiComp = metrichash['fieldComponent']
    kpiimage = metrichash['image']
    extractStats = data_IO.str2bool(metrichash['extractStats'])
    makeAnim = data_IO.str2bool(metrichash['animation'])
    export2Blender = data_IO.str2bool(metrichash['blender'])

    HideAll()
    Show(dataReader, renderView1)
    if kpiimage != "None" and kpiimage != "plot":
        pvutils.adjustCamera(kpiimage, renderView1, metrichash)
    
    print(kpi)
    
    ave = []
    if kpitype == "Slice":
        d = pvutils.createSlice(metrichash, dataReader, readerDisplay)
    elif kpitype == "Clip":
        d = pvutils.createClip(metrichash, dataReader, readerDisplay)
    elif kpitype == "Probe":
        d = pvutils.createProbe(metrichash, dataReader)
    elif kpitype == "Line":
        d = pvutils.createLine(metrichash, dataReader, outputDir, caseNumber)
    elif kpitype == "StreamLines":
        d = pvutils.createStreamTracer(metrichash, dataReader, readerDisplay)
    elif kpitype == "Volume":
        d = pvutils.createVolume(metrichash, dataReader)
    elif kpitype == "Basic":
        d = pvutils.createBasic(metrichash, dataReader, readerDisplay)

    if extractStats:
        pvutils.extractStats(d, kpi, kpifield, kpiComp, kpitype, fp_csv_metrics)

    if kpiimage != "None" and kpiimage != "plot":
        if not (os.path.exists(outputDir)):
            os.makedirs(outputDir)
        if caseNumber:
            metrichash['imageName'] = metrichash['imageName'].format(int(caseNumber))
        SaveScreenshot(outputDir + '/' + metrichash['imageName'],
                       magnification=magnification, quality=100)

    if makeAnim:
        #animationName = metrichash['animationName']
        animationName = "out_"+kpi+".gif"
        if caseNumber:
            animationName = animationName.format(int(caseNumber))

        pvutils.makeAnimation(outputDir, kpi, magnification, animationName)

    if export2Blender:
        blenderContext=metrichash['blendercontext']
        renderBody=metrichash['blenderbody']
        pvutils.exportx3d(outputDir, kpi, d, dataReader, renderBody, blenderContext)

fp_csv_metrics.close()
