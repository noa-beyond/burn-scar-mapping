import json
import logging
from datetime import datetime, timedelta
from L2A_Downloader import Downloader
from L2A_Processor import Processor

def load_config(config_path):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config

# TODO AMA DEN DINEI START DATE END DATE O XRISTIS
def main(config_path= "config_file.json", save_path = 'D:/Praktiki/burned-scar-mapping/burn-scar-mapping/src/mapping/Images_Save'):
    config = load_config(config_path)
    # Accessing the values from the config
    client_id = config['sentinelhub']['client_id']
    client_secret = config['sentinelhub']['client_secret']
    username = config['sentinelhub']['username']
    password = config['sentinelhub']['password']
    start_date = config['process_info']['start_date']
    fire_date = config['process_info']['fire_date']
    end_date = config['process_info']['end_date']
    fire_duration = config['process_info']['fire_duration']
    lat = config['process_info']['lat']
    lon = config['process_info']['lon']
    cloud_coverage_threshold = config['user_variables']['cloud_coverage_threshold']
    mask_threshold = config['user_variables']['mask_threshold']
    debug = config['debug']
   
    # Convert the string to a datetime object
    fire_date_ns = datetime.strptime(fire_date, "%Y-%m-%d")
    # Calculate pre_fire_date and post_fire_date
    pre_fire_date_ns = fire_date_ns - timedelta(days = 1)
    post_fire_date_ns = fire_date_ns + timedelta(days = fire_duration)
    # Convert back to string
    pre_fire_date = pre_fire_date_ns.strftime("%Y-%m-%d")
    post_fire_date = post_fire_date_ns.strftime("%Y-%m-%d")
    print("Pre-Fire Date:", pre_fire_date)
    print("Post-Fire Date:", post_fire_date)

    downloader = Downloader(username, password, client_id, client_secret)
    processor = Processor(downloader, cloud_coverage_threshold, mask_threshold)
    processed_dir = processor.process_burned_area(start_date,end_date,pre_fire_date,post_fire_date, lat, lon, save_path)
    # Log the result
    logging.info("Processing completed successfully.")
    logging.info(f"Processed data saved to: {processed_dir}")

if __name__ == "__main__":
    main(config_path= "L2A_config_file.json", save_path = 'D:/Praktiki/burned-scar-mapping/burn-scar-mapping/src/mapping/Images_Save')