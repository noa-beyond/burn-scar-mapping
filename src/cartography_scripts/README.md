# burn-scar-mapping
Burn Scar Mapping collection of scripts

# 1. Map Visualization Script

## Overview
This script creates a detailed map visualization of wildfire impacts. It reads geospatial data from a shapefile, processes it, and generates a high-quality map with various features including an inset map, annotations, and logos. The final output is saved as an image file.

## Script Breakdown

### 1. Load Configuration

```python
# Load the configuration from the YAML file
with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
```

### 2. Load and Prepare Shapefiles

```python
# Load the shapefiles
shapefile1 = gpd.read_file(config['shapefiles']['path1'])
shapefile2 = gpd.read_file(config['shapefiles']['path2'])


# Set and reproject CRS
shapefile1.crs = config['shapefiles']['epsg1']
shapefile2.crs = config['shapefiles']['epsg2']
shapefile1 = shapefile1.to_crs(epsg=4326)  # Reproject in WGS84
shapefile2 = shapefile2.to_crs(epsg=4326)  # Reproject in WGS84
```

Purpose: Loads the shapefiles, sets their Coordinate Reference System (CRS) to their EPSG respectively, and reprojects them to WGS84 (EPSG:4326).

### 3. Calculate Extent, Create Bounding Box, Bound the Shapefiles

```python
# Get the bounding box of the larger shapefile
x_min, y_min, x_max, y_max = shapefile1.total_bounds
width = x_max - x_min
height = y_max - y_min

# Optionally adjust the bounding box size
expansion_factor = config['map']['expansion_factor']
x_min -= width * expansion_factor
x_max += width * expansion_factor
y_min -= height * expansion_factor
y_max += height * expansion_factor

# Create a polygon for the bounding box
bbox_polygon = Polygon([(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max), (x_min, y_min)])
bbox_gdf = gpd.GeoDataFrame({'geometry': [bbox_polygon]}, crs=shapefile1.crs)

# Filter shapefile2 to only include points within the bounding box of shapefile1
bounded_shapefile2 = shapefile2[shapefile2.geometry.within(bbox_polygon)]

```

Purpose: Defines and expands the bounding box for the map and converts it into a GeoDataFrame for plotting while bounding the two shapefiles.

### 4. Create Main Plot and Customize Axis Appearance

```python
# Create the plot
fig, ax = plt.subplots(figsize=(10, 10))
shapefile1.plot(ax=ax, edgecolor='red', facecolor='none', alpha=0.5, hatch='/////', legend=True)
bounded_shapefile2.plot(ax=ax, edgecolor='black', facecolor='white', markersize=50, alpha=1, marker='o', legend=True)

# Annotate the names of the areas
for idx, row in bounded_shapefile2.iterrows():
    plt.annotate(text=row['name'], xy=(row.geometry.centroid.x, row.geometry.centroid.y), xytext=(3, 3), textcoords='offset points', fontsize=8, color='white') # change name according to column name of the settlements

# Add the satellite basemap using contextily
ctx.add_basemap(ax, crs=shapefile1.crs.to_string(), source=ctx.providers.Esri.WorldImagery)
plt.tight_layout()

# Set the coordinates to be displayed vertically
ax.tick_params(axis='x', rotation=0)
ax.tick_params(axis='y', rotation=90)

# Set the format for the coordinates
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.3f}'))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.3f}'))
```

Purpose: Initializes the plot, styles the shapefiles, adds a basemap, adjusts the layout and rotates axis ticks and formats their labels for readability.

### 5. Calculate Scale

```python
# Calculate latitude and longitude ranges
lat_mid = (y_max + y_min) / 2  # Use the midpoint latitude for accuracy
cos_lat = np.cos(np.radians(lat_mid))  # Cosine of the latitude for longitude adjustment

# Improved horizontal and vertical scales in meters
scale_x = (x_max - x_min) * 111000 * cos_lat  # Horizontal scale adjusted for latitude
scale_y = (y_max - y_min) * 111000  # Vertical scale remains the same

# Determine the maximum scale for consistency
scale = max(scale_x, scale_y)

# Calculate the scale ratio for the map (e.g., 1:100000)
# Assuming your map is being displayed at a specific width in pixels, you can use that to get the scale ratio
real_world_width_meters = scale_x  # The real-world width represented by the map

scale_ratio = real_world_width_meters / width  # Meters per pixel

# Determine the appropriate scale text
scale_text = f"Scale: 1:{int(scale_ratio)}"
```

