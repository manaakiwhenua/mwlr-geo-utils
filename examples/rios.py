#!/usr/bin/env python

import argparse
from pathlib import Path

import numpy as np

from rios import applier, cuiprogress, fileinfo

np.seterr(invalid='ignore')

parser = argparse.ArgumentParser()
parser.add_argument('raster1', type=Path)
parser.add_argument('raster2', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--cloud', type=Path, default=None)
parser.add_argument('--mask', type=Path, default=None)
args = parser.parse_args()

info = fileinfo.ImageInfo(args.raster1.as_posix())

controls = applier.ApplierControls()
infiles = applier.FilenameAssociations()
outfiles = applier.FilenameAssociations()
otherargs = applier.OtherInputs()

controls.drivername = 'KEA'
controls.calcStats = True
controls.progress = cuiprogress.GDALProgressBar()
controls.referenceImage = args.image.as_posix()
#controls.layernames = ["Red", "Green", "Blue"]
controls.statsIgnore = np.nan

# use info.nrows/ncols to set rios window size to entire image
controls.windowxsize=256#info.nrows
controls.windowysize=256#info.ncols

print("WINSIZE", controls.windowxsize, controls.windowysize)
#print("EST RAM", controls.windowxsize * controls.windowysize * 6 * 4 * 1.5 * (1 / 1024 / 1024), 'MB')

infiles.raster1 = args.raster1.as_posix()
infiles.raster2 = args.raster2.as_posix()

otherargs.cloud = args.cloud is not None and args.cloud
if otherargs.cloud:
    infiles.cloud = args.cloud.as_posix()

otherargs.mask = args.mask is not None
if otherargs.mask:
    infiles.mask = args.mask.as_posix()

outfiles.output = args.output.as_posix()

print('IN  - RASTER1:',infiles.raster1)
print('IN  - RASTER2:',infiles.raster2)
print('IN  - MASK:',infiles.mask if otherargs.mask else "NONE")
print('IN  - CLOUD:',infiles.cloud if otherargs.cloud else "NONE")

print('OUT - OUTPUT:', outfiles.indices)

def apply(info, ins, outs, others):

    outs.output = np.zeros((13, ) + ins.raster1.shape[1:], dtype=float)

    valid = np.ones_like((1,) + ins.raster1.shape[1:], dtype=bool)

    if others.mask:
        valid *= ins.mask == 1
    
    if otherargs.cloud:
        valid *= ins.cloud == 1

    if not valid.any():
        outs.output[:] = np.nan
        return
    
    outs.output = ins.raster1 + ins.raster2
    outs.output *= valid

applier.apply(apply, infiles, outfiles, otherargs, controls=controls)

print("Done")
