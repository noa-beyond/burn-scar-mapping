# Sentinel-2 Pass Prediction from KML files

## Overview
The Satellite Pass Prediction project consists of two main components: a class definition (SatellitePassPrediction_class.py) and a main script (SatellitePass_Main.py). The purpose of this project is to process satellite observation data stored in KML files, extract relevant information, and determine observation times for a specified geographic location.

## Features
- Extracts info from KML files
- Generates a GeoDataFrame
- Retrieves observation information for the specified location


## Files
### **1.** SatellitePassPrediction_class.py
This file defines the SatellitePassPrediction class, which is responsible for handling KML files, extracting geographical data, and determining when a satellite pass occurs over a specified location.

#### Key Methods
- **__init__(self, kml_file, latitude, longitude):** Initializes the class with the KML file path, latitude, and longitude of the observation point.

- **load_kml(self):** Loads the KML file and parses it using pykml and lxml libraries.

- **coordinates_to_polygon(self, coordinates):** Converts KML coordinate strings into Shapely Polygon objects.

- **extract_placemarks(self, folder, gdf_data):** Recursively extracts placemark data from the KML file and appends it to a list.

- **extract_placemarks_to_gdf(self):** Converts the extracted placemark data into a GeoDataFrame (gpd.GeoDataFrame) and sets the appropriate coordinate reference system (CRS).

- **get_observation_info(self):** Checks if the specified point (latitude, longitude) is contained within any of the polygons in the GeoDataFrame and returns relevant observation information.

### **2.** SatellitePass_Main.py
This script serves as the main entry point for processing satellite pass data. It reads configuration settings, iterates over KML files, and uses the SatellitePassPrediction class to extract and print observation information for a specific location.

#### Main Script Workflow
**1.** **Configuration Loading:** The script reads a JSON configuration file (config_SatellitePass.json) to get the latitude, longitude, and base directory containing KML files.

**2.** **KML File Collection:** The script scans the specified directory for all .kml files and collects their paths.

**3.** **Processing Each KML File:**

- For each KML file, the script initializes a SatellitePassPrediction object.
- It extracts placemark data, generates a GeoDataFrame, and retrieves observation information for the specified location.
- The script then prints out details of any satellite observation polygons that contain the specified point.

## Configuration
The script reads settings from a JSON configuration file (config_SatellitePass.json). The configuration file should contain the following keys:
- latitude: Latitude of the observation point.
- longitude: Longitude of the observation point.
- base_kml_directory: Path to the directory containing KML files.

### Sample Configuration (config_SatellitePass.json:)
```
{
    "base_kml_directory": "burn-scar-mapping/notebooks/KML_acquisition_plans/update",
    "latitude": "37.95",
    "longitude": "23.70"
}
```

## How to Use
check this notebook ()