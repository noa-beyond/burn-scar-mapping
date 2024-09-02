import json
import os
from SatellitePassPrediction_class import SatellitePassPrediction

"""
Main script that uses the SatellitePassPrediction class to process a KML file,
extract satellite pass data, and find observation times for a specified location.
"""

# Main script
# Path to the configuration file
config_file_path = 'burn-scar-mapping/notebooks/SatellitePass/config_SatellitePass.json'
def SatellitePass_Main(config_file_path: str = 'config_SatellitePass.json'):
    with open(config_file_path, 'r') as config_file:
                    config = json.load(config_file)

    # Extract latitude and longitude from the config
    latitude = config.get("latitude")
    longitude = config.get("longitude")
    base_kml_directory = config.get("base_kml_directory")

    # Initialize an empty list to store the KML file paths
    kml_filenames = []

    # Get a list of KML files
    for f in os.listdir(base_kml_directory) :
        if f.endswith('.kml'):
            kml_file_path = os.path.join(base_kml_directory, f)
            kml_filenames.append(kml_file_path)

    print("\nkml list :", kml_filenames)
    print("Number of KML files:", len(kml_filenames))

    # Loop through each KML file and process it
    for i, kml_filename in enumerate(kml_filenames):
        # Initialize the SatellitePassPrediction object
        satellite_pass = SatellitePassPrediction(kml_filename, latitude, longitude)

        # Extract placemarks and generate GeoDataFrame
        satellite_pass.extract_placemarks_to_gdf()

        # Get observation info for the specified point
        observation_info = satellite_pass.get_observation_info()

        # Print the observation info
        if observation_info:
            print("\n------------------------------------------------------------------------------------------------------------")
            print(f"Processing file {i+1}/{len(kml_filenames)}: {kml_filename}")
            print("There are", len(observation_info), "polygons containing the point.")
            print("Observation info for the point:")
            for j, info in enumerate(observation_info, 1):
                print(f"{j}. {info}")
        else:
            print("The point is not within any of the polygons.")

if __name__ == "__main__":
    SatellitePass_Main(config_file_path)
