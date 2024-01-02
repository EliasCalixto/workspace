from datetime import datetime
from tools.emoticons import *
from tools.ping import ping
from tools.moneyStatus import getPercentBlue, getPercentRed
from tools.notion import get_notion_count


def monitor():

    # last print 
    if get_notion_count() == 0:
        print(f'[{money}{getPercentBlue()}%/{getPercentRed()}%] {red_emo}{ping()}'.expandtabs(2), end='')
        print(f'')
    else:
        print(f'[{get_notion_count()}] [{money}{getPercentBlue()}%/{getPercentRed()}%] {red_emo}{ping()}'.expandtabs(2), end='')
        print(f'')
        

if __name__ == '__main__':
    monitor()

