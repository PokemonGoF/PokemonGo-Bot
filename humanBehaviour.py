import time
from random import randint

def sleep(seconds):
    jitter = seconds * 1000 / 10
    sleep_time = randint( seconds-jitter ,seconds+jitter)
    time.sleep(sleep_time)