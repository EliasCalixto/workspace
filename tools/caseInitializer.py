import os
import pandas as pd


def initCase(caseNumber: int, dataFrame: list, filePath: str) -> None:
    try:
        os.mkdir(f'APM files/{caseNumber}')
        print('Directory created successfully.')
    except:
        print('Error creating Case Directory')

    #Create Excel
    dfFile = pd.DataFrame(dataFrame)
    file_path = f'APM files/{caseNumber}/{caseNumber} {filePath}'
    
    dfFile.to_excel(file_path, index=False)
    #print(f"File '{file_path}' has been created.")
    
