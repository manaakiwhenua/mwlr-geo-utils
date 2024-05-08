#!/usr/bin/env python
"""Calculate 'Zonal Stats' from a raster for polygons in a given vector
"""
# Author: Jan Schindler

import argparse

from tqdm import tqdm

import numpy as np
from scipy import stats
import geopandas as gpd

import rasterio as rio
from rasterio import features
from rasterio.transform import from_origin
from rasterio import windows


def np_stats(data: np.ndarray, metric: str) -> np.ndarray:
    results = []
    if data.ndim == 1:
        axis = 0
    elif data.ndim == 2:
        axis = 1
    elif data.ndim == 3:
        axis = (1, 2)

    for metric in metric:
        if metric in ['mean', 'std', 'median', 'var', 'sum', 'max', 'min']:
            result = getattr(np, f'nan{metric}')(data, axis=axis)
        elif 'mode' in metric:
            result = stats.mode(data.ravel())[0]
        elif 'perc' in metric:
            result = np.nanpercentile(data, int(metric.replace('perc', '')), axis=axis)
        elif 'quant' in metric:
            result = np.nanquantile(data, int(metric.replace('perc', '')), axis=axis)
        elif metric == 'count':
            result = (~np.isnan(data)).sum(axis=axis)
        else:
            raise Exception(f'Metric {metric} not defined.')
        results.append(result)
        #print(result.shape)
    return np.concatenate(results)



def calc_stats(rio_image, df_row, bands, metrics, buffer, ignore):
    geom = df_row.geometry
    if buffer:
        geom = geom.buffer(buffer)
    
    if np.isnan(geom.bounds).any():
        print('WARN: Empty/invalid geometry')
        data = np.zeros((len(bands), 1, 1), dtype=float)
        data[:] = np.nan
    else:
        res = rio_image.res[0]
        xmin, ymin, xmax, ymax = geom.bounds
        row_offset = np.floor((rio_image.bounds.top - ymax) / res).astype(int)
        col_offset = np.floor((xmin - rio_image.bounds.left) / res).astype(int)
        height = (np.ceil((rio_image.bounds.top - ymin) / res) - row_offset).astype(int)
        width  = (np.ceil((xmax - rio_image.bounds.left) / res) - col_offset).astype(int)

        adj_ymax = rio_image.bounds.top - (res * np.floor((rio_image.bounds.top - ymax) / res))
        adj_xmin = rio_image.bounds.left + (res * np.floor((xmin - rio_image.bounds.left) / res))        

        geom_mask = features.geometry_mask(
            geometries=[geom], out_shape=(height, width),
            transform=from_origin(adj_xmin, adj_ymax, res, res), all_touched=True
        )

        data = rio_image.read(window=windows.Window(col_off=col_offset, 
            row_off=row_offset, width=geom_mask.shape[1], 
            height=geom_mask.shape[0])).astype(np.float32)
        data = data[np.array(bands) - 1]
        
        if data.size == 0:
            print('WARN: Geometry outside image bounds!')
            data = np.zeros((len(bands), ) + geom_mask.shape, dtype=float)
            data[:] = np.nan
        elif data.shape[1:] != geom_mask.shape:
            print('WARN: Geometry mismatch, possibly partly outside image bounds!')
            data = np.zeros((len(bands), ) + geom_mask.shape, dtype=float)
            data[:] = np.nan
        else:
            data[geom_mask & (data != rio_image.nodata)] = np.nan

            for val in ignore:
                data[data == val] = np.nan

    results = np_stats(data, metrics)
    
    # import matplotlib.pyplot as plt
    # _, ax = plt.subplots(nrows=1, ncols=2, sharex=True, sharey=True)
    # ax[0].imshow(np.moveaxis(data[:3], 0, -1).astype(int))
    # ax[1].imshow(geom_mask)
    # plt.show()
    # plt.close()

    return results


def calculate_raster_stats(inputvector, raster, outputvector, metrics, prefix,
        bands, bandnames, out_format, buffer, ignore):
    gdf = gpd.read_file(inputvector)
    rio_image = rio.open(raster, 'r')

    
    column_names = [(f"{prefix[i]}_" if len(prefix[i]) > 0 else '') + b + ('_' if len(bandnames) > 0 else '') + stat for stat in metrics for i, b in enumerate(bandnames)]
    # calc_stats(rio_image, gdf.iloc[0], bands, stats)

    for i, row in tqdm(gdf.iterrows(), total=len(gdf)):
        gdf.loc[i, column_names] = calc_stats(rio_image, row, bands, metrics, buffer, ignore)

    gdf.to_file(outputvector, driver=out_format)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("inputvector", help="Vector source file name")
    parser.add_argument("raster", help="Raster file name")
    parser.add_argument("outputvector", help="Output vector file name")
    parser.add_argument("--metrics", nargs='*', type=str, default=[''], 
        help="List of statistics to calculate, e.g., ['mean, std'] or " \
             "['perc25', 'perc75'] for the 25th and 75th percentiles.")
    parser.add_argument("--bands", nargs='*', type=int, default=[1], 
        help="Band number(s) to select")
    parser.add_argument("--prefix", type=str, default=[''], 
        help="Attribute prefix(s) for band(s)")
    parser.add_argument("--bandnames", nargs='*', type=str, default=[''], 
        help="Band names")
    parser.add_argument("--format", type=str, default='GPKG', 
        help="Output vector format")
    parser.add_argument("--buffer", type=float, default=0., 
        help="Buffer radius of vector features")
    parser.add_argument("--ignore", nargs='*', type=float, default=[0.], 
        help="Values to ignore during metric calculation")
    args = parser.parse_args()

    if len(args.bands) > 1:
        if len(args.prefix) == 1:
            args.prefix *= len(args.bands)
        
        if len(args.bandnames) == 1:
            args.bandnames = [f"b{band:02d}" for band in args.bands]

        if len(args.prefix) == 1:
            args.prefix *= len(args.bands)
        elif len(args.prefix) != len(args.bands):
            raise Exception("--prefix should either be 1 arg or the same length as --bands")
        
    assert len(args.bandnames) == len(args.bands), "--bandnames should either be 1 arg or the same length as --bands"
    assert len(args.prefix) == len(args.bands), "--prefix should either be 1 arg or the same length as --bands"

    calculate_raster_stats(
        args.inputvector, 
        args.raster, 
        args.outputvector,
        metrics=args.metrics, 
        prefix=args.prefix, 
        bands=args.bands, 
        bandnames=args.bandnames, 
        out_format=args.format, 
        buffer=args.buffer,
        ignore=args.ignore
    )

# python rasterstats.py /nesi/project/landcare03178/data/experiments/trees-wairarapa/model_detectron2/prediction_gwrc_RGB_2021_wairarapa_2.gpkg /nesi/project/landcare03178/data/experiments/wairarapa-species/model_smp_unet64_f1_jaccard/prediction_gwrc_RGBI_2021_wairarapa_2.kea /nesi/project/landcare03178/data/experiments/trees-wairarapa/model_detectron2/prediction_gwrc_RGB_2021_wairarapa_2_species.gpkg --metrics mode --bands 1 --bandnames CLASS --buffer 0  