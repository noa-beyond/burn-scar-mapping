import os
import requests
import os
import logging
import requests
import pandas as pd
import geopandas as gpd
import xarray as xr
import glob
import zipfile
from sentinelhub import SHConfig, DataCollection, SentinelHubCatalog, BBox, CRS
import rioxarray
from SentinelDownloader import Downloader

class Processor:
    def __init__(self, downloader):
        self.downloader = downloader

    def create_index(self, band1_path, band2_path, index_name):
        band1 = rioxarray.open_rasterio(band1_path)
        band2 = rioxarray.open_rasterio(band2_path)
        band2_resampled = band2.interp_like(band1, method='nearest')
        index = (band1.values - band2_resampled.values) / (band1.values + band2_resampled.values)
        index = xr.DataArray(index.squeeze(), coords={'x': band1['x'], 'y': band1['y']}, dims=['y', 'x'])
        return index.squeeze()

    def create_nbr(self, band8_path, band12_path):
        return self.create_index(band8_path, band12_path, "NBR")

    def create_ndvi(self, band4_path, band8_path):
        return self.create_index(band4_path, band8_path, "NDVI")

    def create_ndwi(self, band3_path, band8_path):
        return self.create_index(band3_path, band8_path, "NDWI")

    def create_dnbr(self, nbr_pre, nbr_post):
        return nbr_pre - nbr_post

    def export_burned_area(self, dnbr_proj, bb_crop, output_dir):
        dnbr_crop = dnbr_proj.sel(x=slice(bb_crop[0], bb_crop[2]), y=slice(bb_crop[3], bb_crop[1]))
        dnbr_crop.rio.to_raster(os.path.join(output_dir, 'dnbr_crop.tif'))
        mask = dnbr_crop > 0.09
        result = dnbr_crop.where(mask).squeeze()
        result = xr.DataArray(result.values, coords={'x': result['x'], 'y': result['y']}, dims=['y', 'x']).to_dataset(name='burned')
        result.to_netcdf(os.path.join(output_dir, 'burned.nc'))
        gdal_command = f"gdal_polygonize.py {os.path.join(output_dir, 'burned.nc')} -b 1 {os.path.join(output_dir, 'burned.shp')}"
        os.system(gdal_command)
        polygon = gpd.read_file(os.path.join(output_dir, 'burned.shp')).set_crs(4326).to_crs(2100)
        polygon['area'] = polygon.area
        print('Total Burned area:', polygon['area'].sum() / 10000)
        polygon = polygon[polygon.area > 25000]
        polygon_buffer = polygon.buffer(40, join_style=1).buffer(-40.0, join_style=1).simplify(tolerance=5)
        polygon_buffer.to_file(os.path.join(output_dir, 'burned_smoothed_buffer40_simplify5.shp'))

    def find_path_pattern(self, safe_dir):
        band8_path_pattern = os.path.join(safe_dir, 'GRANULE', '*', 'IMG_DATA','*', '*_B08*.jp2')
        band12_path_pattern = os.path.join(safe_dir, 'GRANULE', '*', 'IMG_DATA','*', '*_B12*.jp2')
        band4_path_pattern = os.path.join(safe_dir, 'GRANULE', '*', 'IMG_DATA','*', '*_B04*.jp2')
        band3_path_pattern = os.path.join(safe_dir, 'GRANULE', '*', 'IMG_DATA', '*','*_B03*.jp2')
        band2_path_pattern = os.path.join(safe_dir, 'GRANULE', '*', 'IMG_DATA', '*','*_B02*.jp2')
        band8_path = glob.glob(band8_path_pattern)
        band12_path = glob.glob(band12_path_pattern)
        band4_path = glob.glob(band4_path_pattern)
        band3_path = glob.glob(band3_path_pattern)
        band2_path = glob.glob(band2_path_pattern)
        print(band8_path)
        nbr = self.create_nbr(band8_path[0],band12_path[0])
        
        return nbr


    def process_burned_area(self, start_date, end_date, lat, lon, output_dir):
        if lon<=25: #TODO read with rioxarray and get the crs
            raw_crs = 'epsg:32634'
        else:
            raw_crs = 'epsg:32635'

        folder_name = 'test_{}_{}'.format(lat,lon)
        output_dir= os.path.join(output_dir,folder_name)
        os.makedirs(output_dir, exist_ok=True)

        bb = [lon-0.01, lat-0.01, lon+0.01, lat+0.01]
        data_collection = "SENTINEL-2"
        aoi = f"POLYGON(({bb[0]} {bb[1]},{bb[2]} {bb[1]},{bb[2]} {bb[3]},{bb[0]} {bb[3]},{bb[0]} {bb[1]}))'"  
        
        pre_id, post_id, pre_name, post_name = self.downloader.search_sentinel(start_date=start_date, end_date=end_date, aoi_polygon=aoi, bbox=bb)
        pre_save_dir = self.downloader.download_sentinel_image(pre_id, output_dir, pre_name)
        post_save_dir = self.downloader.download_sentinel_image(post_id, output_dir, post_name)
        nbr_pre = self.find_path_pattern(pre_save_dir)
        nbr_post = self.find_path_pattern(post_save_dir)
        dnbr = self.create_dnbr(nbr_pre, nbr_post)
        dnbr.rio.write_crs(raw_crs, inplace=True)
        dnbr_proj = dnbr.rio.reproject("epsg:4326")
        bb_crop = [lon-0.0005, lat-0.0005, lon+0.0005, lat+0.0005]
        self.export_burned_area(dnbr_proj, bb_crop, output_dir)
        return output_dir
