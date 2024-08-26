import tabula
import pandas as pd
import numpy as np
import os
from pyrosvestiki import DeltiaFire
# To A/A einai me ellinika grammata


def main():
    pdf_path_folder = './pdf_Data/'
    database_path = './Deltia_Database.xlsx'
    excel_path_outputs = './excel_output/'

    for file in os.listdir(pdf_path_folder):
        if file.endswith('.pdf'):
            print('Processing file:', file)
            # Orizoume ena oject typou pyrosvestiki kai bazoume mesa ta DataFrames
            # pernoume tous pinakes apo to arxeio .pdf kai ta bazoume se ena DataFrame
            deltio = DeltiaFire(os.path.join(pdf_path_folder, file))
            # kanoume oti tropopoisi xreiazete sto DataFrame (vlepe pyrosvestiki.py)
            tables = deltio.get()
            # enimerosi tou excel me ta proigoumena deltia kai prosthiki twn newn entrys
            deltio.save_to_database(tables, database_path)
            # apothikeusi kathe deltiou 3exorista
            deltio.save_to_excel(tables, os.path.join(excel_path_outputs, file.replace('.pdf','.xlsx')))
            print('\n')
    print('Done!')

if __name__ == "__main__":
    main()