Purpose: Computes the scale for the map based on its extent and prepares the scale text.

### 6. Create Inset Map

```python
# Create the inset map showing the area of interest (AOI)
expansion_factor = config['map']['expansion_factor2'] 
x_min_ = x_min + (width * expansion_factor)
x_max_ = x_max - (width * config['map']['ysize'] * expansion_factor)
y_min_ = y_min + (height * expansion_factor)
y_max_ = y_max - (height * expansion_factor)

aoi_polygon = Polygon([(x_min-0.1, y_min-0.1), (x_max+0.1, y_min-0.1), (x_max+0.1, y_max+0.1), (x_min-0.1, y_max+0.1)]) #adjust size of red square
aoi_polygon_ = Polygon([(x_min_, y_min_), (x_max_, y_min_), (x_max_, y_max_), (x_min_, y_max_)])
aoi_gdf = gpd.GeoDataFrame(geometry=[aoi_polygon], crs=shapefile1.crs)
aoi_gdf_ = gpd.GeoDataFrame(geometry=[aoi_polygon_], crs=shapefile1.crs)

# Adjust the coordinates for the inset to be placed under the title
inset_ax = fig.add_axes([config['map']['x'], config['map']['y'], config['map']['width'], config['map']['height']])
aoi_gdf_.plot(ax=inset_ax, edgecolor='red', facecolor='none', alpha=0, legend=True)
aoi_gdf.plot(ax=inset_ax, edgecolor='red', facecolor='none', alpha=1, linewidth=3, legend=True)
ctx.add_basemap(inset_ax, crs=shapefile1.crs.to_string(), source=ctx.providers.Esri.WorldImagery)
inset_ax.set_xticks([])
inset_ax.set_yticks([])
inset_ax.set_xlabel('')
inset_ax.set_ylabel('')
```

Purpose: Defines the extent and appearance of an inset map to show the area of interest and adds it to the main figure.

### 7. Add Title, Legend, and Annotations

```python
# Add title
plt.text(config['firehub']['x'], config['firehub']['y'], config['firehub']['name'], transform=ax.transAxes, rotation=0, va='top', fontweight='bold', fontsize=20, color='red') 

xtext = config['text_position']['x']
ytext = config['text_position']['y']

# Add legend
plt.text(xtext, ytext + config['ypomnima']['y'], config['ypomnima']['name'], transform=ax.transAxes, rotation=0, ha='left', va='baseline', fontweight='bold', fontsize=10) 
bbox_gdf.plot(ax=ax, edgecolor='red', facecolor='red', alpha=0, legend=True) 
plt.plot(shapefile1[config['ypomnima']['id_name1']], label=config['ypomnima']['label1'])
plt.plot(bounded_shapefile2[config['ypomnima']['id_name2']], label=config['ypomnima']['label2'])
fire = mpatches.Patch(edgecolor='red', facecolor='none', alpha=0.5, hatch='/////', label=config['ypomnima']['label1'])
settlement = Line2D([0], [0], marker='o', color='w', label=config['ypomnima']['label2'], markerfacecolor='white', markeredgecolor='black', markersize=10, alpha=0.5)
plt.legend(loc='right', title_fontproperties=fm.FontProperties(weight='bold'), bbox_to_anchor=(config['ypomnima']['xlabel'], config['ypomnima']['ylabel']), borderaxespad=0, frameon=False, handles=[settlement, fire])
```

Purpose: Adds title, legend, and a text annotations to the main plot.

### 8. Get Current Date, Add Standardized Text with Map Information

