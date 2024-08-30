from ast import pattern
import xarray as xr
import os
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import mapping
from shapely.geometry import box
import rasterio
from rasterio.mask import mask
import glob
import requests
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import requests
import getpass
import zipfile
from sentinelhub import (SHConfig, DataCollection, SentinelHubCatalog, SentinelHubRequest, BBox, bbox_to_dimensions, CRS, MimeType, Geometry)
import rioxarray

def get_access_token(username: str, password: str) -> str:
    '''
    Get access token for the Copernicus Data Store
    '''
    data = {
        "client_id": "cdse-public",
        "username": "alexantrasaka@gmail.com",
        "password": "Skelen9802!_",
        "grant_type": "password",
    }
    try:
        r = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data=data,
        )
        r.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Access token creation failed. Reponse from the server was: {r.json()}"
        )

    return r.json()["access_token"]

def search_products(bbox, time_user): #bbox = BBox(bbox=[12.44693, 41.870072, 12.541001, 41.917096], crs=CRS.WGS84)
    # Credentials
    config = SHConfig()
    config.sh_client_id = 'sh-dce21bb4-8cfb-48df-8f32-8c655d0a83f1'
    config.sh_client_secret = '6ZiLKeRpeyTNfrovxYLVgnMN7qj0HUv1'
    config.sh_base_url = 'https://sh.dataspace.copernicus.eu'
    config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'

    catalog = catalog = SentinelHubCatalog(config=config)

    search_iterator = catalog.search(
      DataCollection.SENTINEL2_L2A,  
      bbox=bbox,
      time = time_user, #time=('2023-04-11', '2023-05-11'),
    )
    results = list(search_iterator)
    return results

def find_cloud_coverage (bbox,start_date, end_date, level = 'sentinel-2a', cloud_coverage_threshold=10):
    
    results = search_products(BBox(bbox=bbox, crs=CRS.WGS84), (start_date, end_date)) # Search for products
    products = pd.DataFrame(results)  # Convert to DataFrame
    products['title'] = products['id']
    products['date'] = products['properties'].apply(lambda x: x['datetime'])
    products['cloud_coverage'] = products['properties'].apply(lambda x: x['eo:cloud_cover'])
    products = products[products.cloud_coverage <= cloud_coverage_threshold]
    products_sorted_with_cloud = products.sort_values(['date', 'title'], ascending=True).reset_index()
    
    return products_sorted_with_cloud

def search_sentinel(start_date, end_date, aoi_polygon ,bbox, data_collection = "SENTINEL-2", level = 'L2A'):
    '''
    Search for Sentinel-2 images in the Copernicus Data based on dates and area of interest
    '''
    json = requests.get(f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{data_collection}' and OData.CSC.Intersects(area=geography'SRID=4326;{aoi_polygon}) and ContentDate/Start gt {start_date}T00:00:00.000Z and ContentDate/Start lt {end_date}T00:00:00.000Z").json()
    products = pd.DataFrame.from_dict(json['value'])

    products['tile'] = products.Name.apply(lambda x: x.split('_')[5][1:])
    products['level'] = products.S3Path.apply(lambda x: x.split('/')[4])
    products = products[products.level == level]
    products['date'] = products.ContentDate.apply(lambda x: x['Start'])  
    products_sorted  = products.sort_values('date', ascending=True).reset_index()
    products_sorted_with_cloud = find_cloud_coverage (bbox,start_date, end_date, level = 'sentinel-2a')

    # Merge the DataFrames on the matching columns
    merged_df = pd.merge(products_sorted, products_sorted_with_cloud, left_on='Name', right_on='title', how='left')
    # Filter rows where the merge was successful
    filtered_df = merged_df[merged_df['cloud_coverage'].notna()]
    # Extract the cloud coverage column to the row list
    row = filtered_df['cloud_coverage'].tolist()
    # Drop rows from the original DataFrame where the merge was not successful
    products_sorted_filtered = products_sorted[products_sorted.Name.isin(filtered_df.Name)]
    
    if products_sorted_filtered.empty:
        print("There not available images with the given cloud coverage threshold")
        return None, None, None, None
  
    pre_id = products_sorted_filtered.loc[0].Id
    pre_tile = products_sorted_filtered.loc[0].tile
    pre_name = products_sorted_filtered.loc[0].Name
    post_products_sorted = products_sorted_filtered[products_sorted_filtered.tile == pre_tile]
    post_id = post_products_sorted.loc[post_products_sorted.index[-1]].Id
    post_name = products_sorted_filtered.loc[post_products_sorted.index[-1]].Name
  
    return(pre_id,post_id,pre_name,post_name) #Returns a tuple containing the IDs and names of the earliest and latest products

