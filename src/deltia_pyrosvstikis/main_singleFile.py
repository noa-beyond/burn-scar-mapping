from pyrosvestiki import DeltiaFire
import yaml
import os
# To A/A einai me ellinika grammata


if __name__ == "__main__":

    with open('configs/config_singleFile.yaml', encoding='utf8') as configFile:
        config = yaml.load(configFile, yaml.FullLoader)
        
    pdf_path   = config['Input_PDF_File_PATH']
    excel_path = config['Output_Excel_File_PATH']

    # Orizoume ena oject typou pyrosvestiki kai bazoume mesa ta DataFrames
    # pernoume tous pinakes apo to arxeio .pdf kai ta bazoume se ena DataFrame
    deltio = DeltiaFire(pdf_path)

    # apothikeusi kathe deltiou 3exorista
    deltio.save_to_excel(excel_path)

    print('Done!')

