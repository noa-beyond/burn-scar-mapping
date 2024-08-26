import tabula
import pandas as pd
import numpy as np
import os
# To A/A einai me ellinika grammata

def extract_tables_from_pdf(pdf_path):
    # get tables from pdf
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
    return tables

def save_tables_to_excel(tables, excel_path):
    merged_tables = pd.concat(tables, ignore_index=True)
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        merged_tables.to_excel(writer, index=False)
    return 0

def sum_numbers(cell):
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

def delete_rows_rename(tables):
    for i in range(0, len(tables)):
        tables[i].drop(["ΧΡΟΝΟΛΟΓΙΑ" ,"Unnamed: 1", "Unnamed: 2",
                        "Unnamed: 3", "Unnamed: 4", "Unnamed: 5",
                        "ΠΡΟΣΩΠΙΚΟ", "Unnamed: 6", "Unnamed: 7",
                        "ΜΕΣΑ", "Unnamed: 8", "Unnamed: 9"],
                        axis=1, inplace = True)

        tables[i].rename(columns = {'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ':'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ',
                                    'ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ':'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ',
                                    'Unnamed: 0':'ΩΡΑ ΕΝΑΡΞΗΣ'},
                         inplace=True)

        tables[i]['ΚΑΜΕΝΗ ΕΚΤΑΣΗ (Στρέμματα)'] = tables[i]['ΚΑΜΕΝΗ ΕΚΤΑΣΗ (Στρέμματα)'].apply(sum_numbers)

        tables[i] = tables[i].drop( tables[i][tables[i]['Α/Α'] == 'Α/Α ΠΥΡΚ'].index )
        tables[i] = tables[i].drop( tables[i][tables[i]['ΩΡΑ ΕΝΑΡΞΗΣ'] == 'ΕΝΑΡ.'].index )
    return tables

def update_old(df_new, df_old, database_path):
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

