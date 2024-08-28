import os
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
import logging

class KMLManager:
    '''
        Downloads and sorts kml files for Sentinel 2 passes
        input: directories
        output: None
    '''
    def __init__(
            self, 
            base_directory: str = 'update', 
            s2a_directory: str = 'S2A', 
            s2b_directory: str = 'S2B',
            ):
        
        self.base_directory = base_directory
        self.s2a_directory = s2a_directory
        self.s2b_directory = s2b_directory

        # Ensure directories exist
        os.makedirs(self.base_directory, exist_ok=True)
        os.makedirs(self.s2a_directory, exist_ok=True)
        os.makedirs(self.s2b_directory, exist_ok=True)

        # Set up logging
        #logging.basicConfig(filename='kml_manager.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def download_kml(self):
        KML_url = 'https://sentinel.esa.int/web/sentinel/copernicus/sentinel-2/acquisition-plans'
        base_url = 'https://sentinel.esa.int/'
        response = requests.get(KML_url)
        sentinel_types = ['sentinel-2a', 'sentinel-2b']
        save_directory = self.base_directory
        os.makedirs(save_directory, exist_ok=True)

        if response.status_code == 200:
            logging.info('Response OK!')

            # Parse the HTML content
            html_content = BeautifulSoup(response.content, 'html.parser')
            
            for sentinel_type in sentinel_types:
                elements = html_content.find_all(class_=sentinel_type)

                if elements:
                    for element in elements:
                        # Find all links within the element
                        links = element.find_all('a')

                        for link in links:
                            if 'href' in link.attrs:
                                file_url = link['href']
                                link_text = link.get_text(strip=True)
                                logging.info(f'Downloading {link_text} from {base_url + file_url}')

                                # Normalize case of the file name, Construct the file path and full URL
                                file_name = os.path.basename(file_url).lower() + '.kml'  # Normalize case here
                                full_file_url = base_url + file_url
                                file_path = os.path.join(save_directory, file_name)

                                # Download the file
                                try:
                                    # Download the file
                                    urlretrieve(full_file_url, file_path)
                                    logging.info(f'Successfully downloaded {file_name} from {full_file_url} to {file_path}')
                                except Exception as e:
                                    logging.error(f'Failed to download {file_name} from {full_file_url}: {e}')

                            else:
                                logging.warning('No href attribute found for a link in element class {sentinel_type}.')
                else:
                    logging.warning(f'No elements found for sentinel type: {sentinel_type}')
        else:
            logging.error(f'Failed to retrieve KML page, status code: {response.status_code}')    

        return 0

    def update_local_dataset(self):
        # Iterate through files in the base directory
        for file_name in os.listdir(self.base_directory):
            
            if file_name.endswith('.kml'):
                source_path = os.path.join(self.base_directory, file_name)

                # Check the file name to determine the appropriate directory
                if 's2a' in file_name:
                    destination_path = os.path.join(self.s2a_directory, file_name)
                elif 's2b' in file_name:
                    destination_path = os.path.join(self.s2b_directory, file_name)
                else:
                    logging.warning(f'Unexpected file name: {file_name}')
                    continue

                # Move the file to the determined directory
                try:
                    shutil.move(source_path, destination_path)
                    logging.info(f'Successfully moved {file_name} to {destination_path}')
                except Exception as e:
                    logging.error(f'Failed to move {file_name} from {source_path} to {destination_path}: {e}')
            else:
                logging.warning(f'Skipped non-KML file: {file_name}')