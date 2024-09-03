# Burned Area Monitor
(from script FireMonitor.ipynb but added many stuff)

## Features
- Finds Sentinel 2 images from a given box (AOI) (BurnedAreaBox.json)
- Filters images with clouds, half images(where AOI is in 2 images and not in one)
- Auto Select Pre and Post Fire images
- Auto Saves NBR_PRE_FIRE.tiff, NBR_POST_FIRE.tiff
- Auto saves NDVI_PRE_FIRE.tiff, NDVI_POST_FIRE.tiff
- Auto Creates and Saves DNBR.tiff


## How to Use
- Open BurnedAreaBox.json and paste your AOI box that you copy from Sentinel Data Space
- Open **burn-scar-mapping/configs/config.yaml** input start_DATE and end_DATE for searching, cloudCover and EPSG for output raster(s)
- Run **main.py**

### Use it with Objects
- Init fire object <br />
```fire = FireMonitor(burnedAreaBox, start_DATE, end_DATE, cloudCover)``` <br /><br />
- Save RGB image using 'post' or 'pre', output tiff name and prefered EPSG <br />
```fire.save_tiff_rgb('post', 'output_name.tiff', output_EPSG)``` <br /><br />
- Save a single band using its name (see below) or save nbr and ndvi using 'nbr_post' or 'nbr_pre' and 'ndvi_post' or 'ndvi_pre' and output tiff name and prefered EPSG <br />
```fire.save_tiff_single('channel_name or nbr or ndvi' 'output_name.tiff', output_EPSG)``` <br /><br />
- Plot nbr for all dates
```fire.data.nbr.plot()```

Sentinel 2 Band names<br />
band 1 -><br />
band 2 -> blue<br />
band 3 -> green<br />
band 4 -> red<br />
band 5 -> redegde1<br />
band 6 -> rededge2<br />
band 7 -> rededge3<br />
band 8 -> nir<br />
band 8A -> nir08<br />
band 9 -> nir09<br />
band 10 -> <br />
band 11 -> swir16<br />
band 12 -> swir22<br />
