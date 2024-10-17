import os
import sys
import pandas as pd
from tools.caseInitializer import init_case

removeStopSellingFilePath = 'IMPORT Stop Sell Removal.xlsx'

def onboarding():
    args = []
    
    for i,arg in enumerate(sys.argv):
        args.append(arg)

    if len(args) == 2:
        dataFrame = {
            'Hotel ID':[''],
            'SF ID': [''],
            'Stop Sell Property':['No'],
            'Action Type':['Update']
        }
        init_case(args[1], dataFrame, removeStopSellingFilePath)
        os.mkdir(f'APM files/{args[1]}/Imports Results')
        
        #Create ManagedBy File
        dataCsv = {
            'Account ID': [],
            'Managed by': []
        }

        # Create a DataFrame from the data
        dfCsv = pd.DataFrame(dataCsv)
        # Specify the file name and path
        file_pathCsv = f'APM files/{args[1]}/{args[1]} UpdateManagedBy.csv'
        # Write the DataFrame to and Excel file
        dfCsv.to_csv(file_pathCsv, index=False)
        #print(f"ManagedBy.csv file has been created.")
        
    elif len(args) == 3:
        dataFrame = {
            'Hotel ID':[f'{args[2]}'],
            'Stop Sell Property':['No'],
            'Action Type':['Update']
        }
        init_case(args[1], dataFrame, removeStopSellingFilePath)
        os.mkdir(f'APM files/{args[1]}/Imports Results')
    
    else:
        print('Does not met arguments requirements, directory not created.')

if __name__ == "__main__":
    onboarding()
