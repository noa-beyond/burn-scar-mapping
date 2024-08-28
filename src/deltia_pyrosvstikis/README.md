# Fire Reports PDFs to Databse


## Features
- Generate Excel from PDF Report
- Generate Database from PDF Reports
- Update Database for every new PDF Report (old and new entrys)

## Requirements
- Install **requirements.txt** <br />
- numpy==2.1.0, pandas==2.2.2, PyYAML==6.0.1 <br />
tabula==1.0.5, tabula_py==2.9.3, Java install locally


## How to Use (Directly)
### Single Fire Report
**1.** Put PDF path into **config_SngleFile.yaml** in "Input_PDF_File_PATH" <br />
**2.** Put  Output path to save Excel File in **config_SngleFile.yaml** in "Output_Excel_File_PATH" <br />
**3.** Run **main_singleFile.py** 
<br /><br />

### Multiple Fire Reports
**1.** Put all PDF files into a folder and folder's path into **config_multipleFiles.yaml** in "PDF_Folder_PATH" <br />
**2.** Put Database Path into **config_multipleFiles.yaml** in "Database_PATH"<br /> (if you have an old Database you can use it but it has to be generated from this script)<br />
**3.** Put Excel Output path into **config_multipleFiles.yaml** in "Excel_Files_Output_PATH" <br />
**4.** Run **main_multipleFiles.py**

#### Output
##### Single Fire Report
- Single Excel File with info from the Fire Report

##### Multiple Fire Reports
- Database containing all info from Fire Reports
- Folder containing unique Excel files from every Fire Report (can be disabled)

## How to Use (Alternative)
### Single Fire Report
- Import DeltiaFire<br />
``
from source.pyrosvestiki import DeltiaFire
``<br /><br />
- Initialize Object with pdf path<br />
``deltio = DeltiaFire(pdf_path)
``<br /><br />
- Save genarated Excel file<br />
``
deltio.save_to_excel(excel_path)
``<br />
### Multiple Fire Reports
- Make a for loop to process all PDF in the specified folder
- Use ``deltio = DeltiaFire(os.path.join(pdf_path_folder, file))`` to process every pdf
- Use ``deltio.save_to_database`` to genate (if not exists) and update the database for every new pdf file
- Use ``deltio.save_to_excel(excel_path_outputs)`` to save every pdf into a separate Excel file
```
import os
from source.pyrosvestiki import DeltiaFire
import yaml
# To A/A einai me ellinika grammata


if __name__ == "__main__":
    with open('configs/config_multipleFiles.yaml', encoding='utf8') as configFile:
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
```
