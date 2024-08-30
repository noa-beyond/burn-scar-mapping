import json
import logging
from ExpAOISentinelDownloader import Downloader
from ExpAOISentinelProcessor import Processor

def load_config(config_path):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config

def main(username, password, client_id, client_secret, start_date, end_date, output_dir, lat, lon):
    downloader = Downloader(username, password, client_id, client_secret)
    processor = Processor(downloader)
    processed_dir = processor.process_burned_area(start_date, end_date, lat, lon, save_path)
    # Log the result
    logging.info("Processing completed successfully.")
    logging.info(f"Processed data saved to: {processed_dir}")

if __name__ == "__main__":

    config = load_config('config_file.json')
    # Accessing the values from the config
    client_id = config['sentinelhub']['client_id']
    client_secret = config['sentinelhub']['client_secret']
    username = config['sentinelhub']['username']
    password = config['sentinelhub']['password']
    start_date = config['process_info']['start_date']
    end_date = config['process_info']['end_date']
    lat = config['process_info']['lat']
    lon = config['process_info']['lon']
    cloud_coverage_threshold = config['user_variables']['cloud_coverage_threshold']
    mask_threshold = config['user_variables']['mask_threshold']

    debug = config['debug']
    #save_path = './'
    save_path = 'D:/Praktiki/burned-scar-mapping/burn-scar-mapping/src/mapping/Images_Save'
    main(username, password, client_id, client_secret, start_date, end_date, save_path, lat, lon)