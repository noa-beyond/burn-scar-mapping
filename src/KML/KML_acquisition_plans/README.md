# Sentinel-2 KML Downloader and Manager

## Overview
This repository contains scripts to manage the download, organization, and updating of Sentinel-2 KML files related to acquisition plans from https://sentinel.esa.int/web/sentinel/copernicus/sentinel-2/acquisition-plans. The main functionality is implemented in the KMLManager class, which downloads and sorts KML files into specified directories. Additionally, a script named test_main.py schedules and manages the execution of these tasks.

## Features
- Download KML files
- Sort KML files

## Requirements 
- install **requirements.txt**

## Files
### **1.** test_kml_manager_class.py
This script defines the KMLManager class, responsible for downloading, organizing, and updating KML files related to Sentinel-2 satellite passes.

#### Key Functions:
- **__init__():** Initializes the KMLManager with base, S2A, and S2B directories, creating them if they don't exist.

- **delete_kml_in_UpdateFile():** Deletes existing .kml files in the base directory to ensure only the most recent files are kept.

- **download_kml():** Downloads the latest KML files from the Sentinel-2 acquisition plans page, saving them to the base directory.

- **update_local_dataset():** Sorts the downloaded KML files into appropriate directories (S2A and S2B) based on their names.

### **2.** test_main.py
This script runs the KML management process, logging its activities and handling configuration through a JSON file.

#### Key Steps:
- **Configuration:** Reads the directory paths from a JSON configuration file (config_directories.json). If the config file is missing or fails to load, it falls back to default directories.

- **Logging:** Sets up logging to a timestamped log file to track the execution of the tasks.

- **Job Execution:** Calls the delete_kml_in_UpdateFile(), download_kml(), and update_local_dataset() methods of the KMLManager class to perform the task.

## Configuration
The script reads the directory paths from a JSON configuration file. The default path for this file is burn-scar-mapping/src/configs/config_directories.json. If the file is missing or an error occurs while reading it, the script uses default directory names: update (base), S2A and S2B.

### Sample Configuration (config_directories.json)
```
{
    "base_directory": "burn-scar-mapping/src/KML/KML_acquisition_plans/update",
    "s2a_directory": "burn-scar-mapping/src/KML/KML_acquisition_plans/S2A",
    "s2b_directory": "burn-scar-mapping/src/KML/KML_acquisition_plans/S2B"
}
```

## How to Use
check this notebook ()


