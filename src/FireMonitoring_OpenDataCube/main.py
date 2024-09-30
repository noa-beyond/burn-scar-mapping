import matplotlib.pyplot as plt
import autoroot
import json
from source.OpenDataCubeFires import FireMonitor
import yaml
from datetime import datetime, timedelta
import os

if __name__ == "__main__":
    
    # path to geojson file containing bounding box of burned area
    with open('configs/FireMonitoring_OpenDataCube/BurnedAreaBox.json', 'r') as file:
        burnedAreaBox = json.load(file)
    file.close()

    with open('configs/FireMonitoring_OpenDataCube/config_fire_monitor.yaml', 'r') as file_config:
        config = yaml.load(file_config, yaml.FullLoader)
        Fire_start_Date = config['Fire_start_Date']
        cloudCover      = config['cloudCover']
        EPSG            = config['EPSG']
        outputFolder    = config['outputFolder']
        Fire_Name       = config['Fire_Name']
        DNBR_Threshold  = config['DNBR_Threshold']
    file_config.close()

    # get 15 days before and after the fire
    Fire_start_Date = datetime.strptime(Fire_start_Date, '%Y-%m-%d')
    start_DATE = Fire_start_Date - timedelta(days=15)
    end_DATE   = Fire_start_Date + timedelta(days=15)
    #print(Fire_start_Date, start_DATE, end_DATE)
    #exit()
    os.makedirs(f'{outputFolder}{Fire_Name}', exist_ok=True)
    outputFolder = os.path.join(outputFolder, Fire_Name)
    
    
    # init fire object
    fire = FireMonitor(burnedAreaBox,
                       start_DATE,
                       end_DATE,
                       cloudCover, 
                       EPSG,
                       DNBR_Threshold,
                       outputFolder,
                       Fire_Name)
    
    # save the post and pre fire auto selected images
    #fire.save_tiff_rgb('post', outputFolder + 'post_fire_RGB.tiff')
    #fire.save_tiff_rgb('pre', outputFolder + 'pre_fire_RGB.tiff')

    #fire.save_tiff_single('nbr_post', outputFolder + 'nbr_post.tiff')
    #fire.save_tiff_single('nbr_pre', outputFolder + 'nbr_pre.tiff')

    fire.save_tiff_single('dnbr')
    
    fire.polygonize(0.2)

    fire.classify()

    #fire.data.nbr.plot(col='time', cmap='Greys_r', col_wrap=4)
    #print(f'Saving plot with pre and post images..')
    #plt.savefig(os.path.join(outputFolder, 'Sentinel 2 Pre and Post Fire.png'), dpi=1000, format='png')
    #plt.show()

    exit()

