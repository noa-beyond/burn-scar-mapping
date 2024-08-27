import logging
from datetime import datetime
from test_kml_manager_class import KMLManager

# Define your directories in the main script
base_directory = 'burn-scar-mapping/notebooks/KML_acquisition_plans/update'
s2a_directory = 'burn-scar-mapping/notebooks/KML_acquisition_plans/S2A'
s2b_directory = 'burn-scar-mapping/notebooks/KML_acquisition_plans/S2B'

def job():
    logging.info("Running scheduled task...")
    # Pass the directories when creating the KMLManager object
    kml_manager = KMLManager(base_directory, s2a_directory, s2b_directory)
    try:
        kml_manager.download_kml()
        kml_manager.update_local_dataset()
    except Exception as e:
        logging.error(f'An error occurred during the scheduled task: {e}')

if __name__ == "__main__":
    # Generate a timestamped log file name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'burn-scar-mapping/notebooks/KML_acquisition_plans/test_kml_main{timestamp}.log'
    
    # Set up logging to append to the existing log file instead of overwriting it
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a'  # 'a' ensures that the log file is appended to, not overwritten
    )
    
    logging.info("Starting the scheduled task...")
    
    # Run the job
    job()