```python
# Get the current date
today = datetime.today().date()
today = today.strftime("%d/%m/%Y")

# Add standardised text on the side of the map
plt.text(xtext, config['place']['y'], config['place']['name'], transform=ax.transAxes, rotation=0, ha='left', va='baseline', fontweight='bold', fontsize=16)
plt.text(xtext, config['subtitle']['y'], config['subtitle']['name'], transform=ax.transAxes, fontsize=11, va='top', fontweight='bold')
plt.text(config['production_date']['x'], config['production_date']['y'], config['production_date']['name'] + today, transform=ax.transAxes, fontsize=10, va='top')
plt.text(xtext, ytext + 0.335, scale_text, transform=ax.transAxes, fontsize=8, va='center', fontweight='bold')
plt.text(xtext, ytext + config['map_information']['y_name'], config['map_information']['name'], transform=ax.transAxes, fontsize=10, va='center', fontweight='bold')
plt.text(xtext, ytext + config['map_information']['y_text'], config['map_information']['text1'].replace('{place}', config['place']['name']) + config['map_information']['text2'].replace('{detection}', config['dates']['detection']) + config['map_information']['text3'].replace('{area}', config['area']), transform=ax.transAxes, fontsize=8, va='center')
plt.text(xtext, ytext + config['sources']['y_name'], config['sources']['name'], transform=ax.transAxes, fontsize=10, va='center', fontweight='bold')
plt.text(xtext, ytext + config['sources']['y_text'], config['sources']['product'] + config['sources']['text'].replace('{download}', config['dates']['download']), transform=ax.transAxes, fontsize=8, va='center')
# plt.text(xtext, ytext + config['publication']['y_name'], config['publication']['name'], transform=ax.transAxes, fontsize=10, va='center', fontweight='bold')
# plt.text(xtext, ytext + config['publication']['y_text'], config['publication']['text'], transform=ax.transAxes, fontsize=8, va='center')
plt.text(xtext, ytext + config['team']['y_name'], config['team']['name'], transform=ax.transAxes, fontsize=10, va='center', fontweight='bold')
plt.text(xtext, ytext + config['team']['y_text'], config['team']['text'], transform=ax.transAxes, fontsize=8, va='center')
plt.text(xtext, ytext + config['contact_details']['y_name'], config['contact_details']['name'], transform=ax.transAxes, fontsize=10, va='center', fontweight='bold')
plt.text(xtext, ytext + config['contact_details']['y_text'], config['contact_details']['text'], transform=ax.transAxes, fontsize=8, va='center')
```

Purpose: Gets current date and adds standardized text

### 9. Add Logos

```python
# Add north
logo_image = plt.imread(config['logos']['north'])
logo_plot = OffsetImage(logo_image, zoom=0.7)  #adjust zoom to control logo size
ab = AnnotationBbox(logo_plot, (config['logos']['x_north'], ytext + config['logos']['y_north']), xycoords='axes fraction', frameon=False) #adjust position of north arrow
ax.add_artist(ab)

# Add logos to the plot
logo_paths = [
    (config['logos']['first'], 0.185),
    (config['logos']['second'], 0.08),
    (config['logos']['third'], 0.123),
    (config['logos']['fourth'], 0.5)
]

# Adjusted coordinates for logos placed side by side
for i, (logo_path, zoom) in enumerate(logo_paths):
    logo_image = plt.imread(logo_path)
    logo_plot = OffsetImage(logo_image, zoom=zoom)
    ab = AnnotationBbox(logo_plot, (config['logos']['x'] + i*0.25, config['logos']['y']), xycoords='axes fraction', frameon=False) #adjust position of logos
    ax.add_artist(ab)
```

Purpose: Adds logos and a north arrow to the map.

### 10. Save and Crop Image

```python
# Save the figure
burned_map = config['images']['burned_map']
cropped_burned_map = config['images']['cropped_burned_map']
plt.savefig(burned_map, dpi=config['images']['dpi'], bbox_inches='tight')

# # Show the plot
# plt.show()

# Close the figure to release memory
plt.close(fig)

# Load the image
image = Image.open(burned_map)

# Get the dimensions of the original image
width, height = image.size

# Define the crop area
left = 0       # Keep the left side as is
upper = 0      # Keep the top side as is
right = width - config['images']['crop_factor']  # Crop x pixels from the right
lower = height  # Keep the bottom side as is

# Crop the image
cropped_image = image.crop((left, upper, right, lower))

# Save the cropped image
cropped_image.save(cropped_burned_map)

# Delete the original image
os.remove(burned_map)

# Optionally, show the cropped image
cropped_image.show()
```
Purpose: Saves the final map image, crops the right side, and optionally displays the cropped image.

## Dependencies

To run this script, you will need the following Python libraries:

