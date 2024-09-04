from heapq import merge
import os
from htmltools import pre
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
import subprocess
import shutil 
from L2A_Downloader import Downloader
from addon_for_mapping import RoadsMasker

class Processor:
    def __init__(self, downloader,cloud_coverage_threshold, mask_threshold):
        self.downloader = downloader
        self.cloud_coverage_threshold = cloud_coverage_threshold
        self.mask_threshold = mask_threshold

    def create_index(self, band1_path, band2_path, index_name):
        band1 = rioxarray.open_rasterio(band1_path)
        band2 = rioxarray.open_rasterio(band2_path)
        band2_resampled = band2.interp_like(band1, method='nearest')
        index = (band1.values - band2_resampled.values) / (band1.values + band2_resampled.values)
        index = xr.DataArray(index.squeeze(), coords={'x': band1['x'], 'y': band1['y']}, dims=['y', 'x'])
        index = index.squeeze()
        band1.close(), band2.close()
        return index

    def create_nbr(self, band8_path, band12_path):
        return self.create_index(band8_path, band12_path, "NBR")

    def create_ndvi(self, band4_path, band8_path):
        return self.create_index(band4_path, band8_path, "NDVI")

    def create_ndwi(self, band3_path, band8_path):
        return self.create_index(band3_path, band8_path, "NDWI")

    def create_dnbr(self, nbr_pre, nbr_post):
        return nbr_pre - nbr_post

    def export_burned_area(self, dnbr_proj, bb_crop, output_dir):
        logging.info('Exporting burned area.')
        try:
            dnbr_crop = dnbr_proj.sel(x=slice(bb_crop[0], bb_crop[2]), y=slice(bb_crop[3], bb_crop[1]))
            dnbr_crop.rio.to_raster(os.path.join(output_dir, 'dnbr_crop.tif'))
            mask = dnbr_crop > self.mask_threshold
            result = dnbr_crop.where(mask)
            result = result.squeeze()
            result = xr.DataArray(result.values, coords={'x': result['x'], 'y': result['y']}, dims=['y', 'x']).to_dataset(name='burned')
            result.to_netcdf(os.path.join(output_dir, 'burned.nc'))
            #result.rio.to_raster(os.path.join(output_dir, 'burned.tiff'))
            ###roadmasker = RoadsMasker(result, "D:\\Praktiki\\OSM_Roads\\gis_osm_roads_free_1.shp", output_dir)
            ###roadmask_dir = roadmasker.mask_roads()
            gdal_script = 'D:\\programs\\installed_in_D\\anaconda3\\envs\\environment_V_p_3_10\\Scripts\\gdal_polygonize.py'
            #gdal_command = f"python {gdal_script} {os.path.join(output_dir, 'burned.tif')} -b 1 {os.path.join(output_dir, 'burned.shp')}"
            ###gdal_command = f"python {gdal_script} {roadmask_dir} -b 1 {os.path.join(output_dir, 'burned.shp')}"
            gdal_command = f"python {gdal_script} {os.path.join(output_dir, 'burned.nc')} -b 1 {os.path.join(output_dir, 'burned.shp')}"
            os.system(gdal_command)
            polygon = gpd.read_file(os.path.join(output_dir,'burned.shp'))
            polygon = polygon.set_crs(4326)
            polygon = polygon.to_crs(2100)
            polygon = polygon.assign(area=polygon.area)
            print('Total Burned area: ',polygon.area.sum()/10000)
            polygon = polygon[polygon.area>25000]
            polygon_buffer = polygon.dissolve()
            polygon_buffer = polygon.buffer(40, join_style=1).buffer(-40.0, join_style=1)
            polygon_buffer = polygon_buffer.simplify(tolerance=5)
            polygon_buffer.to_file((os.path.join(output_dir,'burned_smoothed_buffer40_simplify5.shp')))
            logging.info('Burned area exported and processed successfully.')

        except Exception as e:
            logging.error(f'Error exporting burned area: {e}')
            raise

    def download_n_create_nbr(self, image_id, output_dir, image_name):
        logging.info(f'Downloading and creating NBR for image ID: {image_id}')
        try:
            save_dir = self.downloader.download_sentinel_image(image_id, output_dir, image_name)
            band8_path_pattern = os.path.join(save_dir, 'GRANULE', '*', 'IMG_DATA','*', '*_B08*.jp2')
            band12_path_pattern = os.path.join(save_dir, 'GRANULE', '*', 'IMG_DATA','*', '*_B12*.jp2')
            band4_path_pattern = os.path.join(save_dir, 'GRANULE', '*', 'IMG_DATA','*', '*_B04*.jp2')
            band3_path_pattern = os.path.join(save_dir, 'GRANULE', '*', 'IMG_DATA', '*','*_B03*.jp2')
            band2_path_pattern = os.path.join(save_dir, 'GRANULE', '*', 'IMG_DATA', '*','*_B02*.jp2')
            band8_path = glob.glob(band8_path_pattern)
            band12_path = glob.glob(band12_path_pattern)
            band4_path = glob.glob(band4_path_pattern)
            band3_path = glob.glob(band3_path_pattern)
            band2_path = glob.glob(band2_path_pattern)
            nbr = self.create_nbr(band8_path[0],band12_path[0])
            return nbr
        
        except Exception as e:
            logging.error(f'Error downloading and creating NBR: {e}')
            raise

    def handler(self, func, path, exc_info): 
        print("Inside handler") 
        print(exc_info)    
        
    # Function to delete folders from a given list of image names
    def delete_folders(self,output_dir,images, image_name):
        logging.info('Deleting folders....')
        try:
            for image in images['Name'].values:
                folder_path = os.path.join(output_dir, image)
                # Check if the folder exists and is not in the folders to keep
                if os.path.isdir(folder_path) and image != image_name:
                    logging.info(f"Deleting folder: {folder_path}")
                    try:
                        shutil.rmtree(folder_path, onerror = self.handler) 
                        logging.info(f"Successfully deleted folder: {folder_path}")
                    except:
                        logging.warning(f'Error deleting folder: {folder_path}')
                        pass
        except Exception as e:
            logging.error(f'Error deleting folders: {e}')
            raise  

    def process_burned_area(self, start_date, end_date, pre_fire_date,post_fire_date, lat, lon, output_dir):
        logging.info(f'Starting process for burned area with start_date={start_date}, end_date={end_date}, lat={lat}, lon={lon}')
        try:
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
            
            k = 0; z = 0; pre_cloud_index = 0; post_cloud_index = 0
            pre_cloud_bool = False; post_cloud_bool = False

            logging.info('For the pre image:')
            products_sorted_pre = self.downloader.search_sentinel(start_date, pre_fire_date, aoi, bb, self.cloud_coverage_threshold, data_collection = "SENTINEL-2", level = 'L2A')
            
            while pre_cloud_bool == False and k < 5:
                pre_id, pre_name, pre_tile = self.downloader.select_pre_image(products_sorted_pre, pre_cloud_index)
                nbr_pre = self.download_n_create_nbr(pre_id, output_dir, pre_name)
                pre_cloud_bool, pre_cloud_index = self.downloader.check_clouds_in_aoi(bb,output_dir,pre_name, pre_cloud_index)
                
                k += 1
                if k == 5: logging.warning('I have to stop after 5 iterations.')
            
            self.delete_folders(output_dir,products_sorted_pre, pre_name)

            logging.info('For the post image:')
            products_sorted_post = self.downloader.search_sentinel(post_fire_date, end_date, aoi, bb, self.cloud_coverage_threshold, data_collection = "SENTINEL-2", level = 'L2A')
            
            while post_cloud_bool == False and z < 5: 
                post_id, post_name = self.downloader.select_post_image(pre_tile, products_sorted_post, post_cloud_index)
                nbr_post = self.download_n_create_nbr(post_id,output_dir, post_name)
                post_cloud_bool, post_cloud_index = self.downloader.check_clouds_in_aoi(bb,output_dir,post_name, post_cloud_index)
                
                z += 1 
                if z == 5: print('I have to stop')    

            self.delete_folders(output_dir,products_sorted_post, post_name)    
            logging.info('Process completed.')

            print('The images that will be used are:')
            print('Pre image:', pre_name)
            print('Post image:', post_name)
            
            nbr_pre.to_netcdf(os.path.join(output_dir,'nbr_pre.nc'))
            nbr_post.to_netcdf(os.path.join(output_dir,'nbr_post.nc'))
            dnbr = self.create_dnbr(nbr_pre, nbr_post)
            dnbr.rio.to_raster(os.path.join(output_dir,'dnbr.nc'))
            dnbr.rio.write_crs(raw_crs, inplace=True)
            dnbr_proj = dnbr.rio.reproject("epsg:4326")
            bb_crop = [lon-0.6, lat-0.4, lon+0.6, lat+0.4]
            #print(bb_crop)
            self.export_burned_area(dnbr_proj, bb_crop, output_dir)
            return output_dir
        
        except Exception as e:
            logging.error(f'Error processing burned area: {e}')
            raise    
