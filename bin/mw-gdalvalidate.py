#!/usr/bin/env python
"""Use GDAL to 'validate' input raster(s) by checking for file corruption

Very simple script, attempt open each raster and print the names of the ones that passed
Optionally delete those that don't pass (--delete)

Usage:
    VALID=$( mw-gdalvalidate.py /path/to/*.kea )
    OR
    mw-gdalvalidate.py --delete /path/to/*.kea
"""
# Author: Ben Jolly

import sys
from osgeo import gdal
from pathlib import Path
import argparse

gdal.UseExceptions()

# lambdas

# argparse
parser = argparse.ArgumentParser()
parser.add_argument('rasters', type=Path, nargs='+')
parser.add_argument('--delete', action='store_true', help="Delete any rasters that fail validation")
args = parser.parse_args()

valid_rasters = []
for raster in args.rasters:
    try:
        ds = gdal.Open(raster.as_posix())
        del ds
    except RuntimeError as ex:
        print("BAD FILE:", raster, '(DELETING...)' if args.delete else '(skipping)', file=sys.stderr)
        if args.delete:
            raster.unlink()
    else:
        valid_rasters.append(raster.as_posix())

print(' '.join(valid_rasters))