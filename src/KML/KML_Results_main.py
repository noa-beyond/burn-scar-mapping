import logging
import autoroot
from datetime import datetime
from src.KML.KML_acquisition_plans.KML_Manager_class import KMLManager
from src.KML.KML_acquisition_plans.KML_Manager_main import job as job
from src.KML.SatellitePass.SatellitePassPrediction_class import SatellitePassPrediction
from src.KML.SatellitePass.SatellitePass_Main import SatellitePass_Main as SatellitePass_Main

if __name__ == "__main__":
    # Generate a timestamped log file name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'src/KML/KML_acquisition_plans/log_archive/test_kml_main{timestamp}.log'
    
    # Set up logging to append to the existing log file instead of overwriting it
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a'  # 'a' ensures that the log file is appended to, not overwritten
    )
    
    logging.info("Starting the scheduled task...")

    # Path to the configuration file
    config_file_path = 'configs/KML/config_KML_directories.json'
    
    # Run the job
    job(config_file_path)

    # Path to the configuration file
    config_file_path = 'configs/KML/config_SatellitePass.json'
    
    # Run SatellitePass_Main
    SatellitePass_Main(config_file_path)