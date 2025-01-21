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
import importlib.util

def import_module_from_file(file_path):
    spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

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
parser.add_argument('--copybandnames', action='store_true', default=False)
parser.add_argument('--referenceimage', type=Path, default=None)
parser.add_argument('--footprint', type=str, default='UNION', help="controls.footprint setting - choose UNION (default), INTERSECTION, or BOUNDS_FROM_REFERENCE")
parser.add_argument('--windowsize', type=int, default=512, help='')
parser.add_argument('--calcfile', type=Path, default=None, help='Path to a Python file to import, must contain an apply function, not compatible with --calc')
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
    assert not args.copybandnames
    controls.layernames = args.bandnames # ['LST_Day_1km', 'LST_Night_1km']

if args.dstnodata is not None:
    controls.statsignore = int(args.dstnodata) if '.' not in args.dstnodata else np.nan if args.dstnodata == "np.nan" else float(args.dstnodata)
else:
    controls.statsignore = finfo.nodataval

if args.referenceimage is not None:
    assert args.referenceimage.exists()
    controls.referenceImage = args.referenceimage.as_posix()

if args.copybandnames and len(args.rasters) > 1:
    print("""WARNING: --copybandnames is set but you have more than 1 input raster,
    defaulting to the band names of the first one""")

controls.footprint = getattr(applier, args.footprint, None)
controls.windowxsize, controls.windowysize = args.windowsize, args.windowsize
print("WINSIZE", controls.windowxsize, controls.windowysize)

# rios files
infiles.rasters = [x.as_posix() for x in args.rasters]
outfiles.result = args.result.as_posix()
#print('IN:',infiles.raw)
print('OUT:',outfiles.result)

otherargs.formula = args.calc
otherargs.calcmask = args.calcmask
otherargs.nodata = controls.statsignore

if args.calcfile is not None:
    assert args.calcfile.exists()
    calcfile = import_module_from_file(args.calcfile.as_posix())
else:
    calcfile = None
    
# rios apply function
def apply(info, ins, outs, others):
    outs.result = eval(others.formula, {"rasters": ins.rasters, "np": np})
    
    if others.calcmask is not None:
        outs.result[eval(others.calcmask, {"rasters": ins.rasters, "np": np, "result": outs.result})] = others.nodata

# rios execute 
applier.apply(apply if calcfile is None else calcfile.apply, infiles, outfiles, otherargs, controls=controls)

if args.copybandnames:
    from osgeo import gdal
    src_ds = gdal.Open(args.rasters[0].as_posix())
    dst_ds = gdal.Open(args.result.as_posix(), gdal.GA_Update)

    for i in range(1, src_ds.RasterCount + 1):
        src_band = src_ds.GetRasterBand(i)
        dst_band = dst_ds.GetRasterBand(i)
        dst_band.SetDescription(src_band.GetDescription())

    src_ds = None
    dst_ds = None

print("Done")
