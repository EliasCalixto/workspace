import os
import sys
import pandas as pd
from tools.case_initializer import init_case

remove_stop_selling_file_path = 'IMPORT Stop Sell Removal.xlsx'

def onboarding():
    args = []
    
    for i,arg in enumerate(sys.argv):
        args.append(arg)

    if len(args) == 2:
        data_frame = {
            'Hotel ID':[''],
            'SF ID': [''],
            'Stop Sell Property':['No'],
            'Action Type':['Update']
        }
        init_case(args[1], data_frame, remove_stop_selling_file_path) # type: ignore
        os.mkdir(f'APM files/{args[1]}/Imports Results')
        
        #Create ManagedBy File
        data_csv = {
            'Account ID': [],
            'Managed by': []
        }

        # Create a DataFrame from the data
        df_csv = pd.DataFrame(data_csv)
        # Specify the file name and path
        file_path_csv = f'APM files/{args[1]}/{args[1]} UpdateManagedBy.csv'
        # Write the DataFrame to and Excel file
        df_csv.to_csv(file_path_csv, index=False)
        #print(f"ManagedBy.csv file has been created.")
        
    elif len(args) == 3:
        data_frame = {
            'Hotel ID':[f'{args[2]}'],
            'Stop Sell Property':['No'],
            'Action Type':['Update']
        }
        init_case(args[1], data_frame, remove_stop_selling_file_path) # type: ignore
        os.mkdir(f'APM files/{args[1]}/Imports Results')
    
    else:
        print('Does not met arguments requirements, directory not created.')

if __name__ == "__main__":
    onboarding()
