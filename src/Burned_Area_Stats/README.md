# Burned Area Statistics

## Features
- Calculate Stats from a given Burned Area Shapefile(s)
- Export results in .csv format
- Export clipped shapefiles (inside burned area)
- Genarate Pie Chart for Corine Land Cover
- Calculate stats for mutiple burned areas in one run

## How to Use
**1.** Put all shapefiles from Burned Areas inside a folder and specify the path into **configs/config.yaml** in "BurnedAreas_PATH" <br />
**2.** Create an output folder (or it will be created automaticaly) and specify the path into **configs/config.yaml** in "OutputFolder_PATH" <br />
**3.** Run **main.py**
- The above steps will genarate stats for the Burned Area from the shapefiles specified in config.yaml and also the main.py if more shapefiles are needed then follow the steps

