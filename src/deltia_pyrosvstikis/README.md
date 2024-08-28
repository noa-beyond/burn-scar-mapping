# Fire Reports PDFs to Databse


## Features
- Generate Excel from PDF Report
- Generate Database from PDF Reports
- Update Database for every new PDF Report (old and new entrys)

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
