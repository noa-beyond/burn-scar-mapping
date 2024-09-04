import geopandas as gp
import autoroot
from source.BurnedAreaStats import BAStats
import matplotlib.pyplot as plt
import yaml
import os
from source.pie_chart_fnal_python import PlotCLC

if __name__ == "__main__":
    # load paths for shapefiles
    with open('configs/Burned_Area_Stats/config_BAS.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        file.close()
    
    # load Shapefiles into GeoDataFrames
    CLC_GeoDataFrame        = gp.read_file(config['CorineLandCover_PATH'])
    BSM_GeoDataFrame        = gp.read_file(config['BSM_PATH'])
    BSM_2023_GeoDataFrame   = gp.read_file(config['BSM_2023_PATH'])
    NATURA_GeoDataFrame     = gp.read_file(config['Natura2000_PATH'])
    Oikismoi_GeoDataFrame   = gp.read_file(config['Oikismoi_PATH'])
    Periferies_GeoDataFrame = gp.read_file(config['Periferies_PATH'], encoding='cp1253') # encoding mono gia auto to shapefile


    # load burned area(s) path
    BurnedAreas_PATH = config['BurnedAreas_PATH']
    # load output folder path and check if it exist, otherwise create it
    output_path      = config['OutputFolder_PATH']

    # create outpurt folder if not exist
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    # get burned areas folder names and calculate stats for all burned areas one by one
    BurnedAreas = os.listdir(BurnedAreas_PATH)

    # loop over all folder containing burned area shapefiles and calcualte stats for given shapefile
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


        # init objects with dataframes
        stats_CLC        = BAStats(CLC_GeoDataFrame, BurnedArea)
        stats_BSM        = BAStats(BSM_GeoDataFrame, BurnedArea)
        stats_BSM_2023   = BAStats(BSM_2023_GeoDataFrame, BurnedArea)
        stats_NATURA     = BAStats(NATURA_GeoDataFrame, BurnedArea)
        stats_OIKISMOI   = BAStats(Oikismoi_GeoDataFrame, BurnedArea)
        stats_Periferies = BAStats(Periferies_GeoDataFrame, BurnedArea)


        # Periferies Stats
        print('Shapefile:', str(os.path.splitext(os.path.basename(config['Periferies_PATH']))[0]))
        stats_Periferies.calc_stats(column='PER') # can laso be if unknown column=None
        stats_Periferies.save_csv(output_path, 'PERIFERIES_STATS_' + burned_area_polygon_name)
        stats_Periferies.save_polygon(output_path,  (os.path.splitext(os.path.basename(config['Periferies_PATH']))[0]))


        # Corine Land Cover Stats
        print('Shapefile:', str(os.path.splitext(os.path.basename(config['CorineLandCover_PATH']))[0]))
        stats_CLC.calc_stats(column='code_18') # can laso be if unknown column=None # code_18  # column apo pou tha paropume tis katigories
        stats_CLC.save_csv(output_path, 'CLC_STATS_' + burned_area_polygon_name)
        stats_CLC.save_polygon(output_path, str(os.path.splitext(os.path.basename(config['CorineLandCover_PATH']))[0]))


        # BSM 1984 - 2022 stats
        print('Shapefile:', str(os.path.splitext(os.path.basename(config['BSM_PATH']))[0]))
        stats_BSM.calc_stats(column='year')     # column apo pou tha paropume tis katigories # can laso be if unknown column=None
        stats_BSM.save_csv(output_path, 'BSM_STATS_' + burned_area_polygon_name)
        stats_BSM.save_polygon(output_path, str(os.path.splitext(os.path.basename(config['BSM_PATH']))[0]))


        # BSM 2023
        print('Shapefile:', str(os.path.splitext(os.path.basename(config['BSM_2023_PATH']))[0]))
        stats_BSM_2023.calc_stats(column='Id_1') # column apo pou tha paropume tis katigories # can laso be if unknown column=None
        stats_BSM_2023.save_csv(output_path, 'BSM_2023_STATS_' + burned_area_polygon_name)
        stats_BSM_2023.save_polygon(output_path, str(os.path.splitext(os.path.basename(config['BSM_2023_PATH']))[0]))


        # NATURA2000 stats
        print('Shapefile:', str(os.path.splitext(os.path.basename(config['Natura2000_PATH']))[0]))
        stats_NATURA.calc_stats(column='SITETYPE') # column apo pou tha paropume tis katigories # can laso be if unknown column=None
        stats_NATURA.save_csv(output_path, 'NATURA2000_STATS_' + burned_area_polygon_name)
        stats_NATURA.save_polygon(output_path, str(os.path.splitext(os.path.basename(config['Natura2000_PATH']))[0]))


        # Oikismoi stats
        print('Shapefile:', str(os.path.splitext(os.path.basename(config['Oikismoi_PATH']))[0]))
        stats_OIKISMOI.calc_stats(column='CODE_OIK') # column apo pou tha paropume tis katigories # can laso be if unknown column=None
        stats_OIKISMOI.save_csv(output_path, 'OIKISMOI_STATS_' + burned_area_polygon_name)
        stats_OIKISMOI.save_polygon(output_path, str(os.path.splitext(os.path.basename(config['Oikismoi_PATH']))[0]))

        # plot corine land cover pie stats and save png of plot
        PlotCLC(output_path + 'CLC_stats_' + burned_area_polygon_name + '.csv', config['CorineLandCover_JSON_PATH'])
