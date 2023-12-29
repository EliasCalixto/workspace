import os

def ping():
    text = os.popen('ping hostingplus.cl').readlines(100)
    del text[0]
    try:
        return text[1][40:44]
    except:
        return 'Err'
    