- **geopandas**: For working with geospatial data, reading shapefiles, and performing spatial operations.
- **matplotlib**: For creating plots, customizing map visualizations, and adding text, legends, and annotations.
    
    Specific submodules used:
  1. **matplotlib.pyplot**: For general plotting.
  2. **matplotlib.patches**: For adding custom patches like polygons or rectangles.
  3. **matplotlib.lines.Line2D**: For creating custom lines and markers.
  4. **matplotlib.offsetbox.OffsetImage and AnnotationBbox**: For placing images (e.g., logos) on the plot.
  5. **matplotlib.font_manager**: For managing fonts and font properties.
- **mpl_toolkits.axes_grid1**: For creating inset axes, which are smaller axes placed inside the main axes.

    Specific submodules used:
  1. **inset_locator**: To add inset axes to the main plot.
  2. **make_axes_locatable**: To create a divider for easily placing colorbars or other elements.
- **shapely.geometry.Polygon**: For creating and manipulating geometric shapes, particularly polygons representing bounding boxes.
- **contextily**: For adding basemaps (such as satellite imagery) to the plots.
- **Pillow**: For image processing, including loading, cropping, and saving images.
- **numpy**:For numerical operations, particularly for handling coordinate transformations and scaling.
- **yaml**:For loading and parsing configuration files written in YAML format.
- **json**:Although not currently active in the script (commented out), it's used for loading configuration from a JSON file (if needed).
- **os**:For interacting with the file system, such as removing files.
- **datetime**:For working with dates and times, particularly for adding the current date to the map.

### Installation

You can install the required libraries using Conda. Run the following commands:

```bash
conda create -n my_environment python=your_python_version
conda activate my_environment
conda install -c conda-forge geopandas matplotlib shapely contextily pillow numpy pyyaml
```

## Files

config.yaml: Configuration file with everything that needs to be adjusted.\
Shapefiles containing the geospatial data.\
Logos and images used in the script.

# 2. Map Comparisson Script

## Overview
This script creates a detailed map visualization of 2 wildfire impacts and compares them. It reads geospatial data from shapefile, processes it, and generates a high-quality map with various features including an inset map, annotations, and logos. The final output is saved as an image file.

## Script Breakdown

### 1. Load Configuration

```python
# Load the configuration from the YAML file
with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
```

### 2. Load and Prepare Shapefiles

```python
# Load the shapefiles
shapefile1 = gpd.read_file(config['shapefiles']['path1'])
shapefile2 = gpd.read_file(config['shapefiles']['path2'])
shapefile3 = gpd.read_file(config['shapefiles']['path3'])

# Set and reproject CRS
shapefile1.crs = config['shapefiles']['epsg1']
shapefile2.crs = config['shapefiles']['epsg2']
shapefile3.crs = config['shapefiles']['epsg3']
shapefile1 = shapefile1.to_crs(epsg=4326)  # Reproject in WGS84
shapefile2 = shapefile2.to_crs(epsg=4326)  # Reproject in WGS84
shapefile3 = shapefile3.to_crs(epsg=4326)  # Reproject in WGS84

```

Purpose: Loads the shapefiles, sets their Coordinate Reference System (CRS) to their EPSG respectively, and reprojects them to WGS84 (EPSG:4326).

### 3. Calculate Extent, Create Bounding Box, Bound the Shapefiles

```python
# Get the bounding box of the larger shapefile
x_min, y_min, x_max, y_max = shapefile1.total_bounds
width = x_max - x_min
height = y_max - y_min

# Optionally adjust the bounding box size
expansion_factor = config['map']['expansion_factor']
x_min -= width * expansion_factor
x_max += width * expansion_factor
y_min -= height * expansion_factor
y_max += height * expansion_factor

# Create a polygon for the bounding box
bbox_polygon = Polygon([(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max), (x_min, y_min)])
bbox_gdf = gpd.GeoDataFrame({'geometry': [bbox_polygon]}, crs=shapefile3.crs)

# Filter shapefile2 to only include points within the bounding box of shapefile1
bounded_shapefile1 = shapefile1[shapefile1.geometry.within(bbox_polygon)]
bounded_shapefile2 = shapefile2[shapefile2.geometry.within(bbox_polygon)]
```

