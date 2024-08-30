import pyproj
import pystac_client
from shapely.geometry import box
from shapely.ops import transform
import odc.stac
from odc.geo.geobox import GeoBox
import matplotlib.colors as mcolors
from geogif import dgif
import matplotlib.pyplot as plt
import xarray as xr
import numpy as np
import json
import rasterio
from rasterio.transform import from_origin
from source.OpenDataCubeFires import FireMonitor




if __name__ == "__main__":
    
    # path to geojson file containing bounding box of burned area
    with open('BurnedAreaBox.json', 'r') as file:
        burnedAreaBox = json.load(file)


    start_DATE = '2024-06-15' # xios fire 2024-07-01
    end_DATE   = '2024-07-15'
    cloudCover = 5            # percenatage
    EPSG       = 'EPSG:32635'

    # init fire object
    fire = FireMonitor(burnedAreaBox, start_DATE, end_DATE, cloudCover)

    # save the post and pre fire auto selected images
    fire.save_tiff_rgb('post', 'post_fire_RGB.tiff', EPSG)
    fire.save_tiff_rgb('pre', 'pre_fire_RGB.tiff', EPSG)

    fire.save_tiff_single('nbr_post', 'nbr_post.tiff', EPSG)
    fire.save_tiff_single('nbr_pre', 'nbr_pre.tiff', EPSG)

    fire.save_tiff_single('dnbr', 'dnbr.tiff', EPSG)
    

    fire.data.nbr.plot(col='time', cmap='Greys_r', col_wrap=4)
    print(f'Saving plot with pre and post images..')
    plt.savefig('Sentinel 2 Pre and Post Fire.png', dpi=1000, format='png')
    #plt.show()

    exit()

