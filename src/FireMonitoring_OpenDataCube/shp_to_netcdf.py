import geopandas as gpd
import xarray as xr
import numpy as np

def shapefile_to_netcdf(shapefile_path, netcdf_output_path):
    # Load the shapefile
    gdf = gpd.read_file(shapefile_path)

    # Prepare data for NetCDF, converting geometries to WKT or coordinates
    gdf['geometry_wkt'] = gdf['geometry'].apply(lambda geom: geom.wkt)  # Convert to WKT
    data = {
        'geometry': gdf['geometry_wkt'].values,
        **{col: gdf[col].values for col in gdf.columns if col != 'geometry'}
    }

    # Create an xarray Dataset
    ds = xr.Dataset()

    # Add each attribute to the Dataset as a DataArray
    for key, value in data.items():
        ds[key] = (['features'], value)  # Specify the dimension name

    # Save to NetCDF
    ds.to_netcdf(netcdf_output_path)

    print(f'Successfully converted {shapefile_path} to {netcdf_output_path}')

# Example usage
#shapefile_to_netcdf('C:/Users/nikos/Desktop/greece_geofabrik/gis_osm_roads_free_1.shp', 'C:/Users/nikos/Desktop/greece_geofabrik/test.nc')

ds = xr.open_dataset('C:/Users/nikos/Desktop/greece_geofabrik/test.nc')
# Print dataset details
print("Dataset Information:")
print(ds)

# Print dimensions
print("\nDimensions:")
for dim in ds.dims:
    print(f"{dim}: {ds.dims[dim]}")

# Print variables
print("\nVariables:")
for var in ds.data_vars:
    print(f"{var}: {ds[var].dims} {ds[var].shape} {ds[var].attrs}")

# Print global attributes
print("\nGlobal Attributes:")
for attr in ds.attrs:
    print(f"{attr}: {ds.attrs[attr]}")

# Close the dataset
ds.close()