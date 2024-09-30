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
from shapely.wkt import loads as wkt_loads





class polygonize:
    def __init__(self, outputFolder, EPSG, threshold, dnbr_xr):
        # dnbr from xarray
        dnbrData = dnbr_xr
        
        # get transform of dnbrData array
        transform = dnbrData.rio.transform()
        crs = dnbrData.rio.crs.to_wkt()
        
        # dimensions of dnbr image
        width = dnbrData.shape[1]
        height = dnbrData.shape[0]
        
        
        # apply threshold while first make xarray numpy array
        dnbrData_array = dnbrData.values
        # make >= from threshold values = 1 and everything else 0
        masked_array = np.where(dnbrData_array >= threshold, 1, 0)

        # create in memory raster to hold temp raster
        memory_driver = gdal.GetDriverByName('MEM')
        memory_raster = memory_driver.Create('', width, height, 1, gdal.GDT_Byte)
        # set geo trasform
        #memory_raster.SetGeoTransform(transform.to_gdal())
        memory_raster.SetGeoTransform(transform.to_gdal())
        memory_raster.SetProjection(crs)

        # write mask into memory raster
        memory_band = memory_raster.GetRasterBand(1)
        memory_band.WriteArray(masked_array)
        nodata_value = np.nan
        memory_band.SetNoDataValue(0)    
        

        # create output Shapefile
        driver = ogr.GetDriverByName('Memory')
        out_dnbr = driver.CreateDataSource(outputFolder)
        
        # create EPSG code 
        srs = osr.SpatialReference()
        epsg_code = int(EPSG.split(':')[1] if isinstance(EPSG, str) else EPSG)
        srs.ImportFromEPSG(epsg_code)
        
        # output layer for the shapefile
        out_layer = out_dnbr.CreateLayer('polygonized', srs=srs, geom_type=ogr.wkbPolygon)

        # add a new field to store pixel values 0 or 1
        new_field = ogr.FieldDefn('DN', ogr.OFTInteger)
        out_layer.CreateField(new_field)
        
        # polygonize the masked layer
        gdal.Polygonize(memory_band, None, out_layer, 0, [], callback=None)


        # filter poltgons with DN = 1
        # Copy only DN = 1 polygons to a new GeoDataFrame (filtered in memory)
        polygons = []
        for feature in out_layer:
            if feature.GetField('DN') == 1:
                geom_wkt = feature.GetGeometryRef().ExportToWkt()
                polygons.append(wkt_loads(geom_wkt))  # Convert WKT to shapely geometry

         # Convert list of polygons into a GeoDataFrame
        gdf = gpd.GeoDataFrame({'geometry': polygons}, crs=srs.ExportToProj4())

        # make output folder to store the shapefile
        os.makedirs(outputFolder + '/' + 'DNBR_Polygon', exist_ok=True)
        
        # Find the largest polygon and save it
        largest_polygon = gdf.loc[gdf.geometry.area.idxmax()]
        largest_polygon_filename = outputFolder + '/' + 'DNBR_Polygon' + '/' + 'polygon.shp'     

        # Save the largest polygon
        largest_gdf = gpd.GeoDataFrame([largest_polygon], columns=gdf.columns, crs=gdf.crs)
        largest_gdf.to_file(largest_polygon_filename)
        print('Polygon Created! Output saved to', largest_polygon_filename)
        

        # used in crop only
        self.polygonName = largest_polygon_filename # only used in crop
        self.dnbr = dnbrData    





    def crop_dnbr(self):
        return self.crop_dnbr_to_shapefile(self.polygonName, self.dnbr)
    

    def crop_dnbr_to_shapefile(self, shapefile, dnbr):
        #shapefile = self.polygonName
        #dnbr = self.dnbr
        
        # Load the shapefile using geopandas
        polygon_gdf = gpd.read_file(shapefile)

        # Ensure CRS of shapefile matches with DNBR data
        dnbr_crs = dnbr.rio.crs
        polygon_crs = polygon_gdf.crs
        
        if dnbr_crs.to_epsg() != polygon_crs.to_epsg():
            # Reproject shapefile to match the DNBR CRS if necessary
            polygon_gdf = polygon_gdf.to_crs(dnbr_crs)
        
        # Use rioxarray to crop the self.dnbr data based on the polygon geometry
        cropped_dnbr = dnbr.rio.clip(polygon_gdf.geometry, polygon_gdf.crs, drop=True)
        
        return cropped_dnbr