import geopandas as gp
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import os
# shapefile --> allagi CRS se Greek Grid --> fix geometry --> clip sto Burned Area --> dissolve gia kapoio column --> fix overlaps --> ypologismos posostou

class BAStats:
    def __init__(self, Shapefile_GeoDataFrame, BurnedArea_GeoDataFrame):
        # creating geodataframe from shapefile
        # geo_df is Shapefile to get stats from
        # AOI is burned area polygon
        self.geo_df = Shapefile_GeoDataFrame
        self.AOI    = BurnedArea_GeoDataFrame
        self.areaOfCatagorys = gp.GeoDataFrame() # final results, just initiate the Series

    
    def check_crs(self):
        if self.geo_df.crs != self.AOI.crs:
            print('CRS of Shapefile:  ', self.geo_df.crs)
            print('CRS of Burned Area:', self.AOI.crs)
            print('CRS will be changed to', self.AOI.crs, '\n')
            # change CRS of shapefile to much 
            self.geo_df = self.geo_df.to_crs(self.AOI.crs)
        else:
            print('CRS of Shapefile and Burned Area:', self.geo_df.crs, '\n')


    def fix_geometry(self, geometry):
        if geometry.is_valid:
            return geometry
        else:
            fixed_geometry = geometry.buffer(0)
            if fixed_geometry.is_valid:
                return fixed_geometry
            else:
                return unary_union([geometry])

    def fix_geometry2(self, geometry):
        from shapely.geometry import shape
        from shapely.ops import unary_union
        from shapely.validation import make_valid

        if geometry.is_valid:
            return geometry
            # Attempt to fix the geometry by buffering by 0
        fixed_geometry = make_valid(geometry)
        if fixed_geometry.is_valid:
            return fixed_geometry
        # Use make_valid if buffering doesn't work
        return make_valid(fixed_geometry)

    def remove_overlap(self):

        num_polygons = len(self.geo_df)
        # Initialize result_geometries and contributions with the correct number of elements
        result_geometries = [None] * num_polygons
        contributions = [Polygon() for _ in range(num_polygons)]

        # Convert GeoDataFrame to a list of geometries for easier manipulation
        geometries = self.geo_df.geometry.tolist()

        # Iterate over each polygon
        for i, polygon_i in enumerate(geometries):
            # pernoume ola ta alla polygona ektos apo to i
            other_polygons = [geom for idx, geom in enumerate(geometries) if idx != i]

            # enonoume ola ta poylgona pou pirame prin
            union_other_polygons = unary_union(other_polygons)
            #from shapely.ops import snap
            #polygon_i = snap(polygon_i, union_other_polygons, tolerance=0.01)
            # ypologismos overlap meta3i tou polygonou i kai twn union (olwn twn allwn)
            overlap = polygon_i.intersection(union_other_polygons)

            if not overlap.is_empty:
                # Calculate non-overlapping part of the current polygon
                non_overlap = polygon_i.difference(overlap)
                contributions[i] = non_overlap

                # Distribute the overlap among other polygons
                for j, polygon_j in enumerate(geometries):
                    if j != i:
                        intersection = overlap.intersection(polygon_j)
                        if not intersection.is_empty:
                            contributions[j] = contributions[j].union(intersection)
            else:
                # If no overlap, just keep the original polygon
                contributions[i] = polygon_i

        # Assign contributions to result_geometries
        for i in range(num_polygons):
            result_geometries[i] = contributions[i]

        # Create a new GeoDataFrame with the updated geometries
        result_gdf = self.geo_df.copy()
        result_gdf['geometry'] = result_geometries
        return result_gdf

    def clip_area_to_AOI(self):

        # check CRS compatability and fix it if needed
        self.check_crs()

        # fix geometrys
        self.geo_df['geometry'] = self.geo_df['geometry'].apply(self.fix_geometry)
        self.AOI['geometry'] = self.AOI['geometry'].apply(self.fix_geometry)

        # clip shapefile to Area of Interest
        self.geo_df = self.geo_df.clip(self.AOI)
        return self.geo_df

    def dissolve_AOI(self): # column = 'DN'
        self.AOI = self.AOI.dissolve()

    def dissolve_shapefile(self, column): # code_18 gia Corine Land Cover 2018
        if column == None:
            self.geo_df = self.geo_df.dissolve()
        else:
            self.geo_df = self.geo_df.dissolve(by=column)

    def get_data_BurnedArea(self):
        return self.AOI

    def get_data_Shapefile(self):
        return self.geo_df

    def save_csv(self, filepath, filename):
        # do no sav if there is nothing to save in the .csv
        if len(self.areaOfCatagorys) == 0:
            return 0
        else:
            self.areaOfCatagorys.to_csv(filepath +
                                        filename +
                                        '.csv',
                                       header=False,
                                       index=True,
                                       sep=',',
                                       encoding='utf-8-sig')

    def save_polygon(self, output_path, filename):
        # do not save if there is nothing to save in the geodataframe
        if len(self.geo_df) == 0:
            return 0
        else:
            path_to_polygon = output_path + filename + '_POLYGON_CLIPPED/'
            if os.path.exists(path_to_polygon):
                    self.geo_df.to_file(path_to_polygon + filename + '.shp')
            else:
                os.makedirs(path_to_polygon)
                self.geo_df.to_file(path_to_polygon + filename + '.shp')

    def calc_stats(self, column):

        # clip shapefile to AOI
        self.clip_area_to_AOI()

        # dissolves burned area (AOI) if needed
        self.dissolve_AOI()

        # check if shapefile is poylgon or point
        # shape file contains points
        if (self.geo_df.geom_type.unique() == 'Point').all():
            categorys = self.geo_df[column].value_counts()
            for i in range(0, len(categorys)):
                print(f'Categoty: {categorys.index[i]} \n Points {categorys[i]} \n')

            if len(categorys) == 0:
                print('None!\n')
                print('--------------------')
            return categorys
        
        # shapefile contains polygon
        else:
            # dissolve shapefile for the column that stats will be calculated
            self.dissolve_shapefile(column)

            # fix overlaps if any
            #self.geo_df = self.remove_overlap()

            totalArea_AOI = self.AOI['geometry'].area.sum() / 10000 # total area of AOI, burned area shapefile in ha
            totalArea_Shapefile = self.geo_df['geometry'].area.sum() / 10000
            print('Toral Burned Area(ha)', round(totalArea_AOI, 1))
            print('Total Shapefile Area(ha) inside Burned Area', round(totalArea_Shapefile, 1), '\n')


            self.areaOfCatagorys = self.geo_df['geometry'].area / 10000 # in ha from m2


            # check if some categorys overlap 100% and fix it
            #for i in range(len(self.areaOfCatagorys)):
            #    if self.areaOfCatagorys.iloc[i] == 0.:
            #        self.areaOfCatagorys.iloc[i] = self.areaOfCatagorys.iloc[i-1]
            #        print('WARNING overlap 100%')


            for i in range(0, len(self.areaOfCatagorys)):
                percentage = round(( self.areaOfCatagorys.iloc[i] / totalArea_AOI ) * 100, 1)
                print(f'Category: {self.areaOfCatagorys.index[i]} \nArea in % {percentage}\n')
                self.areaOfCatagorys.iat[i] = percentage

            if len(self.areaOfCatagorys) == 0:
                print('None!')
            print('--------------------')
            return self.areaOfCatagorys

