
import sqlite3
import pandas as pd

# Define the path to your .db file
db_file = "Deltia_Database.db"

# Establish a connection to the database
conn = sqlite3.connect(db_file)

# Get a list of all tables in the database
query = "SELECT name FROM sqlite_master WHERE type='table';"
tables = pd.read_sql(query, conn)

# Create a Pandas Excel writer using openpyxl engine
excel_file = "Deltia_Databse.xlsx"
writer = pd.ExcelWriter(excel_file, engine='openpyxl')

# Loop through all the tables and write each one to a separate Excel sheet
for table_name in tables['name']:
    # Read the table into a DataFrame
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    # Write the DataFrame to an Excel sheet
    df.to_excel(writer, sheet_name=table_name, index=False)

# Save the Excel file
writer._save()

# Close the database connection
conn.close()