Purpose: Defines and expands the bounding box for the map and converts it into a GeoDataFrame for plotting while bounding the shapefiles.

### 4. Create Main Plot and Customize Axis Appearance

```python
# Create the plot
fig, ax = plt.subplots(figsize=(10, 10))
bounded_shapefile1.plot(ax=ax, edgecolor='red', facecolor='none', alpha=0.5, hatch='|||||', legend=True)
bounded_shapefile2.plot(ax=ax, edgecolor='black', facecolor='white', markersize=50, alpha=1, marker='o', legend=True)
shapefile3.plot(ax=ax, edgecolor='yellow', facecolor='none', alpha=0.5, hatch='/////', legend=True)

# Annotate the names of the areas
for idx, row in bounded_shapefile2.iterrows():
    plt.annotate(text=row['name'], xy=(row.geometry.centroid.x, row.geometry.centroid.y), xytext=(3, 3), textcoords='offset points', fontsize=8, color='white') # change name according to column name of the settlements

# Add the satellite basemap using contextily
ctx.add_basemap(ax, crs=shapefile3.crs.to_string(), source=ctx.providers.Esri.WorldImagery)
plt.tight_layout()

# Set the coordinates to be displayed vertically
ax.tick_params(axis='x', rotation=0)
ax.tick_params(axis='y', rotation=90)

# Set the format for the coordinates
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.3f}'))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.3f}'))
```

Purpose: Initializes the plot, styles the shapefiles, adds a basemap, adjusts the layout and rotates axis ticks and formats their labels for readability.

### 5. Calculate Scale

```python
# Calculate latitude and longitude ranges
lat_mid = (y_max + y_min) / 2  # Use the midpoint latitude for accuracy
cos_lat = np.cos(np.radians(lat_mid))  # Cosine of the latitude for longitude adjustment

# Improved horizontal and vertical scales in meters
scale_x = (x_max - x_min) * 111000 * cos_lat  # Horizontal scale adjusted for latitude
scale_y = (y_max - y_min) * 111000  # Vertical scale remains the same

# Determine the maximum scale for consistency
scale = max(scale_x, scale_y)

# Calculate the scale ratio for the map (e.g., 1:100000)
# Assuming your map is being displayed at a specific width in pixels, you can use that to get the scale ratio
real_world_width_meters = scale_x  # The real-world width represented by the map

scale_ratio = real_world_width_meters / width  # Meters per pixel

# Determine the appropriate scale text
scale_text = f"Scale: 1:{int(scale_ratio)}"
```

Purpose: Computes the scale for the map based on its extent and prepares the scale text.

### 6. Create Inset Map

```python
# Create the inset map showing the area of interest (AOI)
expansion_factor = config['map']['expansion_factor2']
x_min_ = x_min + (width * expansion_factor)
x_max_ = x_max - (width * config['map']['ysize'] * expansion_factor)
y_min_ = y_min + (height * expansion_factor)
y_max_ = y_max - (height * expansion_factor)

aoi_polygon = Polygon([(x_min-0.1, y_min-0.1), (x_max+0.1, y_min-0.1), (x_max+0.1, y_max+0.1), (x_min-0.1, y_max+0.1)]) #adjust size of red square
aoi_polygon_ = Polygon([(x_min_, y_min_), (x_max_, y_min_), (x_max_, y_max_), (x_min_, y_max_)])
aoi_gdf = gpd.GeoDataFrame(geometry=[aoi_polygon], crs=shapefile1.crs)
aoi_gdf_ = gpd.GeoDataFrame(geometry=[aoi_polygon_], crs=shapefile1.crs)

# Adjust the coordinates for the inset to be placed under the title
inset_ax = fig.add_axes([config['map']['x'], config['map']['y'], config['map']['width'], config['map']['height']])
aoi_gdf_.plot(ax=inset_ax, edgecolor='red', facecolor='none', alpha=0, legend=True)
aoi_gdf.plot(ax=inset_ax, edgecolor='red', facecolor='none', alpha=1, linewidth=3, legend=True)
ctx.add_basemap(inset_ax, crs=shapefile1.crs.to_string(), source=ctx.providers.Esri.WorldImagery)
inset_ax.set_xticks([])
inset_ax.set_yticks([])
inset_ax.set_xlabel('')
inset_ax.set_ylabel('')
```

