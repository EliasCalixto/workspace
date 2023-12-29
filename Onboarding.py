from tools.caseInitializer import initCase
import os
import pandas as pd


removeStopSellingFilePath = 'IMPORT Stop Sell Removal.xlsx'

def ob():
    print('')
    caseNumber = input('Case: ')
    hotelID = input('Hotel ID: ')
      
    if hotelID == '':
        dataFrame = {
            'Hotel ID':[''],
            'SF ID': [''],
            'Stop Sell Property':['No'],
            'Action Type':['Update']
        }
        initCase(caseNumber, dataFrame, removeStopSellingFilePath)
        os.mkdir(f'APM files/{caseNumber}/Imports Results')
        
        #Create ManagedBy File
        dataCsv = {
            'Account ID': [],
            'Managed by': []
        }

        # Create a DataFrame from the data
        dfCsv = pd.DataFrame(dataCsv)
        # Specify the file name and path
        file_pathCsv = f'APM files/{caseNumber}/{caseNumber} UpdateManagedBy.csv'
        # Write the DataFrame to and Excel file
        dfCsv.to_csv(file_pathCsv, index=False)
        #print(f"ManagedBy.csv file has been created.")
        
    else:
        dataFrame = {
            'Hotel ID':[f'{hotelID}'],
            'Stop Sell Property':['No'],
            'Action Type':['Update']
        }
        initCase(caseNumber, dataFrame, removeStopSellingFilePath)
        os.mkdir(f'APM files/{caseNumber}/Imports Results')
    
    
    print('')
    print('Ready to work on case.')
    print('')
    
    return caseNumber

if __name__ == "__main__":
    ob()
