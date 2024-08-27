import json
import logging
from SentinelDownloader import Downloader
from SentinelProcessor import Processor

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

    config = load_config('config_file.json')  # Load credentials from config.json
    sentinelhub_config = config['sentinelhub']
    client_id = sentinelhub_config['client_id']
    client_secret = sentinelhub_config['client_secret']
    username = sentinelhub_config['username']
    password = sentinelhub_config['password']
    
    start_date = '2024-07-17'
    end_date = '2024-08-02'
    lat = 41.3754
    lon = 23.5941
    save_path = './'
    main(username, password, client_id, client_secret, start_date, end_date, output_dir, lat, lon)
