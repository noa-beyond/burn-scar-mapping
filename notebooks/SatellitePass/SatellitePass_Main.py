import json
from SatellitePassPrediction_class import SatellitePassPrediction

"""
Main script that uses the SatellitePassPrediction class to process a KML file,
extract satellite pass data, and find observation times for a specified location.
"""

# Main script
# Path to the configuration file
config_file_path = 'burn-scar-mapping/notebooks/SatellitePass/config_SatellitePass.json'
with open(config_file_path, 'r') as config_file:
                config = json.load(config_file)

kml_filename = config.get("kml_filename")
latitude = config.get("latitude")
longitude = config.get("longitude")


# Initialize the SatellitePassPrediction object
satellite_pass = SatellitePassPrediction(kml_filename, latitude, longitude)

# Extract placemarks and generate GeoDataFrame
satellite_pass.extract_placemarks_to_gdf()

# Get observation info for the specified point
observation_info = satellite_pass.get_observation_info()

if observation_info:
    print("There are", len(observation_info), "polygons containing the point.")
    print("Observation info for the point:")
    for i, info in enumerate(observation_info, 1):
        print(f"{i}. {info}")
else:
    print("The point is not within any of the polygons.")