def check_clouds_in_aoi(bb,output_dir,image):
    # Find the file path of the cloud coverage file
    cloud_coverage_dir = os.path.join(output_dir, image)
    jp2_path_pattern = os.path.join(cloud_coverage_dir, 'GRANULE', '*', 'IMG_DATA','*', '*_SCL_20m.jp2')
    jp2_path_pattern = glob.glob(jp2_path_pattern)
    print('the path pattern is:',jp2_path_pattern)
    # Find the file path of the band 8 file (10m resolution)
    band8_path_pattern = os.path.join(cloud_coverage_dir, 'GRANULE', '*', 'IMG_DATA','*', '*_B08*.jp2')
    band8_path = glob.glob(band8_path_pattern)
    # Open the band 8 file and the cloud coverage file
    b8 = rioxarray.open_rasterio(band8_path[0])
    clouds_20m = rioxarray.open_rasterio(jp2_path_pattern[0])
    # Resample the cloud coverage file to 10m resolution
    clouds_resampled_10m = clouds_20m.interp_like(b8,method='nearest')

    # Aoi to polygon
    # Create a Shapely polygon object
    polygon = Polygon([(bb[0], bb[1]), (bb[2], bb[1]), (bb[2], bb[3]), (bb[0], bb[3]), (bb[0], bb[1])])
    # Create a GeoDataFrame
    # Create a GeoDataFrame from the Polygon
    gdf = gpd.GeoDataFrame([polygon], columns=['geometry'])
    # Set the CRS ## ALLOW OVERRIDE TRUE !!
    gdf = gdf.set_crs(crs="EPSG:4326", epsg=None, inplace=False, allow_override=True)
    # Step 1: Reproject the polygon to match the CRS of the DataArray if necessary
    gdf = gdf.to_crs(clouds_resampled_10m.rio.crs)
    # Step 2: Convert the polygon to a geometry object if necessary
    # If the polygon is a GeoDataFrame, extract the geometry
    if isinstance(gdf, gpd.GeoDataFrame):
        geom = gdf.geometry.values[0]
    else:
        geom = gdf
    # Step 3: Clip the DataArray using the polygon
    masked_data = clouds_resampled_10m.rio.clip([mapping(geom)], clouds_resampled_10m.rio.crs, drop=True)    
    # Step 4: Check for the presence of values 2, 3, 8, or 9
    relevant_values = [2, 3, 8, 9]
    presence = np.isin(masked_data, relevant_values)
    # Step 5: Count the number of pixels with these values
    count = np.sum(presence)
    # Convert the masked data to a numpy array
    masked_data_array = masked_data.values
    # Count the total number of pixels in the clipped area
    total_pixels = np.prod(masked_data_array.shape)
    cloud_percentage = (count / total_pixels) * 100
    # Step 6: Output the result
    if np.any(presence): # If any pixel has those values
        print("The area contains", count, "pixels with values 2, 3, 8, or 9 of the Total:.", total_pixels)
        print("The percentage of pixels with values 2, 3, 8, or 9 is", cloud_percentage, "%")
    else:
        print("The area does not contain pixels with values 2, 3, 8, or 9.")

    #return()

