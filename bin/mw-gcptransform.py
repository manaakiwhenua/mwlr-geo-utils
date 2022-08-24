#!/usr/bin/env python
"""Transform all GCPS in a raster to a different SRS (ie EPSG 4326 -> EPSG 3031)

Usage:
    mw-gcptransform.py my.tif 3031
    OR
    mw-gcptransform.py my.tif 3031 --output my_transformed.tif
"""
# Author: Ben Jolly

import shutil
from osgeo import gdal, osr
import argparse

def transform_GCP(gcp, transform):
    """ Create a transformed copy of a osgeo.gdal.GCP"""
    x, y, z = transform.TransformPoint(gcp.GCPY, gcp.GCPX, gcp.GCPZ)
    return gdal.GCP(x, y, z, gcp.GCPPixel, gcp.GCPLine)

def str_to_SRS(srs_str):
    """Convert a Proj4 or WKT string, or EPSG code, into an osgeo.osr.SpatialReference """
    srs = osr.SpatialReference()

    if '+proj' in srs_str.lower():
        srs.ImportFromProj4(srs_str)
    elif 'epsg' in srs_str.lower() or len(srs_str) == 4:
        srs.ImportFromEPSG(int(srs_str.strip()[-4:]))
    else:
        srs.ImportFromWKT(srs_str)

    return srs

def transform_all_GCPs(raster, tgt_srs):
    """Read all GCPs from raster, transform them, the write them back"""
    ds = gdal.Open(raster, gdal.GA_Update)
    original_GCPs = ds.GetGCPs()
    
    if len(original_GCPs) == 0:
        print("WARNING: No GCPs found in file, skipping:", raster)
    else:
        src_srs = osr.SpatialReference()
        src_srs.ImportFromWkt(ds.GetGCPProjection())
        if src_srs.IsSame(tgt_srs) == 1:
            print("WARNING: New SRS is the same as the current GCP SRS, skipping:", raster)
        else:
            transform = osr.CoordinateTransformation(src_srs, tgt_srs)
            transformed_GCPs = [transform_GCP(gcp, transform) for gcp in original_GCPs]
            ds.SetGCPs(transformed_GCPs, tgt_srs)
            print("Transformed GCPs in", raster)

    del ds

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Transform all GCPS in a raster to a different SRS (ie EPSG 4326 -> EPSG 3031)")
    parser.add_argument('raster')
    parser.add_argument('t_srs', help="Target SRS (EPSG code, PROJ4 string, or WKT)")
    parser.add_argument('--output', default=None, help="Copy raster and modify this one instead")
    args = parser.parse_args()

    if args.output is not None:
        shutil.copyfile(args.raster, args.output)
        args.raster = args.output

    transform_all_GCPs(args.raster, str_to_SRS(args.t_srs))