import xarray as xr
from source.polygonize import polygonize
import rasterio
from source.classify import classify

filePath = 'C://burned-scar-mapping//burn-scar-mapping//src//FireMonitoring_OpenDataCube//dnbr.nc'

dnbr = xr.open_dataset(filePath)
dnbr.rio.write_crs('EPSG:32635', inplace=True)

outputFolder = 'C://burned-scar-mapping//burn-scar-mapping//src//FireMonitoring_OpenDataCube//output//'
polygonizer = polygonize(outputFolder, 'EPSG:32635', 0.2, dnbr['nbr'])

croped_dnbr = polygonizer.crop_dnbr()

classify = classify(croped_dnbr, outputFolder, 'EPSG:32635')