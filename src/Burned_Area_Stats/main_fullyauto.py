import geopandas as gp
from source.BurnedAreaStats import BAStats
import matplotlib.pyplot as plt
import yaml
import os
from source.pie_chart_fnal_python import PlotCLC

if __name__ == "__main__":
    # load path for shapefiles
    with open('configs/config_auto.yaml') as file:
        config = yaml.load(file, yaml.FullLoader)

    print(config)    