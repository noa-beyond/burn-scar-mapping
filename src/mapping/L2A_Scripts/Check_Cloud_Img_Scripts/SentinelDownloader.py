import os
import logging
import requests
import pandas as pd
import geopandas as gpd
import xarray as xr
import glob
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
    
    