def fix_names(table):
    for i in range(table.shape[0]):
        if pd.isna(table.at[i, 'Α/Α']) and pd.notna(table.at[i, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ']):
            table.at[i-1, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'] = f"{table.at[i-1, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ']} {table.at[i, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ']}"
        elif pd.isna(table.at[i, 'Α/Α']) and pd.isna(table.at[i, 'ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ']):
            table.at[i-1, 'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'] = f"{table.at[i-1, 'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ']} {table.at[i, 'ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ']}"
            if pd.isna(table.at[i,  'ΩΡΑ ΕΝΑΡΞΗΣ']):
                table.at[i+2, 'ΩΡΑ ΕΝΑΡΞΗΣ'] = table.at[i+1, 'ΩΡΑ ΕΝΑΡΞΗΣ']


    return table

def check_for_nans(table):
    rowsToDelete = set()
    for i in range(table.shape[0]):
        if pd.isna(table.at[i, 'Α/Α']):
            rowsToDelete.add(i)
    table = table.drop(index=rowsToDelete).reset_index(drop=True)
    return table

def shift_up(column):
    # Drop NaNs and reset the index
    non_nan_values = column.dropna().reset_index(drop=True)
    # Calculate the number of NaNs
    num_nans = column.isna().sum()
    # Create a new series with NaNs at the end
    filled_column = pd.concat([non_nan_values, pd.Series([np.nan] * num_nans)], ignore_index=True)
    return filled_column

def save_to_database(tables, database_path):

    merged_tables = pd.concat(tables, ignore_index=True)
    merged_tables = fix_names(merged_tables)
    merged_tables = check_for_nans(merged_tables)


    # prepei na diagra3oume ta nan kai na feroume mia thesi panw oti exei apo katw tous
    #merged_tables['Α/Α'] = shift_up(merged_tables['Α/Α'])
    #merged_tables['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'] = shift_up(merged_tables['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'])
    #merged_tables['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'] = shift_up(merged_tables['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'])
    #merged_tables['ΩΡΑ ΕΝΑΡΞΗΣ'] = shift_up(merged_tables['ΩΡΑ ΕΝΑΡΞΗΣ'])
    #merged_tables = merged_tables.dropna(subset=['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'])
    #merged_tables = merged_tables.dropna(subset=['ΩΡΑ ΕΝΑΡΞΗΣ'])
    #merged_tables = merged_tables.fillna(-1)

    # stiles pou tha exei to teliko dataframe
    df = pd.DataFrame(columns=['Α/Α',
                               'ΠΥΡ/ΚΗ ΥΠΗΡΕΣΙΑ',
                               'ΔΗΜΟΣ-ΚΟΙΝΟΤΗΤΑ',
                               'ΗΜΕΡΟΜΗΝΙΑ ΕΝΑΡΞΗΣ',
                               'ΩΡΑ ΕΝΑΡΞΗΣ',
                               'ΚΑΜΕΝΗ ΕΚΤΑΣΗ',
                               'Εντοπισμός FireHUB',
                               'Αιτιολογία',
                               'Ώρα εντοπισμού',
                               'ΨΗΦΙΟΠΟΙΗΣΗ',
                               'Εικόνες Seviri για έλεγχο'
                               ])

    rows = []
    for i in range(0, len(merged_tables), 2):
        # Get the values for the current chunk
        chunk = merged_tables.iloc[i:i + 2]['Α/Α'].values
        if len(chunk) == 2:
            first_value, second_value = chunk
            df.at[i, 'Α/Α'] = second_value

    rows = []
    for i in range(0, len(merged_tables), 2):
        # Get the values for the current chunk
        chunk1 = merged_tables.iloc[i:i + 2]['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ'].values
        #print(chunk1)
        chunk2 = merged_tables.iloc[i:i + 2]['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'].values
        #print(chunk2)
        chunk3 = merged_tables.iloc[i:i + 2]['ΩΡΑ ΕΝΑΡΞΗΣ'].values
        #print(chunk3)
        chunk4 = merged_tables.iloc[i:i + 2]['ΚΑΜΕΝΗ ΕΚΤΑΣΗ (Στρέμματα)'].values
        #print(chunk4)

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
            df.at[i, 'ΗΜΕΡΟΜΗΝΙΑ ΕΝΑΡΞΗΣ'] = first_value3
            df.at[i, 'ΩΡΑ ΕΝΑΡΞΗΣ'] = second_value3
        else:
            df.at[i, 'ΩΡΑ ΕΝΑΡΞΗΣ'] = chunk3

        if len(chunk4) == 2:
            first_value4, second_value4 = chunk4
            df.at[i, 'ΚΑΜΕΝΗ ΕΚΤΑΣΗ'] = first_value4
        else:
            df.at[i, 'ΚΑΜΕΝΗ ΕΚΤΑΣΗ'] = chunk4




    #print(merged_tables['ΔΗΜΟΣ/ΚΟΙΝΟΤΗΤΑ'])
    #print(df['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ 1'])
    #print(df['ΠΥΡΟΣΒΕΣΤΙΚΗ ΥΠΗΡΕΣΙΑ 2'])
    #print(df['ΚΑΜΕΝΗ ΕΚΤΑΣΗ (Στρέμματα)'])

    # fix later if not
    if not os.path.isfile(database_path):
        print('Dimiourgia neou Excel, den brethike proigoumeno')
        df.to_excel(database_path, header=True, index=False)
    else:
        print('Enimerosi Excel...(old entrys)')
        df_existing = pd.read_excel(database_path, header=0)
        update_old(df, df_existing, database_path)
    return 0


def main():
    pdf_path = 'Δελτίο Σοβαρών Δασικών 22-07-2024.pdf'
    excel_path = pdf_path + '.xlsx'
    database_path = 'Deltia_Database.xlsx'

    tables = extract_tables_from_pdf(pdf_path)
    # delete this
    #save_tables_to_excel(tables, excel_path)
    #exit(22)

    tables = delete_rows_rename(tables)
    #print(tables[0].head())
    #print(tables[0].columns.tolist(), tables[1].columns.tolist())

    # dimiourgia neou arxeiou excel me ta entrys tou deltiou
    save_tables_to_excel(tables, excel_path)
    print("To neo Deltio Sothike me onoma :", excel_path)

    # enimerosi tou excel me ta proigoumena deltia kai prosthiki twn newn entrys
    save_to_database(tables, database_path)



if __name__ == "__main__":
    main()
