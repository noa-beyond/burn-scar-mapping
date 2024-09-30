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
from shapely.wkt import loads as wkt_loads
from shapely.geometry import Polygon, MultiPolygon
from scipy.ndimage import gaussian_filter1d  # Ensure this import is present




class classify:
    def __init__(self, dnbr_xr, outputFolder, FireName, EPSG):        
        
        # Classification thresholds
        dnbr_thresholds = {
            'low':      (0.10, 0.27),
            'moderate': (0.27, 0.44),
            'high':     (0.44, 0.66),
            'very high':(0.66, 1.50)
            }
        
        # define Colors for classes
        colors = {
            1: '#FFFF00', # yellow for 'low'
            2: '#FFBF00', # orange for 'moderate'
            3: '#FF8000', # dark orange for 'high'
            4: '#FF0000', # red for 'very high'
            }
        
        # get data from xarray
        dnbrData = dnbr_xr
        
        # get transform and crs
        transform = dnbrData.rio.transform()
        crs = dnbrData.rio.crs.to_wkt()
        
        # get raster size from xarray
        width = dnbrData.shape[1]
        height = dnbrData.shape[0]

        dnbr_array = dnbrData.values
        nodata_value = 0#np.nan
        
        # maska gia ta nodata values sti eikona 
        # etsi oste meta to filtro na ta epanaferoume
        no_data_mask = np.isnan(dnbr_array)
        
        class_array = np.full(dnbr_array.shape, fill_value=0, dtype=np.uint8)  # Initialize with 0
                
        # do the classification
        for index, (category, (low, high)) in enumerate(dnbr_thresholds.items()):
            mask = (dnbr_array > low) & (dnbr_array <= high)
            class_array[mask] = index + 1
            
            
        # apply filter to classification raster to smooth out noise
        class_array = median_filter(class_array, size=3)
        
        # restore unburned pixels (no data value)
        class_array[no_data_mask] = nodata_value
        
        # memory raster 
        memory_driver = gdal.GetDriverByName('MEM')
        memory_raster = memory_driver.Create('', width, height, 1, gdal.GDT_Byte)
        memory_raster.SetGeoTransform(transform.to_gdal())
        memory_raster.SetProjection(crs)
        
        # write the classification into the memory raster
        memory_band = memory_raster.GetRasterBand(1)
        memory_band.WriteArray(class_array)
        if nodata_value is not None:
            memory_band.SetNoDataValue(nodata_value)

        # create shapefile in memory
        driver = ogr.GetDriverByName('Memory')
        out_class_dnbr = driver.CreateDataSource(outputFolder + 'classified')
        
        # create epsg if needed
        srs = osr.SpatialReference()
        epsg_code = int(EPSG.split(':')[1] if isinstance(EPSG, str) else EPSG)
        srs.ImportFromEPSG(epsg_code)
        
        # create output layer
        out_layer = out_class_dnbr.CreateLayer('classified', srs=srs, geom_type=ogr.wkbPolygon)

        # add new field for the classification into the layer numbers 0 to 5
        new_field = ogr.FieldDefn('Class', ogr.OFTInteger)
        out_layer.CreateField(new_field)    
        
        # add new field for classificatin colors
        color_field = ogr.FieldDefn('Color', ogr.OFTString)
        out_layer.CreateField(color_field)
        
        # raster to vector
        gdal.Polygonize(memory_band, None, out_layer, 0, [], callback=None)
        

        for feature in out_layer:
            class_id = feature.GetField('Class')
            color = colors.get(class_id) 
            feature.SetField('Color', color)
            out_layer.SetFeature(feature)
            
        # Convert features to polygons and keep fields
        polygons = []
        class_values = []
        color_values = []
        
        for feature in out_layer:
            polygons.append(wkt_loads(feature.GetGeometryRef().ExportToWkt()))
            class_values.append(feature.GetField('Class'))
            color_values.append(feature.GetField('Color'))
        
        # Create GeoDataFrame with geometry and original fields
        gdf = gpd.GeoDataFrame({
            'geometry': polygons,
            'Class': class_values,
            'Color': color_values
        }, crs=srs.ExportToProj4())


        # make output folder
        os.makedirs(outputFolder + '/' + 'classified', exist_ok=True)
        
        gdf['geometry'] = gdf['geometry'].apply(lambda geom: self.gaussian_smooth_polygon(geom, sigma=1))
        gdf = gdf[gdf['Class'] != 0]
        
        gdf.to_file(os.path.join(outputFolder + '/' + 'Classify_Polygon' '/' + FireName + '_Classify_Polygon.shp'))
        
        



        # write rgb image of the classification
        with rasterio.open(os.path.join(outputFolder, FireName + '_Classify_Raster.tiff'),
                           'w',
                           driver='GTiff',
                           height=height,
                           width=width,
                           count=3,
                           dtype='uint8',
                           crs=crs,
                           transform=transform
                           ) as outputClassImage:
            
            color_array = np.zeros((height, width, 3), dtype=np.uint8)
            
            for class_id, hex_color in colors.items():
                if class_id == 0: # unburned pixel
                    continue
                rgb = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)] # convert hex to rgb
                color_array[class_array == class_id] = rgb
                
            color_array[no_data_mask] = [0, 0, 0]

            outputClassImage.write(color_array[:, :, 0], 1) # red
            outputClassImage.write(color_array[:, :, 1], 2) # green
            outputClassImage.write(color_array[:, :, 2], 3) # blue

        del memory_raster, out_class_dnbr
        print('Classification and polygonization complete. Output saved to', outputFolder)
        print('Colored raster output saved to', outputFolder)
        #self.save_qml(outputFolder, colors)

    def gaussian_smooth_polygon(self, geom, sigma=1):
        """Smooth the polygon using a Gaussian filter while preserving holes."""
        
        if geom.is_empty:
            return geom  # Return empty geometries unchanged

        # Handle Polygon type
        if isinstance(geom, Polygon):
            exterior = geom.exterior
            interiors = geom.interiors

            # Smooth the exterior coordinates
            x, y = exterior.xy
            x_smooth = gaussian_filter1d(x, sigma)
            y_smooth = gaussian_filter1d(y, sigma)

            # Create a new smoothed exterior polygon
            smoothed_exterior = Polygon(zip(x_smooth, y_smooth))

            # Create a list to hold smoothed interiors
            smoothed_interiors = []
            for interior in interiors:
                x_int, y_int = interior.xy
                x_int_smooth = gaussian_filter1d(x_int, sigma)
                y_int_smooth = gaussian_filter1d(y_int, sigma)
                smoothed_interiors.append(Polygon(zip(x_int_smooth, y_int_smooth)))

            # Create a new Polygon with the smoothed exterior and interiors
            if smoothed_interiors:  # Check if there are any interiors
                smoothed_polygon = Polygon(smoothed_exterior.exterior.coords, [interior.exterior.coords for interior in smoothed_interiors])
            else:
                smoothed_polygon = smoothed_exterior  # No interiors

            return smoothed_polygon

        # Handle MultiPolygon type
        elif isinstance(geom, MultiPolygon):
            smoothed_polygons = []
            for poly in geom.geoms:
                smoothed_poly = self.gaussian_smooth_polygon(poly, sigma)
                smoothed_polygons.append(smoothed_poly)
            return MultiPolygon(smoothed_polygons)

        # If geometry is not a Polygon or MultiPolygon, return it unchanged
        return geom

