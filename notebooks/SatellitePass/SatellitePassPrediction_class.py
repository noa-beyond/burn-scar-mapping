from pykml import parser
from lxml import etree
import geopandas as gpd
from shapely.geometry import Point, Polygon


class SatellitePassPrediction:
    def __init__(self, kml_file, latitude, longitude):
        self.kml_file = kml_file
        self.latitude = latitude
        self.longitude = longitude
        self.gdf = None

    # Function to load the KML file
    def load_kml(self):
        with open(self.kml_file) as f:
            self.root = parser.parse(f).getroot()
        return self.root

    # Function to convert coordinates to a Polygon object
    def coordinates_to_polygon(self, coordinates):
        # Coordinates are typically in the form "lon,lat,alt lon,lat,alt ..."
        points = []
        for coord in coordinates.split():
            lon, lat, _ = map(float, coord.split(","))
            points.append((lon, lat))
        return Polygon(points)

    # Function to recursively extract placemarks and save to GDB
    def extract_placemarks(self, folder, gdf_data=[]):
        if hasattr(folder, 'Placemark'):
            for placemark in folder.Placemark:
                data = {
                    'name': placemark.name.text if hasattr(placemark, 'name') else "No Name",
                    'geometry': self.coordinates_to_polygon(
                        placemark.Polygon.outerBoundaryIs.LinearRing.coordinates.text
                    ) if hasattr(placemark, 'Polygon') else None,
                    'styleUrl': placemark.styleUrl.text if hasattr(placemark, 'styleUrl') else None,
                    'visibility': int(placemark.visibility.text) if hasattr(placemark, 'visibility') else None,
                    'begin': placemark.TimeSpan.begin.text if hasattr(placemark, 'TimeSpan') else None,
                    'end': placemark.TimeSpan.end.text if hasattr(placemark, 'TimeSpan') else None,
                }
                # Extract ExtendedData fields
                if hasattr(placemark, 'ExtendedData'):
                    for data_field in placemark.ExtendedData.Data:
                        data_name = data_field.get('name')
                        data_value = data_field.value.text
                        data[data_name] = data_value

                gdf_data.append(data)

        if hasattr(folder, 'Folder'):
            for subfolder in folder.Folder:
                self.extract_placemarks(subfolder, gdf_data)
                
        return gdf_data
    
    # Function to extract placemarks and save to GeoDataFrame
    # Also removes duplicate entries and sets the CRS to EPSG:4326
    def extract_placemarks_to_gdf(self):
        # Load KML data
        root = self.load_kml()
        
        # Extract placemarks data
        gdf_data = self.extract_placemarks(root.Document)
        
        # Convert extracted data to GeoDataFrame
        columns = ['name', 'geometry', 'styleUrl', 'visibility', 'begin', 'end'] + \
                  list({key for row in gdf_data for key in row.keys() if key not in ['name', 'geometry', 'styleUrl', 'visibility', 'begin', 'end']})
        
        # Create the GeoDataFrame
        self.gdf = gpd.GeoDataFrame(gdf_data, columns=columns)
        
        # Remove duplicates
        self.gdf = self.gdf.drop_duplicates(subset=self.gdf.columns)
        
        # Set CRS
        self.gdf.set_crs('EPSG:4326', inplace=True)
        
        return self.gdf
    
    # Function to get observation info for a given point
    def get_observation_info(self):
        if self.gdf is None:
            raise ValueError("GeoDataFrame is not initialized. Run extract_placemarks_to_gdf() first.")
                
        # Create a Point object for the given latitude and longitude
        point = Point(self.longitude, self.latitude)

        # List to hold observation info for all matching polygons
        observation_info = []

        # Ensure the point is in the correct CRS
        if self.gdf.crs.to_string() != 'EPSG:4326':
            point = gpd.GeoSeries([point], crs='EPSG:4326').to_crs(self.gdf.crs).iloc[0]

        # Search for all polygons that contain the point
        for i, row in self.gdf.iterrows():
            if row['geometry'] and row['geometry'].contains(point):
                # Append the ID, the ObservationTimeStart and ObservationTimeStop to the list
                observation_info.append({
                    'Id': row.get('ID'),
                    'ObservationTimeStart': row.get('ObservationTimeStart'),
                    'ObservationTimeStop': row.get('ObservationTimeStop')
                })

        return observation_info
    

    
