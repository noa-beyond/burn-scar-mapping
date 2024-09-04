import geopandas as gp
import autoroot
from source.BurnedAreaStats import BAStats
import matplotlib.pyplot as plt
import yaml
import os
from source.pie_chart_fnal_python import PlotCLC

if __name__ == "__main__":
    # load path for shapefiles
    with open('configs/Burned_Area_Stats/config_BAS_auto.yaml') as file:
        config = yaml.load(file, yaml.FullLoader)
        file.close()

    
    # load all Shapefiles into GeoDataFrames in a dictionary and column keys also
    geodataframes_dict = {}
    geodataframesColumns_dict = {}
    for item in config:
        # find shapefiles in the config
        if config[item].endswith('.shp'):
            # get shapefile name from the config
            shapefile_name = os.path.splitext(os.path.basename(config[item]))[0]
            # load shapefile into geodatafeame
            gdf = gp.read_file(config[item])
            # put geodatafeame into dictionary
            geodataframes_dict[shapefile_name] = gdf

            # find column keys in config for every shapefile
            config_column_name = item.replace('_PATH', '_COLUMN')
            # actual column name inside shapefile
            column_name = config[config_column_name]
            # put column name in the dictionary for every shapefile
            geodataframesColumns_dict[shapefile_name] = column_name


    # load burned area(s) path
    BurnedAreas_PATH = config['BurnedAreas_PATH']

    # load output folder path and check if it exists or not
    out_path         = config['OutputFolder_PATH']

    # create output folder if not exists
    if not os.path.exists(out_path):
        os.mkdir(out_path)

    # get burned areas folder name and calculate stats for all burned areas one by one
    BurnedAreas = os.listdir(BurnedAreas_PATH)

    # loop over all folder(s) containing burned area(s) shapefiles and calc stats
    for BurnedArea in BurnedAreas:
        # get name of burened area shpapefile inside folder for saving later
        for filename in os.listdir(BurnedAreas_PATH + BurnedArea):
            if filename.endswith('.shp'):
                # get burned area shapefile name from folder
                BurnedArea_PATH = BurnedAreas_PATH + BurnedArea + '/' + filename
                # load burned area shapefile into a GeodataFrame
                BurnedArea = gp.read_file(BurnedArea_PATH)
                # get shapefile name only for naming the polygon of the burned area later
                burned_area_polygon_name = os.path.splitext(filename)[0]
                print('Burned Area:', burned_area_polygon_name)

        # reset output folder in every loop
        output_path = config['OutputFolder_PATH']
        # make output folder named as the burned area shapefile inside output folder
        if not os.path.exists(output_path + burned_area_polygon_name + '_stats'): 
            os.mkdir(output_path + burned_area_polygon_name + '_stats' + '/')
            output_path = output_path + burned_area_polygon_name + '_stats' + '/'
        else:
            output_path = output_path + burned_area_polygon_name + '_stats' + '/'


        # initiate all required objects with the geodataframes and burned area
        initialized_objects_dict = {}

        for shapefile_name, gdf in geodataframes_dict.items():
            # initiate object BAS from BurnedAreaStats
            initialized_object = BAStats(gdf, BurnedArea)
            # put the object in a dictionary
            initialized_objects_dict[shapefile_name] = initialized_object

        # loop over all objects and calcuate stats
        for shapefile_name, object in initialized_objects_dict.items():
            print('Shapefile:', shapefile_name)

            # calc stats
            object.calc_stats(column=geodataframesColumns_dict[shapefile_name])

            # save .csv file
            outputFileName = shapefile_name + '_' + burned_area_polygon_name + '_STATS'
            object.save_csv(output_path, outputFileName)

            # save clipped polygon
            object.save_polygon(output_path, shapefile_name)

    # plot corine land cover pie stats and save png of plot
    clc_stats_path = output_path + os.path.basename(config['CorineLandCover_PATH']).replace('.shp', '') + '_' + burned_area_polygon_name + '_STATS.csv'
    PlotCLC(clc_stats_path, config['CorineLandCover_JSON_PATH'])