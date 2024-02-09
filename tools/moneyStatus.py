import numpy as np
import pandas as pd


try:
    dataFrame = pd.read_excel("C:\\Users\\elias\\OneDrive\\Documentos\\Main.xlsx", sheet_name='data')
    allData = np.array(dataFrame)
except:
    dataFrame = pd.read_excel("/Users/darkesthj/Library/CloudStorage/OneDrive-Personal/Documentos/Main.xlsx", sheet_name='data')
    allData = np.array(dataFrame)

def getCurrentMonth():
    index = 0

    while allData[:,0][index] != 0:
        index += 1

    currentMonth = allData[index-1]
    
    return currentMonth

def getTotalBlue():
    currentMonth = getCurrentMonth()
    totalBlue = round(np.sum(currentMonth[1:4]),2)
    return f'{totalBlue}'
    
def getTotalRed():
    currentMonth = getCurrentMonth()
    totalRed = round(np.sum(currentMonth[4:7]),2)
    return f'{totalRed}'

def getCurrentMoney():
    currentMonth = getCurrentMonth()
    currentMoney = round(currentMonth[8],2)
    return f'{currentMoney}'
    
if __name__ == '__main__':
    print(f'{getTotalBlue()}/{getTotalRed()}/{getCurrentMoney()}')
