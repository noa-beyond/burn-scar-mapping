# Burned Area Statistics

## Features
- Calculate Stats for a given Burned Area Shapefile(s)
- Export results in .csv format
- Export clipped shapefiles (inside burned area)
- Genarate Pie Chart for Corine Land Cover
- Calculate stats for multiple burned areas in one run

## Requirements
- Install **requirements.txt** <br />
geopandas==1.0.1, matplotlib==3.9.2, numpy==2.1.0, <br />
pandas==2.2.2, PyYAML==6.0.1, Shapely==2.0.6


## How to Use (Auto Version)
**1.** Put all shapefiles from Burned Areas inside a folder and specify the path into **burn-scar-mapping/configs/config_BAS.yaml** in "BurnedAreas_PATH" <br />
**2.** Put all shapefiles paths to be used for statistics into **burn-scar-mapping/configs/config.yaml**, example --> << shapefile_name_PATH >> <br />
**3.** Put the column to be used for dissolve in the **burn-scar-mapping/configs/config.yaml**, example --> << shapefile_name_COLUMN >> <br />
if unknown put 'None' in the config (not recomented) <br />
**4.** Create an output folder (or it will be created automaticaly) and specify the path into **burn-scar-mapping/configs/config.yaml** in "OutputFolder_PATH" <br />
**5.** Run **main_fullyauto.py** <br />
- The above steps will genarate stats for the Burned Area(s) from the shapefiles specified in config.yaml

## How to Use (Manual Version)
**1.** Put all shapefile(s) paths into **burn-scar-mapping/configs/config.yaml**, example --> << shapefile_name_PATH >> <br />
**2.** Edit **main.py**, add : <br />
- Add new GeoDataFrame <br />
```new_shapefile_GeoDataFrame = gp.read_file(shapefile_path)``` <br /><br />
- Initiate new Object BAStats<br />
``` stats_new_shapefile = BAStats(new_shapefile_GeoDataFrame, BurnedArea_shapefile_GeoDataFrame)``` <br /><br />
- Make use of calc_stats(), save_csv() and save_polygon() from BAStats class <br />
```stats_new_shapefile.calc_stats(column='column')```, column is used for dissolve if unknown put 'None' (not recomented)
```stats_new_shapefile.save_csv(output_path, output_name)```, save .csv file containg all calculated stats
```stats_new_shapefile.save_polygon(output_path, output_name)```, save .shp shapefile with clipped shapefile into burned area

## Output Example (Corine Land Cover)
```
Burned Area: final_burned_varnavas
Shapefile: CLC_2018_SHP_GR+CY
CRS of Shapefile:   EPSG:3035
CRS of Burned Area: EPSG:32634
CRS will be changed to EPSG:32634

Toral Burned Area(ha) 9956.2
Total Shapefile Area(ha) inside Burned Area 9956.2 

Category: 111
Area in % 0.1

Category: 112
Area in % 3.3

Category: 131
Area in % 0.2

Category: 142
Area in % 0.0

Category: 211
Area in % 1.9

Category: 212
Area in % 0.0

Category: 221
Area in % 0.1

Category: 223
Area in % 0.6

Category: 231
Area in % 0.2

Category: 242
Area in % 3.9

Category: 243
Area in % 8.0

Category: 312
Area in % 0.2

Category: 313
Area in % 0.3

Category: 323
Area in % 25.7

Category: 324
Area in % 38.9

Category: 333
Area in % 15.7

Category: 411
Area in % 0.6

Category: 512
Area in % 0.2

--------------------
```

## Genarate Corine Land Cover Pie Chart Example
![Alt text](https://github.com/noa-beyond/burn-scar-mapping/blob/nikos/src/Burned_Area_Stats/screenshots/corine_screen.png)