def download_cart_sentinel(image_id,output_dir,access_token, name = 'unknown'):
    safe_dir = os.path.join(output_dir, name)
    if os.path.exists(safe_dir):
        print(f"The image {image_id} is already downloaded.")
    else:
        url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({image_id})/$value"
    
        headers = {"Authorization": f"Bearer {access_token}"}
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, headers=headers, stream=True)
    
        with open(os.path.join(output_dir,name+'.zip'), "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        unzip_dir = os.path.join(output_dir, name+'.zip')   
        try:
            with zipfile.ZipFile(unzip_dir, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            #os.makedirs(unzip_dir, exist_ok=True)
            #os.system(f'unzip {unzip_dir} -d {output_dir}')
            os.remove(unzip_dir)
        except:
            print('zip has been deleted')
            print(unzip_dir)
    print('SAFE dir:',safe_dir)
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
    nbr = create_nbr(band8_path[0],band12_path[0])
    return(nbr)

def create_nbr(band8_path,band12_path):
    b8 = rioxarray.open_rasterio(band8_path)
    b12 = rioxarray.open_rasterio(band12_path)
    b12_resampled = b12.interp_like(b8,method='nearest')
    nbr = (b8.values - b12_resampled.values)/(b8.values + b12_resampled.values)
    nbr = nbr.squeeze()
    nbr = xr.DataArray(nbr, coords={'x': b8['x'], 'y': b8['y']}, dims=['y', 'x'])
    nbr = nbr.squeeze()
    return(nbr)

def create_ndvi(band4_path,band8_path):
    b4 = xr.open_dataset(band4_path,engine='rasterio')
    b8 = xr.open_dataset(band8_path)
    b8_resampled = b8.interp_like(b4,method='nearest')
    ndvi = (b8_resampled.band_data.values - b4.band_data.values)/(b8_resampled.band_data.values + b4.band_data.values)
    ndvi = ndvi.squeeze()
    ndvi = xr.DataArray(ndvi, coords={'x': b4['x'], 'y': b4['y']}, dims=['y', 'x'])
    ndvi = ndvi.squeeze()
    
    return(ndvi)

def create_ndwi(band3_path,band8_path):
    b3 = xr.open_dataset(band3_path,engine='rasterio')
    b8 = xr.open_dataset(band8_path)
    b8_resampled = b8.interp_like(b3,method='nearest')
    ndwi = (b3.band_data.values - b8_resampled.band_data.values)/(b3.band_data.values + b8_resampled.band_data.values)
    ndwi = ndwi.squeeze()
    ndwi = xr.DataArray(ndwi, coords={'x': b3['x'], 'y': b3['y']}, dims=['y', 'x'])
    ndwi = ndwi.squeeze()
    return(ndwi)

def create_dnbr(nbr_pre, nbr_post):
    dnbr = nbr_pre - nbr_post
    return(dnbr)

def export_burned_area(dnbr_proj, bb_crop, output_dir):
    dnbr_crop = dnbr_proj.sel(x=slice(bb_crop[0],bb_crop[2]), y = slice(bb_crop[3],bb_crop[1]))
    dnbr_crop.rio.to_raster(os.path.join(output_dir,'dnbr_crop.tif'))
    mask = dnbr_crop > 0.09
    result = dnbr_crop.where(mask)
    result = result.squeeze()
    result = xr.DataArray(result.values, coords={'x': result['x'], 'y': result['y']}, dims=['y', 'x'])
    result = result.to_dataset(name='burned')
    result.to_netcdf(os.path.join(output_dir,'burned.nc'))
    gdal_command = 'gdal_polygonize.py {} -b 1 {}'.format(os.path.join(output_dir,'burned.nc'),os.path.join(output_dir,'burned.shp'))
    os.system(gdal_command)
    polygon = gpd.read_file(os.path.join(output_dir,'burned.shp'))
    polygon = polygon.set_crs(4326)
    polygon = polygon.to_crs(2100)
    polygon = polygon.assign(area=polygon.area)
    print('Total Burned area: ',polygon.area.sum()/10000)
    polygon = polygon[polygon.area>25000]
    polygon_buffer = polygon.buffer(40, join_style=1).buffer(-40.0, join_style=1)
    polygon_buffer = polygon_buffer.simplify(tolerance=5)
    #smoothed_polygons = polygon['geometry'].simplify(tolerance=20) # Adjust the tolerance value as needed
    polygon_buffer.to_file((os.path.join(output_dir,'burned_smoothed_buffer40_simplify5.shp')))

def main(start_date, end_date, lat, lon, save_path):
    if lon<=25: #TODO read with rioxarray and get the crs
        raw_crs = 'epsg:32634'
    else:
        raw_crs = 'epsg:32635'
    folder_name = 'test_{}_{}'.format(lat,lon)
    output_dir= os.path.join(save_path,folder_name)
    os.makedirs(output_dir, exist_ok=True)
    bb = [lon-0.01, lat-0.01, lon+0.01, lat+0.01]
    data_collection = "SENTINEL-2"
    aoi = f"POLYGON(({bb[0]} {bb[1]},{bb[2]} {bb[1]},{bb[2]} {bb[3]},{bb[0]} {bb[3]},{bb[0]} {bb[1]}))'"
    access_token = get_access_token("USERNAME", "PASSWORD")
    pre_id, post_id,pre_name,post_name = search_sentinel(start_date, end_date,aoi, data_collection = "SENTINEL-2", level = 'L2A')
    nbr_pre = download_cart_sentinel(pre_id,output_dir,access_token, name = pre_name)
    nbr_post = download_cart_sentinel(post_id,output_dir,access_token, name = post_name)
    nbr_pre.to_netcdf(os.path.join(output_dir,'nbr_pre.nc'))
    nbr_post.to_netcdf(os.path.join(output_dir,'nbr_post.nc'))
    dnbr = create_dnbr(nbr_pre, nbr_post)
    dnbr.rio.to_raster(os.path.join(output_dir,'dnbr.nc'))
    dnbr.rio.write_crs(raw_crs, inplace=True)
    dnbr_proj = dnbr.rio.reproject('epsg:4326')
    bb_crop = [lon-0.6, lat-0.4, lon+0.6, lat+0.4]
    export_burned_area(dnbr_proj, bb_crop, output_dir)

if __name__ == '__main__':
    start_date = '2024-06-29'
    end_date = '2024-07-20'
    lat = 38.4127
    lon = 25.9901
    save_path = './'
    main(start_date, end_date, lat, lon, save_path)



