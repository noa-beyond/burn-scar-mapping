import pyproj
import pystac_client
import autoroot
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
from source.SearchSentinelOpenDataCube import SearchSentinel
import rioxarray
from affine import Affine

""" 
STAC Datasets : https://stacspec.org/en/about/datasets/
Sentinel 2    : https://stacindex.org/catalogs/earth-search#/
"""


class FireMonitor:

    def __init__(self, BurnedAreaBox_json, start_DATE, end_DATE, cloudCover):
        self.BurnedAreaBox_json = BurnedAreaBox_json
        self.start_DATE = start_DATE
        self.end_DATE = end_DATE
        self.cloudCover = cloudCover
        
        # get polygon from json file
        BurnedAreaBox = self.get_bbox(self.BurnedAreaBox_json)

        # load url for earch search open data cube
        STAC_URL, STAC_COLLECTION = self.load_url()

        # get sentinel data from open data cube
        data = SearchSentinel(STAC_URL, STAC_COLLECTION, BurnedAreaBox, self.start_DATE, self.end_DATE, self.cloudCover).get_data()

        # remove clouds and water with masks from SCL ( https://brazil-data-cube.github.io/specifications/bands/SCL.html )
        #data = self.remove_clouds_water(data)

        data = self.create_nbr_ndvi(data)

        self.post_fire_image = data.isel(time=-1).to_array()
        self.pre_fire_image  = data.isel(time=0).to_array()


        self.nbr_post = data['nbr'].isel(time=-1)
        self.nbr_pre  = data['nbr'].isel(time=0)

        self.ndvi_post = data['ndvi'].isel(time=-1)
        self.ndvi_pre  = data['ndvi'].isel(time=0)

        self.dnbr = self.create_dnbr(self.nbr_post, self.nbr_pre)

        
        self.data = data




    def load_url(self):
        with open('configs/FireMonitoring_OpenDataCube/config_url_fire_monitor.yaml', 'r') as file:
            config = yaml.load(file, yaml.FullLoader)
        return config['STAC_URL'], config['STAC_COLLECTION']    
    

    def get_bbox(self, json_file):
        # get coords from json file
        coordinates = json_file['coordinates'][0]

        min_x = min(coord[0] for coord in coordinates)  # Minimum longitude
        min_y = min(coord[1] for coord in coordinates)  # Minimum latitude
        max_x = max(coord[0] for coord in coordinates)  # Maximum longitude
        max_y = max(coord[1] for coord in coordinates)  # Maximum latitude

        bbox = [min_x, min_y, max_x, max_y]
        BurnedAreaBox = box(*bbox)
        # define transformation if needed
        #transformer_4326 = pyproj.Transformer.from_crs(
        #crs_from='4326',
        #crs_to="epsg:4326",
        #always_xy=True,
        #)
        #BurnedAreaBox = transform(transformer_4326.transform, box(*bbox)).bounds
        return BurnedAreaBox.bounds
    

    def remove_clouds_water(self, data):
        water_classes = [6] # 6 is number of class in scl 
        cloud_classes = [8, 9, 10] # 8, 9, 10 is number of classed in scl for cloud (all 8, 9, 10 is clouds in scl)

        scl = data['scl']

        # create mask for water and clouds, in scl where 6, 8, 9, 10 is present it returns True
        mask = np.isin(scl, water_classes + cloud_classes)

        # make nan in data where the is mask
        #data = data.where(~mask, np.nan)
        cloud_mask = np.isin(scl, cloud_classes)  # Boolean mask where clouds are True
        def calculate_cloud_cover(mask):
            cloud_pixels = np.sum(mask, axis=(1, 2))  # Count cloud pixels in each time step
            total_pixels = np.prod(mask.shape[1:])  # Total number of pixels in each time step
            cloud_cover_percentage = (cloud_pixels / total_pixels) * 100  # Cloud cover percentageprint
            return cloud_cover_percentage
        
        cloud_cover_percentage = calculate_cloud_cover(cloud_mask)

        data['cloud_cover'] = xr.DataArray(cloud_cover_percentage, dims='time', coords={'time': data['time']})

        data = data.sel(time=data['cloud_cover'] <= 20)


        #data = data.sel(cloud_cover=~mask_above_threshold)
        print(data)
        return data


    def create_nbr_ndvi(self, data):
        B12 = data.swir22.astype('float32')
        B08 = data.nir.astype('float32')
        B04 = data.red.astype('float32')
        data['nbr'] = (B08-B12)/(B08+B12)
        data['ndvi'] = (B08-B04)/(B08+B04)
        return data



    def create_dnbr(self, post_fire_nbr, pre_fire_nbr):
        return pre_fire_nbr - post_fire_nbr



    def save_tiff_rgb(self, imageData, filePath_name, to_crs):
        if imageData == 'post':
            imageData = self.post_fire_image
        elif imageData == 'pre':
            imageData = self.pre_fire_image  
        else:
            print(f'Use post or pre in the first argument of save_tiff()')
            return 0 

        imageData = imageData.rio.reproject(to_crs)
        
        imageData = imageData.astype('float32')
        
        bands, height, width = imageData.shape


        transform = Affine.translation(imageData.x.min(),
                                       imageData.y.max()) * Affine.scale((imageData.x.max() - imageData.x.min()) / width,
                                        -(imageData.y.max() - imageData.y.min()) / height)           

        print(f'Saving {filePath_name} with CRS {to_crs}')
        # Save as a TIFF file
        with rasterio.open(
            filePath_name,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=3, # 3 channels R,G,B
            dtype=imageData.dtype,
            crs=to_crs,
            transform=transform,
        ) as image_tiff:
            image_tiff.write(imageData[2, :, :], 1) # green 2, blue 3, red 4 from data array
            image_tiff.write(imageData[1, :, :], 2) 
            image_tiff.write(imageData[0, :, :], 3)



    def save_tiff_single(self, imageData, filePath_name, to_crs):
        if imageData == 'nbr_post':
            imageData = self.nbr_post
        elif imageData == 'ndvi_post':
            imageData = self.ndvi_post
        elif imageData == 'ndvi_pre':
            imageData = self.ndvi_pre
        elif imageData == 'nbr_pre':
            imageData = self.nbr_pre
        elif imageData == 'dnbr':
            imageData = self.dnbr        
        else:
            imageData = self.data[imageData]


        #imageData = imageData.to_array()
        imageData = imageData.rio.reproject(to_crs)
        imageData = imageData.astype('float32')
        height, width = imageData.shape

        transform = Affine.translation(imageData.x.min(),
                                imageData.y.max()) * Affine.scale((imageData.x.max() - imageData.x.min()) / width,
                                -(imageData.y.max() - imageData.y.min()) / height)           

        print(f'Saving {filePath_name} with CRS {to_crs}')
        # Save as a TIFF file
        with rasterio.open(
            filePath_name,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1, # 1 channel grayscale
            dtype=imageData.dtype,
            crs=to_crs,
            transform=transform,
        ) as image_tiff:
            image_tiff.write(imageData[:, :], 1) # one band only
