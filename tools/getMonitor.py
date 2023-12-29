import pandas as pd
import numpy as np

try:
    data_frame = pd.read_excel('..\..\OneDrive\Documentos\Main.xlsx' ,sheet_name='moni-data')
    data = np.array(data_frame)
except:
    print("can't find 'Main.xlsx'")

def get_monitor_code():
    return round(data[0][0]*100)

def get_monitor_workout():
    return round(data[0][1]*100)

    
if __name__ == '__main__':
    print(data)
