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
- Open configs/config.yaml input start and end date for searching
