import time
from math import ceil
from random import random, randint

def sleep(seconds, jitter=0.1):
    jitter = ceil(0.1 * seconds)
    sleep_time = randint(seconds-jitter, seconds+jitter)
    time.sleep(sleep_time)

def random_lat_long_delta():
    # Return random value from [-.000025, .000025]. Since 364,000 feet is equivalent to one degree of latitude, this
    # should be 364,000 * .000025 = 9.1. So it returns between [-9.1, 9.1]
    return ((random() * 0.00001) - 0.000005) * 5
