# -*- coding: utf-8 -*-

import time
from random import random, uniform


def sleep(seconds, delta=0.3):
    time.sleep(jitter(seconds,delta))


def jitter(value, delta=0.3):
    jitter = delta * value
    return uniform(value-jitter, value+jitter)


def action_delay(low, high):
    # Waits for random number of seconds between low & high numbers
    longNum = uniform(low, high)
    shortNum = float("{0:.2f}".format(longNum))
    time.sleep(shortNum)


def random_lat_long_delta():
    # Return random value from [-.000025, .000025]. Since 364,000 feet is equivalent to one degree of latitude, this
    # should be 364,000 * .000025 = 9.1. So it returns between [-9.1, 9.1]
    return ((random() * 0.00001) - 0.000005) * 5


# Humanized `normalized_reticle_size` parameter for `catch_pokemon` API.
# 1.0 => normal, 1.950 => excellent
def normalized_reticle_size(factor):
    minimum = 1.0
    maximum = 1.950
    return uniform(
        minimum + (maximum - minimum) * factor,
        maximum)


# Humanized `spin_modifier` parameter for `catch_pokemon` API.
# 0.0 => normal ball, 1.0 => super spin curve ball
def spin_modifier(factor):
    minimum = 0.0
    maximum = 1.0
    return uniform(
        minimum + (maximum - minimum) * factor,
        maximum)
