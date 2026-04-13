"""
ratools.py
Spring 2026 PJW

Module for utility routines for the risk assessment example.
"""

import rasterio
from json import dumps

#===========================================================
#  raster_info()
#
#  Print out metadata about an open raster.
#===========================================================

def raster_info(ras: rasterio.io.DatasetReader) -> None:

    #
    #  Basic information about the grid
    #

    print('Bands:',ras.count)
    print('Nodata:',ras.nodata)
    print('Height:',ras.height)
    print('Width:',ras.width)
    print('Points:',f'{ras.height*ras.width:,}')

    #
    #  Does it use compression?
    #

    if ras.compression is not None:
        print('Compression:',ras.compression.name)
    else:
        print('Compression:','None')

    #
    #  Information about the CRS
    #

    print('CRS:',ras.crs)
    print('EPSG:',ras.crs.to_epsg())
    print('Projected:',ras.crs.is_projected)
    print('Units:',ras.crs.units_factor[0])

    #
    #  Resolution and bounds
    #

    print('Resolution:')
    print(f'   width  = {ras.res[0]}')
    print(f'   height = {ras.res[1]}')

    b = ras.bounds
    print('Bounds:')
    print(f'   left = {b.left}, right = {b.right}')
    print(f'   top = {b.top}, bottom = {b.bottom}')

    print('Tags:')
    print(dumps(ras.tags(),indent=4))

    #
    #  Information about individual bands
    #

    print()
    for band in range(1,1+ras.count):
        print(f'Band {band}:')
        print('Description:',ras.descriptions[band-1])
        print('Data type:',ras.dtypes[band-1])
        print('Tags:')
        print(dumps(ras.tags(band),indent=4))

