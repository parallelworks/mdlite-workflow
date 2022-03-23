import data_IO
import json
import warnings

from collections import OrderedDict


def readKPIJsonFile(kpiFile):
    fp_jsonIn = data_IO.open_file(kpiFile)
    kpihash = json.load(fp_jsonIn, object_pairs_hook=OrderedDict)
    orderPreservedKeys = data_IO.byteify(list(kpihash.keys()))
    kpihash = data_IO.byteify(kpihash)
    fp_jsonIn.close()
    return kpihash, orderPreservedKeys


def setKPIFieldDefaults(metrichash, kpi, caseNumber=""):

    # Set component to "Magnitude" if not given for vector/tensor fields
    if not ('field' in metrichash):
        metrichash['field'] = 'None'
        metrichash['fieldComponent'] = 'None'

    if not ('IsParaviewMetric' in metrichash):
        metrichash['IsParaviewMetric'] = 'True'

    if not ('DEXoutputFlag' in metrichash):
        if data_IO.str2bool(metrichash['IsParaviewMetric']):
            metrichash['DEXoutputFlag'] = 'all'
        else:
            metrichash['DEXoutputFlag'] = ''

    # If not a Paraview Metric, make sure the information for extracting
    # data/images from a generic file is provided.
    if not data_IO.str2bool(metrichash['IsParaviewMetric']):
        if metrichash['DEXoutputFlag'].lower() == "image":
            if not ('imageName' in metrichash):
                metrichash['imageName'] = "out_" + kpi + ".png"

        if metrichash['DEXoutputFlag'].lower() == "animation":
            if not ('animation' in metrichash):
                metrichash['animation'] = 'True'
            if not data_IO.str2bool(metrichash['animation']):
                warnings.warn('Setting {}.animation to True'.format(kpi))
                metrichash['animation'] = 'True'
            if not ('animationName' in metrichash):
                metrichash['animationName'] = "out_" + kpi + ".gif"
        else:
            metrichash['animation'] = 'False'

        if not(metrichash['DEXoutputFlag'].lower() in {"none", "image", "animation"}):
            if not ('resultFile' in metrichash):
                warningMsg = 'Please provide resultFile for {}. Setting ' \
                             '{}.DEXoutputFlag to "none".'.format(kpi, kpi)
                warnings.warn(warningMsg)
                metrichash['DEXoutputFlag'] = 'none'
            if not ("delimiter" in metrichash):
                metrichash["delimiter"] = ""
            if not ("locationInFile" in metrichash):
                metrichash["locationInFile"] = "1"
        return metrichash

    # Set default image properties
    if not ('image' in metrichash):
        metrichash['image'] = 'None'
        metrichash['imageName'] = 'None'
    if not ('bodyopacity' in metrichash):
        metrichash['bodyopacity'] = "0.3"
    if not ('min' in metrichash):
        metrichash['min'] = 'auto'
    if not ('max' in metrichash):
        metrichash['max'] = 'auto'
    if not ('discretecolors' in metrichash):
        metrichash['discretecolors'] = '20'
    if not ('colorscale' in metrichash):
        metrichash['colorscale'] = 'Blue to Red Rainbow'
    if not ('invertcolor' in metrichash):
        metrichash['invertcolor'] = 'False'
    if not ('opacity' in metrichash):
        metrichash['opacity'] = "1"

    # Set image name
    if not('image' == 'None'):
        if not ('imageName' in metrichash):
            if metrichash['image'] == "plot":
                metrichash['imageName'] = "plot_" + kpi + ".png"
            else:
                #metrichash['imageName'] = "out_" + kpi + ".png"
                metrichash['imageName'] = kpi + ".gif"

    # Set default streamline properties
    if metrichash['type'] == "StreamLines":
        if not ('seedType' in metrichash):
            metrichash['seedType'] = 'Line'

    if not('extractStats' in metrichash):
        if metrichash['field'] == 'None':
            metrichash['extractStats'] = 'False'
        else:
            metrichash['extractStats'] = 'True'

    if not data_IO.str2bool(metrichash['extractStats']):
        metrichash['DEXoutputFlag'] = 'none'

    if not ('animation' in metrichash):
        metrichash['animation'] = 'False'

    if data_IO.str2bool(metrichash['animation']):
        if not ('animationName' in metrichash):
            metrichash['animationName'] = "out_" + kpi + ".gif"

    if not ('blender' in metrichash):
        metrichash['blender'] = 'False'
    else:
        try:
            metrichash['blendercontext'] = metrichash['blendercontext'].split(",")
        except:
            metrichash['blendercontext'] = []
        try:
            metrichash['blenderbody'] = metrichash['blenderbody'].split(",")
        except:
            metrichash['blenderbody'] = False

    return metrichash