Purpose: Defines the extent and appearance of an inset map to show the area of interest and adds it to the main figure.

### 7. Add Title, Legend, and Annotations

```python
# Add title
plt.text(config['firehub']['x'], config['firehub']['y'], config['firehub']['name'], transform=ax.transAxes, rotation=0, va='top', fontweight='bold', fontsize=20, color='red')

xtext = config['text_position']['x']
ytext = config['text_position']['y']

# Add legend
plt.text(xtext, ytext + config['ypomnima']['y'], config['ypomnima']['name'], transform=ax.transAxes, rotation=0, ha='left', va='baseline', fontweight='bold', fontsize=10)
bbox_gdf.plot(ax=ax, edgecolor='red', facecolor='red', alpha=0, legend=True) 
plt.plot(bounded_shapefile1[config['ypomnima']['id_name1']], label=config['ypomnima']['label1'])
plt.plot(bounded_shapefile2[config['ypomnima']['id_name2']], label=config['ypomnima']['label2'])
plt.plot(shapefile3[config['ypomnima']['id_name3']], label=config['ypomnima']['label3'])
fire = mpatches.Patch(edgecolor='red', facecolor='none', alpha=0.5, hatch='/////', label=config['ypomnima']['label1'])
settlement = Line2D([0], [0], marker='o', color='w', label=config['ypomnima']['label2'], markerfacecolor='white', markeredgecolor='black', markersize=10, alpha=0.5)
previous_fire = mpatches.Patch(edgecolor='yellow', facecolor='none', alpha=0.5, hatch='|||||', label=config['ypomnima']['label3'])
plt.legend(loc='right', title_fontproperties=fm.FontProperties(weight='bold'), bbox_to_anchor=(config['ypomnima']['xlabel'], config['ypomnima']['ylabel']), borderaxespad=0, frameon=False, handles=[settlement, fire, previous_fire])

```

Purpose: Adds title, legend, and a text annotations to the main plot.

### 8. Get Current Date, Add Standardized Text with Map Information

```python
# Get the current date
today = datetime.today().date()
today = today.strftime("%d/%m/%Y")

# Add standardised text on the side of the map
plt.text(xtext, config['place']['y'], config['place']['name'], transform=ax.transAxes, rotation=0, ha='left', va='baseline', fontweight='bold', fontsize=16)
plt.text(xtext, config['subtitle']['y'], config['subtitle']['name'], transform=ax.transAxes, fontsize=11, va='top', fontweight='bold')
plt.text(config['production_date']['x'], config['production_date']['y'], config['production_date']['name'] + today, transform=ax.transAxes, fontsize=10, va='top')
plt.text(xtext, ytext + 0.335, scale_text, transform=ax.transAxes, fontsize=8, va='center', fontweight='bold')
plt.text(xtext, ytext + config['map_information']['y_name'], config['map_information']['name'], transform=ax.transAxes, fontsize=10, va='center', fontweight='bold')
plt.text(xtext, ytext + config['map_information']['y_text'], config['map_information']['text'].replace('{place}', config['place']['name']), transform=ax.transAxes, fontsize=8, va='center')
plt.text(xtext, ytext + config['sources']['y_name'], config['sources']['name'], transform=ax.transAxes, fontsize=10, va='center', fontweight='bold')
plt.text(xtext, ytext + config['sources']['y_text'], config['sources']['text'], transform=ax.transAxes, fontsize=8, va='center')
plt.text(xtext, ytext + config['publication']['y_name'], config['publication']['name'], transform=ax.transAxes, fontsize=10, va='center', fontweight='bold')
plt.text(xtext, ytext + config['publication']['y_text'], config['publication']['text'], transform=ax.transAxes, fontsize=8, va='center')
plt.text(xtext, ytext + config['team']['y_name'], config['team']['name'], transform=ax.transAxes, fontsize=10, va='center', fontweight='bold')
plt.text(xtext, ytext + config['team']['y_text'], config['team']['text'], transform=ax.transAxes, fontsize=8, va='center')
plt.text(xtext, ytext + config['contact_details']['y_name'], config['contact_details']['name'], transform=ax.transAxes, fontsize=10, va='center', fontweight='bold')
plt.text(xtext, ytext + config['contact_details']['y_text'], config['contact_details']['text'], transform=ax.transAxes, fontsize=8, va='center')
```

