
# **Burn Scar Mapping for Sentinel L1C images**

## **Overview**:
The Purpose of this code is to respond to the need of automation for Burned Scar Mapping. The code simply for a particular fire that occured given a search range: start and end date, the fire date and duration, the latitude and longitude of the affected area, extracts the burned area based on the dnbr index (Difference Normalized Burn Ratio). The code secures that the processed Sentinel L1C images have low cloud coverage since the maximum acceptable cloud coverage of the downloaded images is given by the user and therefor the extraction of the affected area is successful. 

## **Features**:
The code is composed of one main script (L1C_main.py) and two classes: _L1C_Downloader.py_ , _L1C_Processor.py_ which are responsible for the downloading of the required images, their processing and consequently the extraction of the burned area.

### **1. Main Code**
The main code L1C_main.py has the following structure:
- Loads the configuration file and matches the required information to variables
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
- the creation of the dnbr index which is very important for effective Burned Scar Mapping
- the extraction of the burned area     

## **How to use:**
1. **Fill in the configuration file** (L1C_config_file.json) with the necessary information for the code to run. Particularly, you should fill in:

- Information that are mandatory to download Sentinel - 2 images: 
    - client id
    - client secret 
    - username
    - password

- Information that are related to a specific fire that occured in a specific area of interest, thus they are needed for the process: 
    - the range of search dates (start_date and end_date)
    - the fire date
    - the fire duration
    - the latitude and longitude of a point inside the AOI

- The variables that you prefer to be applied to the code:
    - the percentage of cloud coverage in the downloaded image that we consider acceptable 
    - the mask threshond which defines the burned and not burned areas.

2. **Run the main script** L1C_main.py: 
- From a Jupyter Notebook like the example below  
- From a Terminal  

### **Example of the configuration file** 

![Configuration](https://github.com/noa-beyond/burn-scar-mapping/blob/eleni/Configuration_File.png)    

### **Example Jupyter Notebook** 

![Configuration](https://github.com/noa-beyond/burn-scar-mapping/blob/eleni/Run_Jupyter_L1C.png) 
