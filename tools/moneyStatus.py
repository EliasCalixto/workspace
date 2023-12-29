import numpy as np
import pandas as pd

try:
    data_frame = pd.read_excel('..\..\OneDrive\Documentos\Main.xlsx' ,sheet_name='data')
    allData = np.array(data_frame)
    totalGastos = (np.sum(allData[:,1:-1]))
except:
    print("can't find 'Main.xlsx'")


def getPercentBlue():
    totalBlue = (np.sum(allData[:,1:4])) + (np.sum(allData[:,7]))
    percentBlue = round((totalBlue/totalGastos)*100,2)
    return f'{percentBlue}'

def getPercentRed():
    totalRed = np.sum(allData[:,4:7])
    percentRed = round((totalRed/totalGastos)*100,2)
    return f'{percentRed}'

if __name__ == '__main__':
    print(f'{getPercentBlue()}/{getPercentRed()}')
