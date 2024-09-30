import matplotlib.pyplot as plt
import autoroot
import json
from source.OpenDataCubeFires import FireMonitor
import yaml


if __name__ == "__main__":
    
    # path to geojson file containing bounding box of burned area
    with open('configs/FireMonitoring_OpenDataCube/BurnedAreaBox.json', 'r') as file:
        burnedAreaBox = json.load(file)
    file.close()

    with open('configs/FireMonitoring_OpenDataCube/config_fire_monitor.yaml', 'r') as file_config:
        config = yaml.load(file_config, yaml.FullLoader)
        start_DATE   = config['start_DATE']
        end_DATE     = config['end_DATE']
        cloudCover   = config['cloudCover']
        EPSG         = config['EPSG']
        outputFolder = config['outputFolder']
    file_config.close()

    
    # init fire object
    fire = FireMonitor(burnedAreaBox,
                       start_DATE, 
                       end_DATE,
                       cloudCover, 
                       EPSG)
    
    # save the post and pre fire auto selected images
    #fire.save_tiff_rgb('post', outputFolder + 'post_fire_RGB.tiff')
    #fire.save_tiff_rgb('pre', outputFolder + 'pre_fire_RGB.tiff')

    #fire.save_tiff_single('nbr_post', outputFolder + 'nbr_post.tiff')
    #fire.save_tiff_single('nbr_pre', outputFolder + 'nbr_pre.tiff')

    fire.save_tiff_single('dnbr', outputFolder+'dnbr.tiff')
    
    fire.polygonize(outputFolder, 0.2)

    fire.classify(outputFolder)

    #fire.data.nbr.plot(col='time', cmap='Greys_r', col_wrap=4)
    print(f'Saving plot with pre and post images..')
    #plt.savefig('Sentinel 2 Pre and Post Fire.png', dpi=1000, format='png')
    #plt.show()

    exit()

