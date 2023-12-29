import os

def cpu_usage():
    try:
        text = os.popen('wmic cpu get loadpercentage').readlines()
        try:
            del text[0]
            del text[0]
            del text[1]
            del text[1]
            del text[1]
            return text[0]
        except:
            return '0'
        
    except:
        return '0'

if __name__ == '__main__':
    print(cpu_usage())
