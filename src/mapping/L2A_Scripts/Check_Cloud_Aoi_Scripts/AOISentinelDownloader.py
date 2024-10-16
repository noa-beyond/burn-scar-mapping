import os
import requests
import logging
import pandas as pd
import geopandas as gpd
import xarray as xr
import numpy as np
import glob
from shapely.geometry import Polygon
from shapely.geometry import mapping
import rioxarray
import zipfile
from sentinelhub import SHConfig, DataCollection, SentinelHubCatalog, BBox, CRS

class Downloader:
    def __init__(self, username, password, client_id, client_secret):
         # Set up logging first
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("Class_utils_downloader.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.config = self.configure_sentinel_hub()
        self.access_token = self.get_access_token()

    def configure_sentinel_hub(self):
        config = SHConfig()
        config.sh_client_id = self.client_id
        config.sh_client_secret = self.client_secret
        config.sh_base_url = 'https://sh.dataspace.copernicus.eu'
        config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
        return config
    
    def get_access_token(self) -> str:
        data = {
            "client_id": "cdse-public",
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
        }
        try:
            r = requests.post(
                "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                data=data,
            )
            r.raise_for_status()
            self.logger.info("Access token obtained successfully.")
        except Exception as e:
            raise Exception(f"Access token creation failed. Response from the server was: {r.json()}")
        return r.json()["access_token"]

    def search_products(self, bbox, time_user):
        catalog = SentinelHubCatalog(config=self.config)
        search_iterator = catalog.search(
            DataCollection.SENTINEL2_L2A,  
            bbox=bbox,
            time=time_user,
        )
        results = list(search_iterator)
        self.logger.info(f"Found {len(results)} products for the specified time range.")
        return results

    def find_cloud_coverage(self, bbox, start_date, end_date, cloud_coverage_threshold=10):
        results = self.search_products(BBox(bbox=bbox, crs=CRS.WGS84), (start_date, end_date))
        products = pd.DataFrame(results)
        products['title'] = products['id']
        products['date'] = products['properties'].apply(lambda x: x['datetime'])
        products['cloud_coverage'] = products['properties'].apply(lambda x: x['eo:cloud_cover'])
        products = products[products.cloud_coverage <= cloud_coverage_threshold]
        products_sorted_with_cloud = products.sort_values(['date', 'title'], ascending=True).reset_index()
        self.logger.info(f"{len(products_sorted_with_cloud)} products meet the cloud coverage criteria.")
        return products_sorted_with_cloud

    def search_sentinel(self, start_date, end_date, aoi_polygon, bbox, data_collection="SENTINEL-2", level='L2A'):
        
        json = requests.get(f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{data_collection}' and OData.CSC.Intersects(area=geography'SRID=4326;{aoi_polygon}) and ContentDate/Start gt {start_date}T00:00:00.000Z and ContentDate/Start lt {end_date}T00:00:00.000Z").json()
        products = pd.DataFrame.from_dict(json['value'])
        products['tile'] = products.Name.apply(lambda x: x.split('_')[5][1:])
        products['level'] = products.S3Path.apply(lambda x: x.split('/')[4])
        products = products[products.level == level]
        products['date'] = products.ContentDate.apply(lambda x: x['Start'])  
        products_sorted = products.sort_values('date', ascending=True).reset_index()
        products_sorted_with_cloud = self.find_cloud_coverage(bbox, start_date, end_date)
        merged_df = pd.merge(products_sorted, products_sorted_with_cloud, left_on='Name', right_on='title', how='left')
        filtered_df = merged_df[merged_df['cloud_coverage'].notna()]
        products_sorted_filtered = products_sorted[products_sorted.Name.isin(filtered_df.Name)]
        
        if products_sorted_filtered.empty:
            self.logger.warning("No available images with the given cloud coverage threshold.")
            return None, None, None, None
        
        pre_id = products_sorted_filtered.loc[0].Id
        pre_tile = products_sorted_filtered.loc[0].tile
        pre_name = products_sorted_filtered.loc[0].Name
        post_products_sorted = products_sorted_filtered[products_sorted_filtered.tile == pre_tile]
        post_id = post_products_sorted.loc[post_products_sorted.index[-1]].Id
        post_name = products_sorted_filtered.loc[post_products_sorted.index[-1]].Name
        
        self.logger.info(f"Selected images: {pre_name} (pre-event) and {post_name} (post-event).")
        return pre_id, post_id, pre_name, post_name

    def download_sentinel_image(self, image_id, output_dir, name='unknown'):
        safe_dir = os.path.join(output_dir, name)
        if os.path.exists(safe_dir):
            self.logger.info(f"The image {image_id} is already downloaded.")
            return safe_dir
        url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({image_id})/$value"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(url, headers=headers, stream=True)
        with open(os.path.join(output_dir, f"{name}.zip"), "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        unzip_dir = os.path.join(output_dir, f"{name}.zip")
        try:
            with zipfile.ZipFile(unzip_dir, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            os.remove(unzip_dir)
        except Exception as e:
            print(f"Failed to unzip {unzip_dir}: {e}")
        return safe_dir
    
    def check_clouds_in_aoi(self,bb,output_dir,image):
        cloud_coverage_dir = os.path.join(output_dir, image)
        jp2_path_pattern = os.path.join(cloud_coverage_dir, 'GRANULE', '*', 'IMG_DATA','*', '*_SCL_20m.jp2')
        jp2_path_pattern = glob.glob(jp2_path_pattern)
        band8_path_pattern = os.path.join(cloud_coverage_dir, 'GRANULE', '*', 'IMG_DATA','*', '*_B08*.jp2')
        band8_path = glob.glob(band8_path_pattern)
        b8 = rioxarray.open_rasterio(band8_path[0])
        clouds_20m = rioxarray.open_rasterio(jp2_path_pattern[0])
        clouds_resampled_10m = clouds_20m.interp_like(b8,method='nearest')

        polygon = Polygon([(bb[0], bb[1]), (bb[2], bb[1]), (bb[2], bb[3]), (bb[0], bb[3]), (bb[0], bb[1])])
        gdf = gpd.GeoDataFrame([polygon], columns=['geometry'])
        gdf = gdf.set_crs(crs="EPSG:4326", epsg=None, inplace=False, allow_override=True)
        gdf = gdf.to_crs(clouds_resampled_10m.rio.crs) # Step 1: Reproject the polygon to match the CRS of the DataArray if necessary

        if isinstance(gdf, gpd.GeoDataFrame): # Step 2: Convert the polygon to a geometry object if necessary
            geom = gdf.geometry.values[0]
        else:
            geom = gdf
       
        masked_data = clouds_resampled_10m.rio.clip([mapping(geom)], clouds_resampled_10m.rio.crs, drop=True)   # Step 3: Clip the DataArray using the polygon  
        relevant_values = [2, 3, 8, 9] # Step 4: Check for the presence of values 2, 3, 8, or 9
        presence = np.isin(masked_data, relevant_values) # Step 5: Count the number of pixels with these values
        count = np.sum(presence)
        masked_data_array = masked_data.values # Convert the masked data to a numpy array
        total_pixels = np.prod(masked_data_array.shape) # Count the total number of pixels in the clipped area
        cloud_percentage = (count / total_pixels) * 100
       
        if np.any(presence):  # Step 6: Output the result
            self.logger.info("The area contains %d pixels with values 2, 3, 8, or 9 of the Total: %d.", count, total_pixels)
            self.logger.info("The percentage of pixels with values 2, 3, 8, or 9 is %.2f%%.", cloud_percentage)
        else:
            self.logger.info("The area does not contain pixels with values 2, 3, 8, or 9.") 