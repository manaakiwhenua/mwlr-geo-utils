#!/usr/bin/env python
"""Get extent of a GDAL raster (image) as xmin ymin xmax ymax

Optionally print ulx uly lrx lry
Optionally buffer it (with -tap option)

Optionally write result to an OGR vector file

Usage:
    mw-extent.py ~/nz_sen2_arefs_1920_100m.kea
    OR (create KML)
    mw-extent.py ~/nz_sen2_arefs_1920_100m.kea --output ~/nz_sen2_arefs_1920_100m.kml -of KML --epsg 4326
"""
# Author: Ben Jolly

import argparse
import math

"""The following block is borrowed/modified from StackExchange

https://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings
"""
from osgeo import gdal,ogr,osr
def GetExtent(image, buffer=0, tap=False, epsg=None):
    """ Return list of corner coordinates from a gdal Dataset (ul ur lr ll) """
    ds = gdal.Open(image)
    
    src_srs=osr.SpatialReference()
    src_srs.ImportFromWkt(ds.GetProjection())

    xmin, xpixel, _, ymax, _, ypixel = ds.GetGeoTransform()
    width, height = ds.RasterXSize, ds.RasterYSize
    xmax = xmin + width * xpixel
    ymin = ymax + height * ypixel

    if buffer != 0:
        xmin, ymin, xmax, ymax = xmin - buffer, ymin - buffer, xmax + buffer, ymax + buffer

    if tap:
        x_abs, y_abs = abs(xpixel), abs(ypixel)
        xmin = math.floor(xmin / x_abs) * x_abs
        ymin = math.floor(ymin / y_abs) * y_abs
        xmax = math.ceil(xmax / x_abs) * x_abs
        ymax = math.ceil(ymax / y_abs) * y_abs

    #              ul            ur            lr            ll
    corners = (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)
    
    if epsg is None:
        tgt_srs = src_srs.CloneGeogCS()
    else:
        tgt_srs = osr.SpatialReference()
        tgt_srs.ImportFromEPSG(epsg)
                
        corners = ReprojectCoords(corners, src_srs, tgt_srs)

    return corners, tgt_srs
        
def ReprojectCoords(coords,src_srs,tgt_srs):
    """ Reproject a list of x,y coordinates. """
    trans_coords=[]
    transform = osr.CoordinateTransformation( src_srs, tgt_srs)
    for x,y in coords:
        x,y,z = transform.TransformPoint(x,y)
        trans_coords.append([x,y])
    return trans_coords


"""StackExchange block done"""


def create_vector(corners, srs, vector_file, format, layer_name, feature_name):
    """Create a polygon from a set of corner and write to an OGR vector file"""
    drv = ogr.GetDriverByName(format)
    ds = drv.CreateDataSource(vector_file)
    lyr = ds.CreateLayer(layer_name, srs, ogr.wkbPolygon)

    field_defn = ogr.FieldDefn("Name", ogr.OFTString)
    lyr.CreateField(field_defn)

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("Name", feature_name)

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(corners[0][0], corners[0][1])
    ring.AddPoint(corners[1][0], corners[1][1])
    ring.AddPoint(corners[2][0], corners[2][1])
    ring.AddPoint(corners[3][0], corners[3][1])
    ring.AddPoint(corners[0][0], corners[0][1])

    # Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    feat.SetGeometry(poly)
    lyr.CreateFeature(feat)
    feat.Destroy()

    ds.Destroy()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Get geospatial extent of image (xmin ymin xmax ymax)")
    parser.add_argument("image")
    parser.add_argument("--buffer", type=float, default=0, help="Buffer extent by this amount (CRS units)")
    parser.add_argument("--ullr", action='store_true', help="Report 'ulx uly lrx lry' instead (for gdal_translate)")
    parser.add_argument("--output", default=None, help="Create polygon of (buffered?) extent and save to file")
    parser.add_argument("-of", default="GML", help="Format of --output [default GML]")
    parser.add_argument("--epsg", type=int, default=None, help="EPSG code for output [default: same as input]")
    parser.add_argument("-tap", action='store_true', help="Target align pixels (make sure extent snaps to pixel size of raster)")
    args = parser.parse_args()

    #NOTE: corners format is [ul ur lr ll] OR [(xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)]
    c, srs = GetExtent(args.image, buffer=args.buffer, tap=args.tap, epsg=args.epsg)

    if args.output is not None:
        create_vector(c, srs, args.output, args.of, "mw-extent", args.image.split('/')[-1])

    if args.ullr:
        print(f"{c[0][0]} {c[0][1]} {c[2][0]} {c[2][1]}")
    else:
        print(f"{c[3][0]} {c[3][1]} {c[1][0]} {c[1][1]}")

