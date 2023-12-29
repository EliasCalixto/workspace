from datetime import datetime
from tools.emoticons import *
from tools.ping import ping
from tools.moneyStatus import getPercentBlue, getPercentRed
from tools.notion import get_notion_count


def monitor():

    """
    try:
        valor_cpu = int(cpu_usage())
    except:
        valor_cpu = 'E'
    try:
        if valor_cpu < 51:
            cpu_emo = '\U00002705'
        elif valor_cpu < 75:
            cpu_emo = '\U000026A1'
        else:
            cpu_emo = '\U0001FA78'
    except:
        cpu_emo = '\U0001FA78'
    """   
    
    # last print
  
    if get_notion_count() == 0:
        print(f'[{money}{getPercentBlue()}%/{getPercentRed()}%] {red_emo}{ping()}'.expandtabs(2), end='')
        print(f'')
    else:
        print(f'[{get_notion_count()}] [{money}{getPercentBlue()}%/{getPercentRed()}%] {red_emo}{ping()}'.expandtabs(2), end='')
        print(f'')
        

if __name__ == '__main__':
    monitor()

