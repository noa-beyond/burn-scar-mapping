import pandas as pd
import os
import tabula
import numpy as np
import sqlite3
from PyPDF2 import PdfReader, PdfWriter
import shutil
import datetime
from unidecode import unidecode
import unicodedata

class DeltiaFire:

    # orizontai to onoma twn dataframes
    def __init__(self, pdf_path_folder):
        self.dfs = self.get_tables_from_pdf(pdf_path_folder)
        self.pdf_path = pdf_path_folder
        
        self.tables = self.fix_tables(self.dfs)

        # Database Stuff
        self.table_name_database = "Deltia_Pyrosvestikis"
        self.current_year = datetime.datetime.now().year



    def get_tables_from_pdf(self, pdf_path):
        #tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, java_options="-Xmx1024m")
        #tables[0].to_excel('test.xlsx')
        return tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)




    def sum_numbers(self, cell):
        if isinstance(cell, float) or isinstance(cell, int):  # If the cell is already a number, return it
            return cell
        numbers = cell.split()
        total = 0
        for number in numbers:
            try:
                total += float(number)
            except ValueError:
                continue
        return total




    def fix_tables(self, tables):
        
        columns_to_drop = ["ΧΡΟΝΟΛΟΓΙΑ",
                           "Unnamed: 2",
                           "Unnamed: 3",
                           "Unnamed: 4",
                           "Unnamed: 5",
                           "ΠΡΟΣΩΠΙΚΟ",
                           "Unnamed: 6",
                           "Unnamed: 7",
                           "ΜΕΣΑ",
                           "Unnamed: 8",
                           "Unnamed: 9"]

        filtered_tables = []
        i = 0
        for table in tables:
            if all(column in table.columns for column in columns_to_drop):
                #table.to_excel(f't{i}.xlsx', header=True, index=False)
                table.drop(columns_to_drop, axis=1, inplace=True)
                filtered_tables.append(table)
                i += 1
            else:
                #table.to_excel(f'testtttttttt{i}.xlsx', header=True, index=False)
                print('Problem with PDF file :', self.pdf_path)
                i += 1    
        tables = filtered_tables 

        for i in range(0, len(tables)):
            tables[i].rename(columns={'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ': 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ',
                                    'ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ': 'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ',
                                    'Unnamed: 0': 'ΩΡΑ ΕΝΑΡΞΗΣ',
                                    'Unnamed: 1': 'ΠΛΗΡΗΣ ΚΑΤΑΣΒΕΣΗ'},
                            inplace=True)

            tables[i]['ΚΑΜΕΝΗ ΕΚΤΑΣΗ (Στρέμματα)'] = tables[i]['ΚΑΜΕΝΗ ΕΚΤΑΣΗ (Στρέμματα)'].apply(self.sum_numbers)

            tables[i] = tables[i].drop(tables[i][tables[i]['Α/Α'] == 'Α/Α ΠΥΡΚ'].index)
            tables[i] = tables[i].drop(tables[i][tables[i]['ΩΡΑ ΕΝΑΡΞΗΣ'] == 'ΕΝΑΡ.'].index)
            #print(tables[0].columns, tables[1].columns)

                
        return tables

    def fix_names(self, table):
        for i in range(table.shape[0]):
            if pd.isna(table.at[i, 'Α/Α']) and pd.notna(table.at[i, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ']):
                table.at[i - 1, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'] = f"{table.at[i - 1, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ']} {table.at[i, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ']}"

            elif pd.isna(table.at[i, 'Α/Α']) and pd.isna(table.at[i, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ']):
                table.at[i - 1, 'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'] = f"{table.at[i - 1, 'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ']} {table.at[i, 'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ']}"
                if pd.isna(table.at[i, 'ΩΡΑ ΕΝΑΡΞΗΣ']):
                    table.at[i + 2, 'ΩΡΑ ΕΝΑΡΞΗΣ'] = table.at[i + 1, 'ΩΡΑ ΕΝΑΡΞΗΣ']
                    table.at[i + 2, 'ΠΛΗΡΗΣ ΚΑΤΑΣΒΕΣΗ'] = table.at[i + 1, 'ΠΛΗΡΗΣ ΚΑΤΑΣΒΕΣΗ']

            elif pd.isna(table.at[i, 'Α/Α']) and pd.isna(table.at[i, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ']) or pd.isna(table.at[i, 'ΩΡΑ ΕΝΑΡΞΗΣ']):
                table.at[i - 1, 'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'] = f"{table.at[i - 1, 'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ']} {table.at[i, 'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ']}"
                if pd.isna(table.at[i, 'ΩΡΑ ΕΝΑΡΞΗΣ']):
                    table.at[i + 0, 'ΩΡΑ ΕΝΑΡΞΗΣ'] = table.at[i - 1, 'ΩΡΑ ΕΝΑΡΞΗΣ']
                    table.at[i + 0, 'ΠΛΗΡΗΣ ΚΑΤΑΣΒΕΣΗ'] = table.at[i - 1, 'ΠΛΗΡΗΣ ΚΑΤΑΣΒΕΣΗ'] 
                    
        return table

    def check_for_nans(self, table):
        rowsToDelete = set()
        for i in range(table.shape[0]):
            if pd.isna(table.at[i, 'Α/Α']):
                rowsToDelete.add(i)
        table = table.drop(index=rowsToDelete).reset_index(drop=True)
        return table

    def shift_up(self, column):
        # Drop NaNs and reset the index
        non_nan_values = column.dropna().reset_index(drop=True)
        # Calculate the number of NaNs
        num_nans = column.isna().sum()
        # Create a new series with NaNs at the end
        filled_column = pd.concat([non_nan_values, pd.Series([np.nan] * num_nans)], ignore_index=True)
        return filled_column

    def save_to_database(self, database_path):

        # pernoume ta tables kai ta ftiaxnoume
        tables = self.tables

        merged_tables = pd.concat(tables, ignore_index=True)
        merged_tables = self.fix_names(merged_tables)
        merged_tables = self.check_for_nans(merged_tables)

        # prepei na diagra3oume ta nan kai na feroume mia thesi panw oti exei apo katw tous
        # merged_tables['Α/Α'] = shift_up(merged_tables['Α/Α'])
        # merged_tables['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'] = shift_up(merged_tables['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'])
        # merged_tables['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'] = shift_up(merged_tables['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'])
        # merged_tables['ΩΡΑ ΕΝΑΡΞΗΣ'] = shift_up(merged_tables['ΩΡΑ ΕΝΑΡΞΗΣ'])
        # merged_tables = merged_tables.dropna(subset=['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'])
        # merged_tables = merged_tables.dropna(subset=['ΩΡΑ ΕΝΑΡΞΗΣ'])
        # merged_tables = merged_tables.fillna(-1)

        # stiles pou tha exei to teliko dataframe
        df = pd.DataFrame(columns=['Α/Α',
                                   'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ',
                                   'ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ',
                                   'DHMOS-KOINOTITA Latin',
                                   'ΗΜΕΡΟΜΗΝΙΑ ΕΝΑΡΞΗΣ',
                                   'ΩΡΑ ΕΝΑΡΞΗΣ',
                                   'ΗΜΕΡΟΜΗΝΙΑ ΛΗΞΗΣ',
                                   'ΩΡΑ ΛΗΞΗΣ',
                                   'ΚΑΜΕΝΗ ΕΚΤΑΣΗ',
                                   'ΕΝΤΟΠΙΣΜΟΣ FireHUB',
                                   'ΗΜΕΡΟΜΗΝΙΑ ΚΑΙ ΩΡΑ ΕΝΤΟΠΙΣΜΟΥ Firehub',
                                   'ΑΙΤΙΟΛΟΓΙΑ ΜΗ ΕΝΤΟΠΙΣΜΟΥ',
                                   'ΕΙΚΟΝΕΣ Seviri ΓΙΑ ΕΛΕΓΧΟ',
                                   'ΨΗΦΙΟΠΟΙΗΣΗ',
                                   'PDF File Name'
                                   ])


        merged_tables['DHMOS-KOINOTITA Latin'] = merged_tables['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'].str.replace('Δ.', '', regex=False)
        merged_tables['DHMOS-KOINOTITA Latin'] = merged_tables['DHMOS-KOINOTITA Latin'].apply(self.normalize_and_transliterate)

        rows = []
        for i in range(0, len(merged_tables), 2):
            # pernoume dedomena ana 2 grammes
            chunk = merged_tables.iloc[i:i + 2]['Α/Α'].values
            if len(chunk) == 2:
                first_value, second_value = chunk
                df.at[i, 'Α/Α'] = second_value

        rows = []
        for i in range(0, len(merged_tables), 2):
            # pernoume dedomena ana 2 grammes
            chunk1 = merged_tables.iloc[i:i + 2]['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'].values
            # print(chunk1)
            chunk2 = merged_tables.iloc[i:i + 2]['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'].values
            # print(chunk2)
            chunk3 = merged_tables.iloc[i:i + 2]['ΩΡΑ ΕΝΑΡΞΗΣ'].values
            # print(chunk3)
            chunk4 = merged_tables.iloc[i:i + 2]['ΚΑΜΕΝΗ ΕΚΤΑΣΗ (Στρέμματα)'].values
            # print(chunk4)
            chuck5 = merged_tables.iloc[i:i + 2]['ΠΛΗΡΗΣ ΚΑΤΑΣΒΕΣΗ'].values
            #print(chuck5)
            chunk6 = merged_tables.iloc[i:i + 2]['DHMOS-KOINOTITA Latin'].values
            #print(chunk6)

            if len(chunk1) == 2:
                first_value1, second_value1 = chunk1
                if first_value1 == '-':
                    df.at[i, 'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ'] = second_value1
                elif second_value1 == '-':
                    df.at[i, 'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ'] = first_value1
                else:
                    df.at[i, 'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ'] = f"{first_value1}, {second_value1}"
            else:
                df.at[i, 'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ'] = chunk1

            if len(chunk2) == 2:
                first_value2, second_value2 = chunk2
                df.at[i, 'ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'] = first_value2
            else:
                df.at[i, 'ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'] = chunk2

            if len(chunk3) == 2:
                first_value3, second_value3 = chunk3
                day3, month3 = first_value3.split('/')
                df.at[i, 'ΗΜΕΡΟΜΗΝΙΑ ΕΝΑΡΞΗΣ'] = str(self.current_year) + '-' + month3 + '-' + day3
                df.at[i, 'ΩΡΑ ΕΝΑΡΞΗΣ'] = second_value3
            else:
                df.at[i, 'ΩΡΑ ΕΝΑΡΞΗΣ'] = chunk3

            if len(chunk4) == 2:
                first_value4, second_value4 = chunk4
                df.at[i, 'ΚΑΜΕΝΗ ΕΚΤΑΣΗ'] = first_value4
            else:
                df.at[i, 'ΚΑΜΕΝΗ ΕΚΤΑΣΗ'] = chunk4

            if len(chuck5) == 2:
                if isinstance(chuck5[0], str) or isinstance(chuck5[1], str):
                    first_value5, second_value5 = chuck5
                    day5, month5 = first_value5.split('/')
                    df.at[i, 'ΗΜΕΡΟΜΗΝΙΑ ΛΗΞΗΣ'] = str(self.current_year) + '-' + month5 + '-' + day5
                    df.at[i, 'ΩΡΑ ΛΗΞΗΣ'] = second_value5
                    
                #elif np.any(np.isnan(float(chuck5[0]))) and np.any(np.isnan(float(chuck5[1]))):
                    #continue
            else:
                df.at[i, 'ΩΡΑ ΛΗΞΗΣ'] = chuck5

            if len(chunk6) == 2:
                first_value6, second_value6 = chunk6   
                df.at[i, 'DHMOS-KOINOTITA Latin'] = first_value6
            else:
                df.at[i, 'DHMOS-KOINOTITA Latin'] = chunk6    

        # save pdf file name for every entry
        df['PDF File Name'] = str(os.path.basename(self.pdf_path))

        # dimourgoume neo arxeio excel an den uparxei idi gia to database
        if not os.path.isfile(database_path):
            print('Dimiourgia neou Sqlite Database, den brethike proigoumeno')
            connection = sqlite3.connect(database_path)

            df.to_sql(self.table_name_database, connection, if_exists='replace', index=False)
            connection.close()
        else:
            # enimerooume to uparxwn excel arxeio an uparxei
            print('Updating Database...')
            #df_existing = pd.read_excel(database_path, header=0)
            #self.update_old(df, df_old database_path)
            self.update_database(df, self.table_name_database, database_path)
        return 0


    def update_database(self, df, table_name_database, database_path):
        connection = sqlite3.connect(database_path)

        cursor = connection.cursor()
        
        # get all tables from Database
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name_database}';")
        table_exists = cursor.fetchone()

        # check if table exists then update if not generate error
        if table_exists[0] == self.table_name_database:
            for index, row in df.iterrows():
                cursor.execute(f"""
                               UPDATE {table_name_database}
                               SET
                               "ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ" = ?,
                               "ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ" = ?,
                               "DHMOS-KOINOTITA Latin" = ?,
                               "ΗΜΕΡΟΜΗΝΙΑ ΕΝΑΡΞΗΣ" = ?,
                               "ΩΡΑ ΕΝΑΡΞΗΣ" = ?,
                               "ΗΜΕΡΟΜΗΝΙΑ ΛΗΞΗΣ" = ?,
                               "ΩΡΑ ΛΗΞΗΣ" = ?,
                               "ΚΑΜΕΝΗ ΕΚΤΑΣΗ" = ?,
                               "PDF File Name" = ?
                               WHERE "Α/Α" = ?;
                               """,(
                               row['ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ'],
                               row['ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'],
                               row['DHMOS-KOINOTITA Latin'],
                               row['ΗΜΕΡΟΜΗΝΙΑ ΕΝΑΡΞΗΣ'],
                               row['ΩΡΑ ΕΝΑΡΞΗΣ'],
                               row['ΗΜΕΡΟΜΗΝΙΑ ΛΗΞΗΣ'],
                               row['ΩΡΑ ΛΗΞΗΣ'],
                               row['ΚΑΜΕΝΗ ΕΚΤΑΣΗ'],
                               row['PDF File Name'],
                               row['Α/Α']))

                if cursor.rowcount == 0:
                    cursor.execute(f"""
                                  INSERT INTO {table_name_database} (
                                  "Α/Α", 
                                  "ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ",
                                  "ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ",
                                  "DHMOS-KOINOTITA Latin",
                                  "ΗΜΕΡΟΜΗΝΙΑ ΕΝΑΡΞΗΣ",
                                  "ΩΡΑ ΕΝΑΡΞΗΣ",
                                  "ΗΜΕΡΟΜΗΝΙΑ ΛΗΞΗΣ",
                                  "ΩΡΑ ΛΗΞΗΣ",
                                  "ΚΑΜΕΝΗ ΕΚΤΑΣΗ",
                                  "PDF File Name"
                                  )
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                                  """,(
                                  row['Α/Α'],
                                  row['ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ'],
                                  row['ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'],
                                  row['DHMOS-KOINOTITA Latin'],
                                  row['ΗΜΕΡΟΜΗΝΙΑ ΕΝΑΡΞΗΣ'],
                                  row['ΩΡΑ ΕΝΑΡΞΗΣ'],
                                  row['ΗΜΕΡΟΜΗΝΙΑ ΛΗΞΗΣ'],
                                  row['ΩΡΑ ΛΗΞΗΣ'],
                                  row['ΚΑΜΕΝΗ ΕΚΤΑΣΗ'],
                                  row['PDF File Name']
                                     ))
        else:
            print('Table not Found in Database, Check File Path!')
            exit(22)

        connection.commit()
        connection.close()

        return 0      







    def update_old(self, df_new, df_old, database_path):
        try:
            # Load the existing data from the Excel file
            df_old = pd.read_excel(database_path)

            # Ensure the column used for updating is present in both DataFrames
            if 'Α/Α' not in df_old.columns or 'Α/Α' not in df_new.columns:
                raise ValueError("Column 'Α/Α' not found in one of the DataFrames.")

            # Convert 'Α/Α' column to string to ensure consistent data type for comparison
            df_old['Α/Α'] = df_old['Α/Α'].astype(str)
            df_new['Α/Α'] = df_new['Α/Α'].astype(str)

            # Set 'Α/Α' as index for both DataFrames to facilitate updating
            df_old.set_index('Α/Α', inplace=True)
            df_new.set_index('Α/Α', inplace=True)

            # Update existing rows in df_old with values from df_new
            df_old.update(df_new)

            # Identify rows in df_new that are not in df_old
            new_rows = df_new[~df_new.index.isin(df_old.index)]

            # Concatenate df_old with new rows from df_new
            df_combined = pd.concat([df_old, new_rows])

            # Reset index to make 'Α/Α' a column again
            df_combined.reset_index(inplace=True)

            # Save the updated DataFrame to the Excel file
            df_combined.to_excel(database_path, header=True, index=False)
            print('To Database enimerothike!')

            return 0

        except Exception as e:
            print(f'An error occurred: {e}')
            return 1



    def save_to_excel(self, excel_path):        
        # ftiaxoume ta tables
        tables = self.tables

        merged_tables = pd.concat(tables, ignore_index=True)
        merged_tables = self.fix_names(merged_tables)
        merged_tables = self.check_for_nans(merged_tables)

        # prepei na diagra3oume ta nan kai na feroume mia thesi panw oti exei apo katw tous
        # merged_tables['Α/Α'] = shift_up(merged_tables['Α/Α'])
        # merged_tables['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'] = shift_up(merged_tables['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'])
        # merged_tables['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'] = shift_up(merged_tables['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'])
        # merged_tables['ΩΡΑ ΕΝΑΡΞΗΣ'] = shift_up(merged_tables['ΩΡΑ ΕΝΑΡΞΗΣ'])
        # merged_tables = merged_tables.dropna(subset=['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'])
        # merged_tables = merged_tables.dropna(subset=['ΩΡΑ ΕΝΑΡΞΗΣ'])
        # merged_tables = merged_tables.fillna(-1)

        # stiles pou tha exei to teliko dataframe
        df = pd.DataFrame(columns=['Α/Α',
                                   'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ',
                                   'ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ',
                                   'DHMOS-KOINOTITA Latin',
                                   'ΗΜΕΡΟΜΗΝΙΑ ΕΝΑΡΞΗΣ',
                                   'ΩΡΑ ΕΝΑΡΞΗΣ',
                                   'ΗΜΕΡΟΜΗΝΙΑ ΛΗΞΗΣ',
                                   'ΩΡΑ ΛΗΞΗΣ',
                                   'ΚΑΜΕΝΗ ΕΚΤΑΣΗ',
                                   'ΕΝΤΟΠΙΣΜΟΣ FireHUB',
                                   'ΗΜΕΡΟΜΗΝΙΑ ΚΑΙ ΩΡΑ ΕΝΤΟΠΙΣΜΟΥ Firehub',
                                   'ΑΙΤΙΟΛΟΓΙΑ ΜΗ ΕΝΤΟΠΙΣΜΟΥ',
                                   'ΕΙΚΟΝΕΣ Seviri ΓΙΑ ΕΛΕΓΧΟ',
                                   'ΨΗΦΙΟΠΟΙΗΣΗ',
                                   'PDF File Name'
                                   ])

        merged_tables['DHMOS-KOINOTITA Latin'] = merged_tables['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'].str.replace('Δ.', '', regex=False)
        merged_tables['DHMOS-KOINOTITA Latin'] = merged_tables['DHMOS-KOINOTITA Latin'].apply(self.normalize_and_transliterate)
        
        rows = []
        for i in range(0, len(merged_tables), 2):
            # pernoume dedomena ana 2 grammes
            chunk = merged_tables.iloc[i:i + 2]['Α/Α'].values
            if len(chunk) == 2:
                first_value, second_value = chunk
                df.at[i, 'Α/Α'] = second_value

        rows = []
        for i in range(0, len(merged_tables), 2):
            # pernoume dedomena ana 2 grammes
            chunk1 = merged_tables.iloc[i:i + 2]['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'].values
            # print(chunk1)
            chunk2 = merged_tables.iloc[i:i + 2]['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'].values
            # print(chunk2)
            chunk3 = merged_tables.iloc[i:i + 2]['ΩΡΑ ΕΝΑΡΞΗΣ'].values
            # print(chunk3)
            chunk4 = merged_tables.iloc[i:i + 2]['ΚΑΜΕΝΗ ΕΚΤΑΣΗ (Στρέμματα)'].values
            # print(chunk4)
            chuck5 = merged_tables.iloc[i:i + 2]['ΠΛΗΡΗΣ ΚΑΤΑΣΒΕΣΗ'].values
            #print(chuck5)
            chunk6 = merged_tables.iloc[i:i + 2]['DHMOS-KOINOTITA Latin'].values
            #print(chunk6)

            if len(chunk1) == 2:
                first_value1, second_value1 = chunk1
                if first_value1 == '-':
                    df.at[i, 'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ'] = second_value1
                elif second_value1 == '-':
                    df.at[i, 'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ'] = first_value1
                else:
                    df.at[i, 'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ'] = f"{first_value1}, {second_value1}"
            else:
                df.at[i, 'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ'] = chunk1
            
            if len(chunk2) == 2:
                first_value2, second_value2 = chunk2
                df.at[i, 'ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'] = first_value2
            else:
                df.at[i, 'ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ'] = chunk2
            
            if len(chunk3) == 2:
                first_value3, second_value3 = chunk3
                day3, month3 = first_value3.split('/')
                df.at[i, 'ΗΜΕΡΟΜΗΝΙΑ ΕΝΑΡΞΗΣ'] = str(self.current_year) + '-' + month3 + '-' + day3
                df.at[i, 'ΩΡΑ ΕΝΑΡΞΗΣ'] = second_value3
            else:
                df.at[i, 'ΩΡΑ ΕΝΑΡΞΗΣ'] = chunk3
            
            if len(chunk4) == 2:
                first_value4, second_value4 = chunk4
                df.at[i, 'ΚΑΜΕΝΗ ΕΚΤΑΣΗ'] = first_value4
            else:
                df.at[i, 'ΚΑΜΕΝΗ ΕΚΤΑΣΗ'] = chunk4
            
            if len(chuck5) == 2:
                if isinstance(chuck5[0], str) or isinstance(chuck5[1], str):
                    first_value5, second_value5 = chuck5
                    day5, month5 = first_value5.split('/')
                    df.at[i, 'ΗΜΕΡΟΜΗΝΙΑ ΛΗΞΗΣ'] = str(self.current_year) + '-' + month5 + '-' + day5
                    df.at[i, 'ΩΡΑ ΛΗΞΗΣ'] = second_value5
                    
                #elif np.any(np.isnan(float(chuck5[0]))) and np.any(np.isnan(float(chuck5[1]))):
                    #continue
            else:
                df.at[i, 'ΩΡΑ ΛΗΞΗΣ'] = chuck5
            
            if len(chunk6) == 2:
                first_value6, second_value6 = chunk6   
                df.at[i, 'DHMOS-KOINOTITA Latin'] = first_value6
            else:
                df.at[i, 'DHMOS-KOINOTITA Latin'] = chunk6
        
        # save pdf file name for every entry
        df['PDF File Name'] = str(os.path.basename(self.pdf_path))

        # dimourgoume neo arxeio excel an den uparxei idi gia to database
        if not os.path.exists(excel_path):
            os.makedirs(excel_path)

        excel_path_name = excel_path + os.path.basename(self.pdf_path).replace('.pdf', '').replace('pdf_Data/', '') + '.xlsx'
        print('Dimiourgia neou Excel,', excel_path_name)
        df.to_excel(excel_path_name, header=True, index=False)

        return 0
    


    def normalize_and_transliterate(self, text):
        if isinstance(text, float):
            return 'nan'
        # Normalize the text (NFKD form)
        normalized_text = unicodedata.normalize('NFKD', text)
        # Remove accents using unidecode and convert to lowercase
        transliterated_text = unidecode(normalized_text).lower()
        return transliterated_text
    


        
        