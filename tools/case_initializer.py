import os
import pandas as pd


def init_case(case_number: int, data_frame: list, file_path: str) -> None:
    """

    :rtype: object
    """
    try:
        os.mkdir(f'APM files/{case_number}')
        print('Directory created successfully.')
    except:
        pass

    #Create Excel
    df_file = pd.DataFrame(data_frame)
    file_path = f'APM files/{case_number}/{case_number} {file_path}'
    
    df_file.to_excel(file_path, index=False)
    #print(f"File '{file_path}' has been created.")
    
