#!/usr/bin/env python
"""Get GDAL paths to individual bands in an HDF file (expects piped input from gdalinfo)

Prints space-delimted:
    Full path to band ('filename:band' format)
    OR
    Band name only

Used to create input for 'gdalbuildvrt -separate', or 'setBandDescr.py'

Usage:
    gdalbuildvrt -separate MYD11A1.A2022002.h14v16.061.vrt $( gdalinfo MYD11A1.A2022002.h14v16.061.hdf | mw-hdfeosgetbands.py )
    THEN
    mw-setbanddescr.py MYD11A1.A2022002.h14v16.061.vrt -d $( gdalinfo MYD11A1.A2022002.h14v16.061.hdf | mw-hdfeosgetbands.py --bandnames )
"""

import sys, re
import argparse

# lambdas


# constants


# argparse
parser = argparse.ArgumentParser(description="Get GDAL paths to individual bands in an HDF file (expects piped input from gdalinfo)")
parser.add_argument('--bandnames', action='store_true')
args = parser.parse_args()

# code
re_dsname = re.compile(r'^\s+SUBDATASET_\d+_NAME=(.*)$')
for line in sys.stdin:
    for match in re_dsname.findall(line):
        if args.bandnames:
            print(match.split(':')[-1], end=' ')
        else:
            print(match, end=' ')
        break

print('')
