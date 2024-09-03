import geopandas as gp
import rasterio as rio
from rasterio.features import rasterize


def apply_buffer(row):
    category = row['fclass']
    buffer_size = buffer_sizes.get(category, 0.1)
    return row.geometry.buffer(buffer_size)


if __name__ == "__main__":

    bunred_raster = 'C:/Praktiki/clean_raster/DNBR_XIOS_022.tif'
    roads = gp.read_file('C:/BurnedAreaStats/demo_data/BurnedAreaRoads_clipped/roads_clipped_burned_area.shp')

    with rio.open(bunred_raster) as src:
        raster = src.read(1)
        raster_meta = src.meta

    buffer_sizes = {
        'secondary': 0.3,
        'track':     0.1,
        # apo to fclass mporoume na prosthesoume oles tis kathgories
        # i default timi einai 0.1 an kapoia den oristi edw
    }
    
    roads['geometry'] = roads.apply(apply_buffer, axis=1)

    mask = rasterize(
        roads['geometry'],
        out_shape=raster.shape,
        transform=raster_meta['transform'],
        all_touched=True,
        dtype='uint8'
    )
    new_value = 0 
    new_raster = raster.copy()
    new_raster[mask == 1] = new_value

    new_raster_path = 'C:/Praktiki/clean_raster/DNBR_XIOS_022_NEW.tif'
    with rio.open(new_raster_path, 'w', **raster_meta) as dst:
        dst.write(new_raster, 1)

    mask_path = 'C:/Praktiki/clean_raster/mask.tif'
    with rio.open(mask_path, 'w', driver='GTiff', height=mask.shape[0], width=mask.shape[1], count=1, dtype=mask.dtype, crs=src.crs, transform=src.transform) as mask_dst:
        mask_dst.write(mask, 1)

    

