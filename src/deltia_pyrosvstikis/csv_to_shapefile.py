import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt

def csv_to_shapefile(input_csv, output_shapefile, geometry_column='the_geom', crs="EPSG:2100"):
    # Step 1: Load the CSV file into a DataFrame
    df = pd.read_csv(input_csv)
    
    # Step 2: Convert the 'geometry' column from WKT format to actual geometries
    df[geometry_column] = df[geometry_column].apply(wkt.loads)
    
    # Step 3: Create a GeoDataFrame from the DataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometry_column)
    
    # Step 4: Set the coordinate reference system (CRS)
    gdf.set_crs(crs, inplace=True)
    
    # Step 5: Save the GeoDataFrame as a Shapefile
    gdf.to_file(output_shapefile, driver='ESRI Shapefile', encoding='utf-8')

# Example usage:
input_csv = 'C:/Users/nikos/Desktop/greece_dimoi/KAPODISTRIAS/greece_dimoi_kapodistrias.csv'  # Path to the input CSV file
output_shapefile = 'C:/Users/nikos/Desktop/greece_dimoi/KAPODISTRIAS/dimoi_kapodistrias.shp'  # Path to the output Shapefile


csv_to_shapefile(input_csv, output_shapefile)
