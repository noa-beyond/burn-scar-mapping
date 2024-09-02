
# **Burn Scar Mapping for Sentinel L2A images**

## **Overview**:
The Purpose of this code is to respond to the need of automation for Burned Scar Mapping. The code simply for a particular fire that occured given a search range start and end date, the fire date and duration, the latitude and longitude of the affected area extracts the burned area based on the dnbr index (Difference Normalized Burn Ratio). The code secures that the processed Sentinel L2A images have very low cloud coverage since the maximum acceptable cloud coverage is 1% of the Area Of Interest and therefor the extraction of the affected area is successful. 

## **Features**:
The code is composed of one main script (main_call.py) and two classes: _L2A_Downloader.py_ , _LA2_Processor.py_ which are responsible for the downloading of the required images, their processing and consequently the extraction of the burned area.

### **1. Main Code**
The main code _Main_call.py_ has the following structure:
- Loads the config file and matches the required information to variables
- Creates an object from the L2A_Downloader and an object fromt the L2A_Proseccor class
- Calls the function process_burned_area from the L2A_Proseccor class which extracts the final burned area

Its worth to be noted that the images and extracted burned area will be saved in the same file with the main script and the classes.     

### **2. Class L2A_Downloader.py**
The class _L2A_Downloader.py_ has a number of operations which achieve:
- the user certification
- the search of products that meet the cloud criteria of the user 
- the search of products that refer to a specific range of dates for Sentinel L2A products
- the selection of the final pre - fire and post - fire images that meet the given criteria
- the downloading of the selected images
- the extraction of the percentage of the cloud coverage in the Area Of Interest that is given and is eccential to assess the image's quality

### **3. Class L2A_Proseccor.py**
The class _L2A_Proseccor.py_ has a number of operations which are responsible for:  
- the selection and downloading of the appropriate images that meet the given cloud critiria
- the deletion of the not-needed images
- the creation of the dnbr index which is very important for effective Burned Scar Mapping
- the extraction of the burned area     
  
## **How to use:**
1. **Fill in the configuration file** (config_file.json) with the necessary information for the code to run. Particularly, you should fill in:

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

2. **Run the main script** main_call.py: 
- From a Jupiter Notebook like the example below  
- From a Terminal  

### **Example of the configuration file** 

![Configuration](https://github.com/noa-beyond/burn-scar-mapping/blob/eleni/Configuration_File.png)    

### **Example of the Jupiter Notebook** 

![Configuration](https://github.com/noa-beyond/burn-scar-mapping/blob/eleni/Run_Jupiter.png) 