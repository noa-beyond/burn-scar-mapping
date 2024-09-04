import sqlite3
import geopandas as gpd
import pandas as pd
from unidecode import unidecode

# Step 1: Load the .db file
db_path = "C:/burned-scar-mapping/Deltia_Database.db"
conn = sqlite3.connect(db_path)

# Query to extract the required column from the Deltia_Pyrovestikis table
query = "SELECT [ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ] FROM Deltia_Pyrosvestikis"
df_db = pd.read_sql_query(query, conn)

# Remove the 'Δ.' prefix from the ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ column
df_db['ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'] = df_db['ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'].str.replace('Δ.', '', regex=False)

# Convert the ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ column to Latin characters and lowercase
df_db['ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'] = df_db['ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'].apply(lambda x: unidecode(x).lower())

# Step 2: Load the shapefile
shapefile_path = "C:/Users/nikos/Desktop/greece_dimoi/dimoi.shp"
gdf = gpd.read_file(shapefile_path)

# Convert the NAME column to Latin characters and lowercase
gdf['NAME'] = gdf['NAME'].apply(lambda x: unidecode(x).lower())

# Step 3: Perform the match and count occurrences
# Group by NAME from the shapefile and count occurrences in the .db file
counts = df_db['ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'].value_counts().reset_index()
counts.columns = ['NAME', 'count']

# Convert NAME in counts to lowercase and Latin characters to ensure matching
counts['NAME'] = counts['NAME'].apply(lambda x: unidecode(x).lower())

# Merge the counts with the original GeoDataFrame
gdf = gdf.merge(counts, on='NAME', how='left')

# Fill NaN values in the 'count' column with 0
gdf['count'] = gdf['count'].fillna(0)

# Step 4: Save the result as a new shapefile
output_shapefile_path = "C:/Users/nikos/Desktop/greece_dimoi/dimoi_with_counts.shp"
gdf.to_file(output_shapefile_path)

print(f"Shapefile saved to {output_shapefile_path}")
