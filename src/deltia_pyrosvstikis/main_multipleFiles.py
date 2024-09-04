import os
import autoroot
from source.pyrosvestiki import DeltiaFire
import yaml
# To A/A einai me ellinika grammata


if __name__ == "__main__":
    with open('configs/Deltia_pyrosvestikis/config_deltia_multipleFiles.yaml', encoding='utf8') as configFile:
        config = yaml.load(configFile, yaml.FullLoader)

    pdf_path_folder    = config['PDF_Folder_PATH']
    database_path      = config['Database_PATH']
    excel_path_outputs = config['Excel_Files_Output_PATH']

    for file in os.listdir(pdf_path_folder):
        if file.endswith('.pdf'):
            print('Processing file:', file)
            # Orizoume ena oject typou pyrosvestiki kai bazoume mesa ta DataFrames
            deltio = DeltiaFire(os.path.join(pdf_path_folder, file))

            # enimerosi tou excel me ta proigoumena deltia kai prosthiki twn newn entrys
            deltio.save_to_database(database_path)
            
            # apothikeusi kathe deltiou 3exorista
            deltio.save_to_excel(excel_path_outputs)
            print('\n')
    print('Done!')
