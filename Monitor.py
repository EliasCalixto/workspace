from datetime import datetime
from tools.emoticons import *
from tools.moneyStatus import getPercentBlue, getPercentRed
from tools.notion import get_notion_count, get_notion_summary


def monitor():

    # last print 
    if get_notion_count() == 0:
        print(f'[{money}{getPercentBlue()}%/{getPercentRed()}%]'.expandtabs(2), end='')
        print(f'')
    else:
        print(f'{notion_emoticon}{get_notion_count()} [{money}{getPercentBlue()}%/{getPercentRed()}%]'.expandtabs(2), end='')
        print(f'')
        

if __name__ == '__main__':
    monitor()

