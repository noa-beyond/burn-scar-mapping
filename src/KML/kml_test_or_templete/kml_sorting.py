import os
import shutil

def update_local_dataset():
    # Define the base directory and subdirectories
    base_directory = 'KML_acq/update'
    s2a_directory = 'KML_acq/S2A'
    s2b_directory = 'KML_acq/S2B'

    # Ensure the base directories exist
    os.makedirs(s2a_directory, exist_ok=True)
    os.makedirs(s2b_directory, exist_ok=True)

    # Iterate through files in the base directory
    for file_name in os.listdir(base_directory):
        if file_name.endswith('.kml'):
            source_path = os.path.join(base_directory, file_name)
            
            # Check the file name to determine the appropriate directory
            if 's2a' in file_name.lower():
                destination_path = os.path.join(s2a_directory, file_name)
            elif 's2b' in file_name.lower():
                destination_path = os.path.join(s2b_directory, file_name)
            else:
                # Optionally handle unexpected file names
                print(f'Unexpected file name: {file_name}')
                continue

            # Move the file to the determined directory
            shutil.move(source_path, destination_path)
            print(f'Moved {file_name} to {destination_path}')
