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
import yaml

""" 
STAC Datasets : https://stacspec.org/en/about/datasets/
Sentinel 2    : https://stacindex.org/catalogs/earth-search#/
"""


class FireMonitor:

    def __init__(self, BurnedAreaBox):
        self.BurnedAreaBox = BurnedAreaBox
        





    def load_url(self):
        with open('configs/config.yaml', 'r') as file:
            config = yaml.load(file, yaml.FullLoader)
        return config['STAC_URL'], config['STAC_COLLECTION']    
    

    def get_bbox(self, json_file):

        coords = json_file['coordinates'][0]



        # get coords from json file
        return json_file['coordinates'][0]
    
