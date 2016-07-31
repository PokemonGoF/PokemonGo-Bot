# -*- coding: utf-8 -*-

import time
from math import exp
from random import random, gauss, uniform
from collections import defaultdict


def lognormal_model(path='data/lognormal.model'):
    '''
    lazy initialization of model
    '''
    if not hasattr(lognormal_model, 'delay_range2mu_sigma'):
        lognormal_model.delay_range2mu_sigma = defaultdict(dict)
        for line in open(path):
            delay, delay_range, mu_, sigma = line.strip().split(',')
            lognormal_model.delay_range2mu_sigma \
                    [int(delay)][int(delay_range)] = \
                    (float(mu_), float(sigma))
    return lognormal_model.delay_range2mu_sigma


def pareto(alpha=5.0, cap=10):
    '''
    somehow reflects human behaviour (Zipf's law)
    transformed to return [alpha-1/alpha, inf) with mean of 1.0
    capped to prevent inf
    '''
    alpha = float(alpha)
    return min((alpha - 1) / alpha / ((1 - random())**(1 / alpha)), cap)


def lognormal(mu_, sigma):
    '''
    Good assumption for ping, human reflexes.
    mu and sigma are for the lognormal, not the values you see.
    Use model parameter to get what you want.
    '''
    return exp(gauss(mu_, sigma))


def sleep(seconds):
    '''
    sleep for (given seconds + jitter + human reflex) seconds.
    '''
    time.sleep(seconds + jitter_rng() + human_reflex_rng())


def jitter_rng(ping=80, ping_range=30):
    '''
    Simple lognormal jitter model for given ping and range.
    Actually wider range is preferred for accurate modeling,
    but we don't want to spend much time...
    '''
    ping = int(ping / 10) * 10
    ping_range = int(ping_range / 5) * 5
    ping = min(max(10, ping), 500)
    ping_range = min(max(10, ping_range), 100)
    mu_, sigma = lognormal_model()[ping][ping_range]
    lag = lognormal(mu_, sigma)
    lag = min(1.0, lag)
    return lag


def human_reflex_rng(reflex_mean=270, reflex_range=100):
    '''
    Simulates human reflexes.
    '''
    mu_, sigma = lognormal_model()[reflex_mean][reflex_range]
    return min(1.0, lognormal(mu_, sigma))


def random_lat_long_delta(radius=0.00025):
    '''
    Simulates gps noise.
    '''
    # Return random value from [-.000025, .000025]ish 99.73% of time.
    # Since 364,000 feet is equivalent to one degree of latitude, this
    # Gaussian is better for gps errors
    noise = gauss(0, radius/3.0)
    noise = min(max(-radius, noise), radius)
    return noise


def action_delay(low, high):
    # Waits for random number of seconds between low & high numbers
    longNum = uniform(low, high)
    shortNum = float("{0:.2f}".format(longNum))
    time.sleep(shortNum)


def ball_throw_reticle_fail_delay(success_prob=0.95):
    '''
    Chances to skip the reticle could be considered constant,
    so the wait time before throwing is binomial,
    given that the pokemon does not interrupt... <- TODO
    '''
    for trial in range(10):
        if random() < success_prob:
            break

    time.sleep(1.8*(trial+random()))


def aim_rng(target, std=0.05):
    '''
    noise from the target point should be approximated by gaussian,
    we can wait for the missed reticles etc, which means we get
    another chance to try...
    
    '''
    for trial in range(10):
        r = gauss(0, std)
        if 0 <= target + r and target + r <= 1:
            break
    else:
        # couldnt find target + gauss between [0, 1]
        return random()
    return target + r


# Humanized `normalized_reticle_size` parameter for `catch_pokemon` API.
# 1.0 => normal, 1.950 => excellent
def normalized_reticle_size(factor, mode='human'):
    if 'bot' == mode:
        return 1.950
    elif 'uniform' == mode:
        minimum = 1.0
        maximum = 1.950
        return uniform(
            minimum + (maximum - minimum) * factor,
            maximum)
    elif 'human' == mode:
        return 2 * aim_rng(factor)
    else:
        return mode(factor) # strategy


# Humanized `spin_modifier` parameter for `catch_pokemon` API.
# 0.0 => normal ball, 1.0 => super spin curve ball
def spin_modifier(factor, mode='human'):
    if 'bot' == mode:
        return 1.0
    elif 'uniform' == mode:
        minimum = 0.0
        maximum = 1.0
        return uniform(
            minimum + (maximum - minimum) * factor,
            maximum)
    elif 'human' == mode:
        return aim_rng(factor)
    else:
        return mode(factor)


def _precalc_lognormal_ping_param(
        output_file_path='lognormal_connection.model'):
    '''
    Precalc parameters for lognormal ping model.
    '''
    def calc_lognormal_ping_param(
            target_mu, target_std, init_mu=0.1, init_std=0.1, debug=False):
        # calculate mu and sighma for lognormal
        import numpy as np
        import theano
        import theano.tensor as T

        # codes to calculate lognormal connection lag
        mu_ = theano.shared(init_mu, name='mu')
        sigma = theano.shared(init_std, name='sigma')

        eps = 1.5  # constant for gradient
        func = (T.exp(mu_ + sigma * sigma / 2.0) - target_mu)**2 + \
            (T.sqrt(T.exp(2 * mu_ + sigma * sigma) *
                    (T.exp(sigma * sigma) - 1)) - target_std)**2

        grad_mu, grad_sigma = T.grad(func, [mu_, sigma])

        train = theano.function(inputs=[], outputs=[func], updates=(
            (mu_, mu_ - eps * grad_mu), (sigma, sigma - eps * grad_sigma)))

        for epoch in range(100000):
            err = train()
            if float(err[0]) < 10e-10:
                break
        err = float(err[0])
        mu_ = float(mu_.get_value())
        sigma = np.abs(sigma.get_value())
        if debug:
            print('Error:%s' % repr(err))
            print('[Expected mu and std]')
            print('mu=%f, std=%f' % (target_mu, target_std))
            print('[lognormal check]')
            print('mean=%f, std=%f' % (exp(mu_ + (sigma**2) / 2.0),
                                       ((exp(sigma**2) - 1) * exp(2 * mu_ + sigma**2))**0.5))
        return mu_, sigma

    # good initial number for algo
    init_mu = -1.5
    init_std = 0.007
    res = []
    for ping_ms in range(10, 501, 10):
        for range_ms in range(5, 101, 5):
            ping = ping_ms / 1000.0
            std = range_ms / 3.0 / 1000.0
            lognormal_mu, lognormal_std = calc_lognormal_ping_param(
                ping, std, init_mu, init_std)
            formatted = ','.join(map(repr, (ping_ms, range_ms, lognormal_mu, lognormal_std)))
            res.append(formatted)
            print(res[-1])
            init_mu = lognormal_mu
            init_std = lognormal_std

    with open(output_file_path, 'w') as fout:
        fout.write('\n'.join(res))


if '__main__' == __name__:
    _precalc_lognormal_ping_param()
