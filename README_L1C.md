
# **Burn Scar Mapping for Sentinel L1C images**
## **Overview**:
The Purpose of this code is to respond to the need of automation for Burned Scar Mapping. The code simply for a particular fire that occured given a search range (stant and end date), the fire date and duration, the latitude and longitude of the affected area extracts the burned area based on the dnbr inxtex (Difference Normalized Burn Ratio). The code secures that the processed Sentinel L1C images have low cloud coverage since the maximum acceptable cloud coverage of the downloaded images is given be the user and therefor the extraction of the affected area is successful. 

## **Features**:
The code is composed of one main script (main_call.py) and two classes: _L1C_Downloader.py_ , _L1C_Processor.py_ which are responsible for the downloading of the required images, their processing and consequently the extraction of the burned area.

### **1. Main Code**
The main code _Main_call.py_ has the following structure:
- Loads the config file and matches the required information to variables
- Creates an object from the L1C_Downloader and an object fromt the L1C_Proseccor class
- Calls the function process_burned_area from the L1C_Proseccor class which extracts the final burned area     

### **2. Class L1C_Downloader.py**
The class _L1C_Downloader.py_ has a number of operations which achieve:
- the user certification
- the search of products that meet the cloud criteria of the user 
- the search of products that refer to a specific range of dates for Sentinel L1C products
- the selection of the final pre - fire and post - fire images that have the lower cloud coverage percentage for the given search range
- the downloading of the selected images


### **3. Class L1C_Proseccor.py**
The class _L1C_Proseccor.py_ has a number of operations which are responsible for:  
- the selection and downloading of the appropriate images that meet the given cloud critiria
- the deletion of the not-needed images
- the creation of the dnbr intex which is very important for effective Burned Scar Mapping
- the extraction of the burned area     
  

## **How to use:**
1. Fill in the config file (config_file.json) with the necessary information for the code to run. Particularly, you should fill in:
- Information that are mandatory to download sentinel - 2 images: client id, client secret, username, password
- Information that are related to a specific fire that occured in a specific area of interest, thus they are needed for the process: the range of search dates (start_date and end_date), the fire date, the fire duration and the latitude and longitude of a point inside the AOI.
- The variables that you prefer to be applied to the code regarding the percentage of cloud coverage in the downloaded image that we consider acceptable and the mask threshond which defines the burned and not burned areas.

2. Run the main script main_call.py: the images and extracted burned area will be saved in the same file with the main script and the classes. 