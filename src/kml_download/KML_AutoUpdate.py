# DONT RUN THIS FILE, IT IS JUST A TEMPLATE FOR THE FINAL SCRIPT

import schedule
import time

def job():
    print("Running scheduled task...")
    download_kml()
    update_local_dataset()

# Schedule the job to run every 24 hours
schedule.every(24).hours.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)


import schedule
import time
import logging
from kml_manager_class import KMLManager

def job():
    logging.info("Running scheduled task...")
    kml_manager = KMLManager()
    try:
        kml_manager.download_kml()
        kml_manager.update_local_dataset()
    except Exception as e:
        logging.error(f'An error occurred during the scheduled task: {e}')

# Schedule the job to run every 24 hours
schedule.every(24).hours.do(job)

if __name__ == "__main__":
    logging.basicConfig(filename='autoupdatemain.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting the auto-update scheduler...")
    while True:
        schedule.run_pending()
        time.sleep(1)
