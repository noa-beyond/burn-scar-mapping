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




class classify:
    def __init__(self, dnbr_xr, outputFolder, EPSG):        
        
        # Classification thresholds
        dnbr_thresholds = {
            'unburned': (0.00, 0.10),
            'low':      (0.10, 0.27),
            'moderate': (0.27, 0.44),
            'high':     (0.44, 0.66),
            'very high':(0.66, np.inf)
            }
        
        # define Colors for classes
        colors = {
            0: '#FFFFFF', # white for 'unburned'
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
        nodata_value = -9999#np.nan
        
        # maska gia ta nodata values sti eikona 
        # etsi oste meta to filtro na ta epanaferoume
        no_data_mask = np.isnan(dnbr_array)
        
        class_array = np.zeros_like(dnbr_array, dtype=np.uint8)
        
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

        # create shapefile and save it
        driver = ogr.GetDriverByName('ESRI Shapefile')
        out_class_dnbr = driver.CreateDataSource(outputFolder + 'classified')
        
        # create epsg if needed
        srs = osr.SpatialReference()
        epsg_code = int(EPSG.split(':')[1] if isinstance(EPSG, str) else EPSG)
        srs.ImportFromEPSG(epsg_code)
        
        # create output layer
        out_layer = out_class_dnbr.CreateLayer('classified', srs=srs, geom_type=ogr.wkbPolygon)
        if out_layer is None:
            raise RuntimeError("Failed to create output layer.")
        # add new field for the classification into the layer numbers 0 to 5
        new_field = ogr.FieldDefn('Class', ogr.OFTInteger)
        out_layer.CreateField(new_field)    
        
        # add new field for classificatin colors
        color_field = ogr.FieldDefn('Color', ogr.OFTString)
        out_layer.CreateField(color_field)
        
        gdal.Polygonize(memory_band, None, out_layer, 0, [], callback=None)
        

        for feature in out_layer:
            class_id = feature.GetField('Class')
            color = colors.get(class_id, '#FFFFFF') # if class not found then put #FFFFFF
            feature.SetField('Color', color)
            out_layer.SetFeature(feature)
            
        # write rgb image of the classification
        with rasterio.open(outputFolder+'classified.tiff',
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
        self.save_qml(outputFolder, colors)

    def save_qml(self, outputFolder, colors):
        qml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <qgis version="3.16" >
            <layer name="classified" type="vector">
                <layerstyle>
                    <renderer-v2 type="categorizedSymbol">
                        <categories>
                            <category>
                                <filter>( "Class" = 0 )</filter>
                                <symbol>
                                    <layer type="polygon" name="0">
                                        <color>{color_0}</color>
                                        <strokeColor>#000000</strokeColor>
                                        <strokeWidth>0.5</strokeWidth>
                                    </layer>
                                </symbol>
                            </category>
                            <category>
                                <filter>( "Class" = 1 )</filter>
                                <symbol>
                                    <layer type="polygon" name="0">
                                        <color>{color_1}</color>
                                        <strokeColor>#000000</strokeColor>
                                        <strokeWidth>0.5</strokeWidth>
                                    </layer>
                                </symbol>
                            </category>
                            <category>
                                <filter>( "Class" = 2 )</filter>
                                <symbol>
                                    <layer type="polygon" name="0">
                                        <color>{color_2}</color>
                                        <strokeColor>#000000</strokeColor>
                                        <strokeWidth>0.5</strokeWidth>
                                    </layer>
                                </symbol>
                            </category>
                            <category>
                                <filter>( "Class" = 3 )</filter>
                                <symbol>
                                    <layer type="polygon" name="0">
                                        <color>{color_3}</color>
                                        <strokeColor>#000000</strokeColor>
                                        <strokeWidth>0.5</strokeWidth>
                                    </layer>
                                </symbol>
                            </category>
                            <category>
                                <filter>( "Class" = 4 )</filter>
                                <symbol>
                                    <layer type="polygon" name="0">
                                        <color>{color_4}</color>
                                        <strokeColor>#000000</strokeColor>
                                        <strokeWidth>0.5</strokeWidth>
                                    </layer>
                                </symbol>
                            </category>
                        </categories>
                    </renderer-v2>
                </layerstyle>
            </layer>
        </qgis>
        """.format(
            color_0=colors[0],
            color_1=colors[1],
            color_2=colors[2],
            color_3=colors[3],
            color_4=colors[4]
        )
        
        qml_file_path = os.path.join(outputFolder, 'classified.qml')
        with open(qml_file_path, 'w') as qml_file:
            qml_file.write(qml_content)
        print('QML style file saved to', qml_file_path)