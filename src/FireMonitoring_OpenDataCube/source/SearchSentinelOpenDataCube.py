import pystac_client
import odc.stac
from odc.geo.geobox import GeoBox
import shapely.geometry as geom

class SearchSentinel:
    def __init__(self, STAC_URL, STAC_COLLECTION, BurnedAreaBox, start_DATE, end_DATE, cloudCover):
        self.STAC_URL        = STAC_URL
        self.STAC_COLLECTION = STAC_COLLECTION
        self.BurnedAreaBox   = BurnedAreaBox
        self.start_DATE      = start_DATE
        self.end_DATE        = end_DATE
        self.cloudCover      = cloudCover
        
        

    def get_data(self):
        # define catalog and add conforms
        catalog = pystac_client.Client.open(self.STAC_URL)
        catalog.add_conforms_to('ITEM_SEARCH')
        catalog.add_conforms_to('QUERY')

        # get stac items from catalog based on collection (here Earth Search)
        stac_items = catalog.search(
            collections=[self.STAC_COLLECTION],
            bbox=self.BurnedAreaBox,
            datetime=[self.start_DATE, self.end_DATE],
            query={'eo:cloud_cover': {'lt': self.cloudCover}}
        )

        # remoce images that are not fully in the bbox
        filtered_items = []
        for item in stac_items.items():
            item_geom = geom.shape(item.geometry)
            if self.is_fully_within(item_geom, self.BurnedAreaBox) == True:
                filtered_items.append(item)
        stac_items = filtered_items


        resolution = 10 / 111320 # 111111 1 degree is 111km
        epsg = 4326
   
        # reolution must match the crs, if projected use meteres, if (f,l) use degrees
        geobox = GeoBox.from_bbox(self.BurnedAreaBox, crs=f"epsg:{epsg}", resolution=resolution)

        data = odc.stac.load(
            stac_items,
            chunks={},
            geobox=geobox, 
                # band 2,  band 3,  band 4, band 5,     band 6,     band 7,  band 8, band 8A,  band 9,  band 11, band 12, missing cirrus
            bands=['blue', 'green', 'red', 'rededge1', 'rededge2', 'rededge3', 'nir', 'nir08', 'nir09', 'swir16', 'swir22', 'scl'],
            groupby='solar_day'
        )
        
        return data        
    

    def is_fully_within(self, geometry, bbox):
        import shapely.geometry as geom
        bbox_geom = geom.box(*bbox)  # Create a Shapely box from the bbox
        return bbox_geom.within(geometry)