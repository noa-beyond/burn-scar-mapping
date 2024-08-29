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


def rgb_composite(data, time):
    def brighten(band):
        alpha = 0.13
        beta = 0
        return np.clip(alpha * band + beta, 0, 255)

    def normalize(band):
        band_min, band_max = band.min(), band.max()
        return (band - band_min) / (band_max - band_min)
    
    # Access the bands using correct variable names
    #red = data['red'].isel(time=time).values
    #green = data['green'].isel(time=time).values
    #blue = data['blue'].isel(time=time).values

    # Access the bands using correct variable names
    red = data['swir22'].isel(time=time).values
    green = data['nir08'].isel(time=time).values
    blue = data['red'].isel(time=time).values

    # Apply brighten and normalize functions
    red_b = brighten(red) # 12
    green_b = brighten(green) # 8A
    blue_b = brighten(blue) # 4

    red_bn = normalize(red_b)
    green_bn = normalize(green_b)
    blue_bn = normalize(blue_b)

    # Combine the bands into an RGB composite
    rgb_composite_bn = np.dstack((red_bn, green_bn, blue_bn))

    # Display the RGB composite
    #plt.imshow(rgb_composite_bn)
    #plt.savefig('swir_nir_red_07_16_2024.png')
    #plt.show()
    #plt.savefig('rgb_07_28_2024.png')



def save_as_tiff(data_array, file_path):
    # Convert the data type to float32
    data_array = data_array.astype('float32')

    # Get the dimensions and resolution
    channels, height, width = data_array.shape
    print(height, width, channels)
    
    transform = from_origin(data_array.longitude.min(), data_array.latitude.max(), 
                            (data_array.longitude.max() - data_array.longitude.min()) / width,
                            (data_array.latitude.max() - data_array.latitude.min()) / height)

    # Save as a TIFF file
    with rasterio.open(
        file_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=3, # 3 channels R,G,B
        dtype=data_array.dtype,
        crs='EPSG:2100',
        transform=transform,
    ) as dst:
        dst.write(data_array[2, :, :], 1) # green 2, blue 3, red 4 from data array
        dst.write(data_array[1, :, :], 2) 
        dst.write(data_array[0, :, :], 3)
        




if __name__ == "__main__":
    
    # path to geojson file containing bounding box of burned area
    with open('BurnedAreaBox.json', 'r') as file:
        burnedAreaBox = json.load(file)

    # init fire object with geojson file containing polygon coords
    fire = FireMonitor(burnedAreaBox)

    

    min_x = min(coord[0] for coord in coordinates)  # Minimum longitude
    min_y = min(coord[1] for coord in coordinates)  # Minimum latitude
    max_x = max(coord[0] for coord in coordinates)  # Maximum longitude
    max_y = max(coord[1] for coord in coordinates)  # Maximum latitude

    bbox = [min_x, min_y, max_x, max_y]

    # make it a box
    BurnedAreaBox = box(*bbox)

    
    # define transformation if needed
    transformer_4326 = pyproj.Transformer.from_crs(
    crs_from='4326',
    crs_to="epsg:4326",
    always_xy=True,
    )

    # transform the coords and get the bounds only
    BurnedAreaBox = transform(transformer_4326.transform, BurnedAreaBox).bounds

    start_DATE = '2024-06-20'
    end_DATE = '2024-07-10'

    catalog = pystac_client.Client.open(STAC_URL)
    catalog.add_conforms_to('ITEM_SEARCH')
    catalog.add_conforms_to('QUERY')

    stac_items = catalog.search(
        collections=[STAC_COLLECTION],
        bbox=BurnedAreaBox,
        datetime=[start_DATE, end_DATE],
        query={'eo:cloud_cover': {'lt': 50}}
    )
    

    resolution = 10 / 111320 #111111 1 degree is 111km
    epsg = 4326


    # reolution must match the crs, if projected use meteres, if (f,l) use degrees
    geobox = GeoBox.from_bbox(BurnedAreaBox, crs=f"epsg:{epsg}", resolution=resolution)

    data = odc.stac.load(
        stac_items.items(),
        chunks={},
        geobox=geobox, 
             # band 2,  band 3,  band 4, band 5,     band 6,     band 7,  band 8, band 8A,  band 9,  band 11, band 12, missing cirrus
        bands=['blue', 'green', 'red', 'rededge1', 'rededge2', 'rededge3', 'nir', 'nir08', 'nir09', 'swir16', 'swir22', 'scl'],
        groupby='solar_day'
    )

    # define SCL values for water and clouds
    # get SCL info from https://brazil-data-cube.github.io/specifications/bands/SCL.html
    water_classes = [6] # 6 is number of class in scl 
    cloud_classes = [8, 9, 10] # 8, 9, 10 is number of classed in scl for cloud (all 8, 9, 10 is clouds in scl)

    scl = data['scl']

    # create mask for water and clouds, in scl where 6, 8, 9, 10 is present it returns True
    mask = np.isin(scl, water_classes + cloud_classes)

    # remove areas from data where the mask is (make them nan)
    data = data.where(~mask, np.nan)

    B12 = data.swir16.astype('float16')
    B08 = data.nir.astype('float16')
    B04 = data.red.astype('float16')

    data['nbr'] = (B08 - B12) / (B08 + B12)
    data['ndvi'] = (B08 - B04) / (B08 + B04)

    #data.nbr.plot(col='time', cmap='Greys_r', col_wrap=4)
    #plt.show()

    post_fire = data.isel(time=[-1])
    pre_fire = data.isel(time=[1])

    # Call the function with your data and desired file path
    rgb_tiff = data.isel(time=-2).to_array()
    file_path = './test_rgb.tiff'
    save_as_tiff(rgb_tiff, file_path)