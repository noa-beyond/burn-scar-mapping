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
from osgeo import gdal, ogr, osr
import os
import geopandas as gpd
from scipy.ndimage import median_filter
from source.polygonize import polygonize
from source.classify import classify

""" 
STAC Datasets : https://stacspec.org/en/about/datasets/
Sentinel 2    : https://stacindex.org/catalogs/earth-search#/
"""


class FireMonitor:

    def __init__(self, BurnedAreaBox_json, start_DATE, end_DATE, cloudCover, EPSG):
        self.BurnedAreaBox_json = BurnedAreaBox_json
        self.start_DATE = start_DATE
        self.end_DATE = end_DATE
        self.cloudCover = cloudCover
        self.EPSG = EPSG
        
        # get polygon from json file
        BurnedAreaBox = self.get_bbox(self.BurnedAreaBox_json)

        # load url for earch search open data cube
        STAC_URL, STAC_COLLECTION = self.load_url()

        # get sentinel data from open data cube
        data = SearchSentinel(STAC_URL, STAC_COLLECTION, BurnedAreaBox, self.start_DATE, self.end_DATE, self.cloudCover).get_data()

        # remove clouds and water with masks from SCL ( https://brazil-data-cube.github.io/specifications/bands/SCL.html )
        #data = self.remove_clouds_water(data)

        # reproject the data to prefered EPSG
        #data = data.rio.write_crs('EPSG:4326') # arxiko EPSG apo to datacube
        #data = data.rio.reproject(EPSG)

        data = self.create_nbr_ndvi(data)

        self.post_fire_image = data.isel(time=-1).to_array()
        self.pre_fire_image  = data.isel(time=0).to_array()


        self.nbr_post = data['nbr'].isel(time=-1)
        self.nbr_pre  = data['nbr'].isel(time=0)

        self.ndvi_post = data['ndvi'].isel(time=-1)
        self.ndvi_pre  = data['ndvi'].isel(time=0)

        self.dnbr = self.create_dnbr(self.nbr_post, self.nbr_pre)
        self.dnbr = self.dnbr.rio.write_crs('EPSG:4326')
        self.dnbr = self.dnbr.rio.reproject(EPSG)
        
        self.data = data

        self.cropped_dnbr = None # used later in polygonize and classify



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



    def save_tiff_rgb(self, imageData, filePath_name):
        if imageData == 'post':
            imageData = self.post_fire_image
        elif imageData == 'pre':
            imageData = self.pre_fire_image  
        else:
            print(f'Use post or pre in the first argument of save_tiff()')
            return 0 

        
        imageData = imageData.astype('float32')
        bands, height, width = imageData.shape


        print(f'Saving {filePath_name} with CRS {self.EPSG}')
        # Save as a TIFF file
        with rasterio.open(
            filePath_name,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=3, # 3 channels R,G,B
            dtype=imageData.dtype,
            crs=imageData.rio.crs,
            transform=imageData.rio.transform(),
        ) as image_tiff:
            image_tiff.write(imageData[2, :, :], 1) # green 2, blue 3, red 4 from data array
            image_tiff.write(imageData[1, :, :], 2) 
            image_tiff.write(imageData[0, :, :], 3)



    def save_tiff_single(self, imageData, filePath_name):
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


        imageData = imageData.astype('float32')
        height, width = imageData.shape


        print(f'Saving {filePath_name} with CRS {self.EPSG}')
        # Save as a TIFF file
        with rasterio.open(
            filePath_name,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1, # 1 channel grayscale
            dtype=imageData.dtype,
            crs=imageData.rio.crs,
            transform=imageData.rio.transform(),
        ) as image_tiff:
            image_tiff.write(imageData[:, :], 1) # one band only



    def polygonize(self, outputFolder, threshold):
        # vlepe arxeio polygonize.py mesa sto fakelo source
        polygonizer = polygonize(outputFolder, self.EPSG, threshold, self.dnbr)
        self.cropped_dnbr = polygonizer.crop_dnbr()
        
    
    def classify(self, outputFolder):
        classify(self.cropped_dnbr, outputFolder, self.EPSG)
        exit()
        # Open the DNBR TIFF file
        dnbr = gdal.Open(dnbrFile)
        if dnbr is None:
            raise RuntimeError(f"Could not open {dnbrFile}")

        band = dnbr.GetRasterBand(1)
        nodata_value = band.GetNoDataValue()  # Get the NoData value if it exists
        dnbr_array = band.ReadAsArray()  # Read the raster data as a NumPy array

        # Create a mask for NoData values
        no_data_mask = np.where(dnbr_array == nodata_value, 1, 0)

        # Apply classification thresholds
        dNBR_thresholds = {
            'unburned': (0, 0.1),
            'low': (0.1, 0.27),
            'moderate': (0.27, 0.44),
            'high': (0.44, 0.66),
            'very high': (0.66, np.inf)
        }

        # Create a classification array
        classification_array = np.zeros_like(dnbr_array, dtype=np.uint8)

        # Assign classifications based on thresholds
        for idx, (category, (low, high)) in enumerate(dNBR_thresholds.items()):
            mask = (dnbr_array > low) & (dnbr_array <= high)
            classification_array[mask] = idx + 1

        # Apply a 3x3 median filter to the classification array, but keep NoData values unchanged
        filtered_classification = median_filter(classification_array, size=3)

        # Restore NoData values in the filtered classification
        filtered_classification[no_data_mask == 1] = nodata_value

        # Create an in-memory raster to hold the filtered classification
        mem_driver = gdal.GetDriverByName('MEM')
        mem_raster = mem_driver.Create('', dnbr.RasterXSize, dnbr.RasterYSize, 1, gdal.GDT_Byte)
        mem_raster.SetGeoTransform(dnbr.GetGeoTransform())
        mem_raster.SetProjection(dnbr.GetProjection())
        
        # Write the filtered classification into the in-memory raster
        mem_band = mem_raster.GetRasterBand(1)
        mem_band.WriteArray(filtered_classification)
        if nodata_value is not None:
            mem_band.SetNoDataValue(nodata_value)  # Set NoData value for the in-memory raster

        # Create the output shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile")
        out_dnbr = driver.CreateDataSource(outputFileName)

        # Create spatial reference from EPSG code
        srs = osr.SpatialReference()
        epsg_code = int(EPSG.split(':')[1]) if isinstance(EPSG, str) else EPSG
        srs.ImportFromEPSG(epsg_code)

        # Create the output layer
        out_layer = out_dnbr.CreateLayer('polygonized', srs=srs, geom_type=ogr.wkbPolygon)

        # Add a new field for classification
        new_field = ogr.FieldDefn('Class', ogr.OFTInteger)
        out_layer.CreateField(new_field)

        # Add a new field for color
        color_field = ogr.FieldDefn('Color', ogr.OFTString)
        out_layer.CreateField(color_field)

        # Polygonize the filtered classified raster
        gdal.Polygonize(mem_band, None, out_layer, 0, [], callback=None)

        # Define colors for each class
        colors = {
            1: '#FFFF00',  # yellow for 'low'
            2: '#FFBF00',  # orange for 'moderate'
            3: '#FF8000',  # dark orange for 'high'
            4: '#FF0000',  # red for 'very high'
            0: '#FFFFFF'   # white for 'unburned'
        }

        # Assign colors to polygons based on classification
        for feature in out_layer:
            class_id = feature.GetField('Class')
            color = colors.get(class_id, '#FFFFFF')
            feature.SetField('Color', color)
            out_layer.SetFeature(feature)

        # Create the output colored raster
        with rasterio.open(dnbrFile) as src:
            transform = from_origin(src.bounds.left, src.bounds.top, src.res[0], src.res[1])
            
            # Create a color array for the output raster
            color_array = np.zeros((dnbr.RasterYSize, dnbr.RasterXSize, 3), dtype=np.uint8)

            for class_id, hex_color in colors.items():
                if class_id == 0:
                    continue  # Skip 'unburned' since it won't be in the classification
                rgb = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]  # Convert hex to RGB
                color_array[filtered_classification == class_id] = rgb

            # Restore NoData values in the color array
            color_array[no_data_mask == 1] = [0, 0, 0]  # You can choose the color for NoData

            # Write the colored output raster
            with rasterio.open(outputRasterFileName, 'w', driver='GTiff', height=color_array.shape[0],
                            width=color_array.shape[1], count=3, dtype='uint8', crs=srs.ExportToWkt(),
                            transform=transform) as dest:
                dest.write(color_array[:, :, 0], 1)  # Write red channel
                dest.write(color_array[:, :, 1], 2)  # Write green channel
                dest.write(color_array[:, :, 2], 3)  # Write blue channel

        # Clean up and close datasets
        del dnbr
        del mem_raster
        del out_dnbr

        print('Classification and polygonization complete. Output saved to', outputFileName)
        print('Colored raster output saved to', outputRasterFileName)




    def crop_tiff_with_shapefile(self, tiff_file, shapefile, output_tiff):
        from shapely.geometry import mapping
        from rasterio.mask import mask
        import geopandas as gpd
        import rasterio

        # Read the shapefile
        gdf = gpd.read_file(shapefile)

        # Open the TIFF file
        with rasterio.open(tiff_file) as src:
            # Convert the geometries to the same CRS as the TIFF file
            if gdf.crs != src.crs:
                gdf = gdf.to_crs(src.crs)

            # Get geometries from shapefile
            geometries = [mapping(geom) for geom in gdf.geometry]

            # Mask the raster using the shapefile geometries
            out_image, out_transform = mask(src, geometries, crop=True)

            # Update metadata
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "count": 1,
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": 0  # Set a no data value if necessary
            })

            # Write the cropped image to a new TIFF file
            with rasterio.open(output_tiff, "w", **out_meta) as dest:
                # Remove the black box by writing only the relevant data
                dest.write(out_image[0], 1)  # Write to the first band

        print(f'Cropped TIFF saved to {output_tiff}')     