#!/usr/bin/env python
"""Create a polygon from image file extents

Written by James Shepherd
"""

import os, re
from osgeo import ogr
from osgeo import osr
import argparse

def write_to_file(args, lines):
    drv = ogr.GetDriverByName(args.f)

    ds = drv.CreateDataSource(args.outfn)
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(2193)
    lyr = ds.CreateLayer("ext_to_poly", sr, ogr.wkbPolygon)

    field_defn = ogr.FieldDefn("Name", ogr.OFTString)
    lyr.CreateField(field_defn)
   

    for line in lines:
        ext = line[:4]
        
        feat = ogr.Feature(lyr.GetLayerDefn())
        feat.SetField("Name", line[-1])

        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(ext[0], ext[1])
        ring.AddPoint(ext[2], ext[1])
        ring.AddPoint(ext[2], ext[3])
        ring.AddPoint(ext[0], ext[3])
        ring.AddPoint(ext[0], ext[1])

        # Create polygon
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        feat.SetGeometry(poly)
        lyr.CreateFeature(feat)
        feat.Destroy()
        
    ds.Destroy()
    
parser = argparse.ArgumentParser()
parser.add_argument("-infn", help="-infn filename  : white-space separated extents, format: tl_x tl_y br_x br_y [optional name]", default=None)
parser.add_argument("-outfn", help="-outfn filename  : default 'temp.kml'", default='temp.gml')
parser.add_argument("-f", help="-f \"OGR Format\" : default GML", default='GML')
parser.add_argument("-separate", help="-separate : create file for each line of input : default False", action='store_true', default=False)

args = parser.parse_args()

readfromfile = True if args.infn else False

if os.path.exists(args.outfn):
    os.remove(args.outfn)

lines = None
if readfromfile:
    with open(args.infn, 'r') as handle:
        lines = handle.readlines()
        
else:
    lines = []
    print('Manual input (q to quit at any time)')
    while True:
        try:
            a = input('tl_x tl_y br_x br_y [name - optional]')
            if a.endswith('q'):
                raise Exception()
            else:
                lines.append(a)
                
        except Exception as ex:
            print(ex)
            if input('Continue? (y|n) [n]') != 'y':
                break

#get and split lines of extents to read
lines = (re.split('\s+', x.strip()) for x in lines)
#skip any that aren't the right length (useful for leading/tailing blanks)
lines = (line for line in lines if len(line) in [4,5])
#make names up (based in line idx) for lines that don't have names
lines = (line if len(line) == 4 else (line + ['f'+str(i)]) for i, line in enumerate(lines))
#convert the extents to float
lines = [[float(x) for x in line[:4]] + [line[4]] for i, line in enumerate(lines)]

if args.separate:
    orig_out = os.path.splitext(args.out)
    
    for line in lines:
        args.outfn = '{0}.{1}.{2}'.format(orig_out[0], line[-1], orig_out[1])
        write_to_file(args, [line])
else:
    write_to_file(args, lines)

print("Done")
