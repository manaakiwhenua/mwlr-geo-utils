#!/usr/bin/env python
"""Set band descriptions in gdal image file and optionally calculate stats and pyrimids

Usage: 
    mw-setbanddescr.py [-h] [-s] [-i ignore] [-p] file.vrt [file.vrt ...] [-d B01 [B02 ...]]

Author:   D.Pairman  21 Jul 2016
"""
# Author: David Pairman

from osgeo import gdal, ogr
from osgeo.gdalconst import *
import argparse
import xml.etree.ElementTree as ET
from rios import calcstats, cuiprogress

gdal.PushErrorHandler('CPLQuietErrorHandler')
ogr.UseExceptions()

def getBandDescr(imgName, suppressprint=False):
    if not suppressprint:
       print('Reading bands from', imgName)
    bandNames = []
    imgFile = gdal.Open(imgName, gdal.GA_ReadOnly)
    for ibnd in range(imgFile.RasterCount):
        bandNames.append(imgFile.GetRasterBand(ibnd+1).GetDescription())

    return bandNames

def setBandDescr( imgName, descr=[], stats=False, ignore=None, pyramids=False ):
    print('Updating: '+imgName)
    # Open the image (for update)
    imgFile = gdal.Open(imgName, gdal.GA_Update)
    imgBands = imgFile.RasterCount

    if len(descr) > 0:
      if len(descr) != imgBands:
        print("Error - image bands: {}, while {} descriptors supplied".format(imgBands, len(descr)))
        exit(1)
      else:
        for bnd in [i+1 for i in range(imgBands)]:
          description = imgFile.GetRasterBand(bnd).GetDescription()
          imgBand = imgFile.GetRasterBand(bnd)
          imgBand.SetDescription(descr[bnd-1])

    if stats: 
      #calcstats.calcStats(imgFile, ignore=0.0)
      print("Ignoring: {}".format(ignore))
      progress = cuiprogress.CUIProgressBar()
      calcstats.addStatistics(imgFile, progress, ignore)

    if pyramids:
      progress = cuiprogress.CUIProgressBar()
      calcstats.addPyramid(imgFile, progress)

    imgFile = None


# Main program - Just parses arguments
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputImage", nargs='+',
                        help="input gdal image file")
    parser.add_argument("-f", "--fromImage", type=str, default=None,
                        help="Copy band names from this file")
    parser.add_argument("-b", "--bandsFromImage", nargs='*', type=int, default=[],
                        help="Only copy THESE band names from file")
    parser.add_argument("-d", "--description", nargs='*', type=str, default=[],
                        help="Band description(s) (in order)")
    parser.add_argument("-s", "--stats", help="calculate statistics", action="store_true")
    parser.add_argument("-i", "--ignore", type=int, nargs='?', const=None, default=0,
                        help="ignore value for stats (def=0, -i alone for None)")
    parser.add_argument("-p", "--pyramids", help="calculate pyramid layers", action="store_true")
    parser.add_argument("--read", action='store_true', help="read and print band names to stdout")
    parser.add_argument("--readnumbers", action='store_true', help="read and print band numbers to stdout")
    
    args = parser.parse_args()

    if args.fromImage is not None:
        description = getBandDescr(args.fromImage)

        if len(args.bandsFromImage) > 0:
           args.description = [ description[i-1] for i in args.bandsFromImage ]
        else:
           args.description = description

    if args.read or args.readnumbers:
      bands = []

      for img in args.inputImage:
        bands += getBandDescr(img, suppressprint=True)

      if args.readnumbers:
        print(' '.join([str(i) for i in range(1,len(bands)+1)]))
      else:
        print(' '.join(bands))
    else:
      for img in args.inputImage:
        setBandDescr(img,
                    descr = args.description,
                    stats = args.stats,
                    ignore = args.ignore,
                    pyramids = args.pyramids)
