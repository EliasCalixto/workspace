import os

def gpu_usage():
    try:
        text = os.popen('nvidia-smi').readlines()
        return text[9][71:74]
    except:
        return 'error getting data'

if __name__ == '__main__':
    print(gpu_usage())
