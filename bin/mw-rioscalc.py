#!/usr/bin/env python
"""Run rios.applier 'apply()' over image(s) to perform user calculations

Available libraries are:
    import numpy as np

--calc should eval() to a 3D numpy array (band, x, y), inputs are available 
    from the 3D (1 image) or 4D (multiple images) ndarray 'rasters' ([image,] band, x, y)

Usage:
    mw-rioscalc.py --calc "np.nanmean(rasters, axis=0)" result.kea /path/to/*.kea --bandnames band_a band_b
"""
import sys
import argparse
import re
from pathlib import Path
import numpy as np
from rios import applier, cuiprogress, fileinfo

np.seterr(invalid='ignore')

# lambdas
getdate = lambda x: re.findall('_(\\d{6})_', x)[0]

# argparse
parser = argparse.ArgumentParser()
parser.add_argument('result', type=Path)
parser.add_argument('rasters', type=Path, nargs='+')
parser.add_argument('--calc', type=str, default="np.nanmean(rasters, axis=0)", help="Formula to apply, raster(s) available np array 'rasters', numpy is available as 'np'")
parser.add_argument('--calcmask', type=str, default=None, help="Mask formula to apply, raster(s) available np array 'rasters', numpy is available as 'np'")
parser.add_argument('-of', type=str, default='KEA')
parser.add_argument('--nostats', action='store_true', help='Do NOT calculate pyramids/stats')
parser.add_argument('--dstnodata', type=str, help="Destination NODATA value (either a number or 'np.nan'")
parser.add_argument('--bandnames', nargs='+', default=None)
args = parser.parse_args()

# rios
controls = applier.ApplierControls()
infiles = applier.FilenameAssociations()
outfiles = applier.FilenameAssociations()
otherargs = applier.OtherInputs()

finfo = fileinfo.ImageInfo(args.rasters[0].as_posix())

# rios options
controls.drivername = args.of
controls.calcStats = not args.nostats
controls.progress = cuiprogress.GDALProgressBar()
if args.bandnames is not None:
    controls.layernames = args.bandnames # ['LST_Day_1km', 'LST_Night_1km']

if args.dstnodata is not None:
    controls.statsignore = int(args.dstnodata) if '.' not in args.dstnodata else np.nan if args.dstnodata == "np.nan" else float(args.dstnodata)
else:
    controls.statsignore = finfo.nodataval
print("WINSIZE", controls.windowxsize, controls.windowysize)

# rios files
infiles.rasters = [x.as_posix() for x in args.rasters]
outfiles.result = args.result.as_posix()
#print('IN:',infiles.raw)
print('OUT:',outfiles.result)

otherargs.formula = args.calc
otherargs.calcmask = args.calcmask
otherargs.nodata = controls.statsignore

# rios apply function
def apply(info, ins, outs, others):
    outs.result = eval(others.formula, {"rasters": ins.rasters, "np": np})
    
    if others.calcmask is not None:
        outs.result[eval(others.calcmask, {"rasters": ins.rasters, "np": np, "result": outs.result})] = others.nodata

# rios execute
applier.apply(apply, infiles, outfiles, otherargs, controls=controls)

print("Done")