Purpose: Gets current date and adds standardized text

### 9. Add Logos

```python
# Add north
logo_image = plt.imread(config['logos']['north'])
logo_plot = OffsetImage(logo_image, zoom=0.7)  #adjust zoom to control logo size
ab = AnnotationBbox(logo_plot, (config['logos']['x_north'], ytext + config['logos']['y_north']), xycoords='axes fraction', frameon=False)
ax.add_artist(ab)

# Add logos to the plot
logo_paths = [
    (config['logos']['first'], 0.185),
    (config['logos']['second'], 0.08),
    (config['logos']['third'], 0.123),
    (config['logos']['fourth'], 0.5)
]

# Adjusted coordinates for logos placed side by side
for i, (logo_path, zoom) in enumerate(logo_paths):
    logo_image = plt.imread(logo_path)
    logo_plot = OffsetImage(logo_image, zoom=zoom)
    ab = AnnotationBbox(logo_plot, (config['logos']['x'] + i*0.25, config['logos']['y']), xycoords='axes fraction', frameon=False) 
    ax.add_artist(ab)
```

Purpose: Adds logos and a north arrow to the map.

### 10. Save and Crop Image

```python
# Save the figure
burned_map = config['images']['burned_map']
cropped_burned_map = config['images']['cropped_burned_map']
plt.savefig(burned_map, dpi=config['images']['dpi'], bbox_inches='tight')

# # Show the plot
# plt.show()

# Close the figure to release memory
plt.close(fig)

# Load the image
image = Image.open(burned_map)

# Get the dimensions of the original image
width, height = image.size

# Define the crop area
left = 0       # Keep the left side as is
upper = 0      # Keep the top side as is
right = width - config['images']['crop_factor']  # Crop x pixels from the right
lower = height  # Keep the bottom side as is

# Crop the image
cropped_image = image.crop((left, upper, right, lower))

# Save the cropped image
cropped_image.save(cropped_burned_map)

# Delete the original image
os.remove(burned_map)

# Optionally, show the cropped image
cropped_image.show()
```
Purpose: Saves the final map image, crops the right side, and optionally displays the cropped image.

## Dependencies

To run this script, you will need the following Python libraries:

- **geopandas**: For working with geospatial data, reading shapefiles, and performing spatial operations.
- **matplotlib**: For creating plots, customizing map visualizations, and adding text, legends, and annotations.
    
    Specific submodules used:
  1. **matplotlib.pyplot**: For general plotting.
  2. **matplotlib.patches**: For adding custom patches like polygons or rectangles.
  3. **matplotlib.lines.Line2D**: For creating custom lines and markers.
  4. **matplotlib.offsetbox.OffsetImage and AnnotationBbox**: For placing images (e.g., logos) on the plot.
  5. **matplotlib.font_manager**: For managing fonts and font properties.
- **mpl_toolkits.axes_grid1**: For creating inset axes, which are smaller axes placed inside the main axes.

    Specific submodules used:
  1. **inset_locator**: To add inset axes to the main plot.
  2. **make_axes_locatable**: To create a divider for easily placing colorbars or other elements.
- **shapely.geometry.Polygon**: For creating and manipulating geometric shapes, particularly polygons representing bounding boxes.
- **contextily**: For adding basemaps (such as satellite imagery) to the plots.
- **Pillow**: For image processing, including loading, cropping, and saving images.
- **numpy**:For numerical operations, particularly for handling coordinate transformations and scaling.
- **yaml**:For loading and parsing configuration files written in YAML format.
- **json**:Although not currently active in the script (commented out), it's used for loading configuration from a JSON file (if needed).
- **os**:For interacting with the file system, such as removing files.
- **datetime**:For working with dates and times, particularly for adding the current date to the map.

### Installation

You can install the required libraries using Conda. Run the following commands:

```bash
conda create -n my_environment python=your_python_version
conda activate my_environment
conda install -c conda-forge geopandas matplotlib shapely contextily pillow numpy pyyaml
```

## Files

config.yaml: Configuration file with everything that needs to be adjusted.\
Shapefiles containing the geospatial data.\
Logos and images used in the script.