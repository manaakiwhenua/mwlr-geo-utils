#!/bin/bash

if [[ $# -ne 4 ]]; then
    echo ""
    echo "Change the bands of a GDAL VRT file, useful after building a VRT with "
    echo "    -separate if you want to reference source bands other than band 1"
    echo "Usage:"
    echo "  mw-setvrtband.sh input_file.vrt fromband toband output_file.vrt"
    echo "  e.g. "
    echo "  mw-setvrtband.sh image1.vrt 1 2 image2.vrt"
    echo ""
    exit 1
fi

sed -e "/SourceBand/s/<SourceBand>$2<\/SourceBand>/<SourceBand>$3<\/SourceBand>/" "$1" > "$4"
