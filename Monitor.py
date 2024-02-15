from tools.emoticons import *
from tools.moneyStatus import getTotalBlue, getTotalRed, getCurrentMoney
from tools.notion import get_notion_count, get_notion_summary


def monitor():
    # last print 
    if get_notion_count() == 0:
        print(f'[{moneyBlue}{getTotalBlue()} {moneyRed}{getTotalRed()} {money}{getCurrentMoney()}]'.expandtabs(2), end='')
        print(f'')
    else:
        print(f'{notion_emoticon}{get_notion_count()} [{moneyBlue}{getTotalBlue()} {moneyRed}{getTotalRed()} {money}{getCurrentMoney()}]'.expandtabs(2), end='')
        print(f'')
        

if __name__ == '__main__':
    monitor()

