# -*- coding: utf-8 -*-

import time
from collections import defaultdict
from config import get_config
from math import exp
from numpy.random import lognormal
from random import random, gauss, uniform

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


def random_lat_long_delta(radius=0.00025):
    '''
    Simulates gps noise??? Sounds more like a rng for random walk.
    Keep it here for now...
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


def sleep(seconds):
    '''
    General sleep with some lags.

    Configs:
    "max_sleep_time" = 60,

    '''
    # some of the actions don't need reflex replication, so removed from here.
    wait_time = seconds + jitter_rng()
    max_sleep = get_config('max_sleep_time', 60)
    time.sleep(min(wait_time, max_sleep))


def ball_throw_reticle_fail_delay():
    '''
    Chances to skip the reticle could be considered constant,
    so the wait time before throwing is as follows,
    given that the pokemon does not interrupt... <- TODO

    Configs:
    "replicate_reticle_fail_delay" = false,
    "reticle_fail_chance = 0.05",
    "reticle_fail_max_trial" = 10,
    '''
    if get_config('replicate_throw_reticle_fail_delay', false):
        fail_prob = get_config('throw_reticle_fail_chance', 0.05)
        for trial in range(get_config('reticle_fail_max_trial', 10)):
            if fail_prob < random():
                break

        time.sleep(1.8*(trial+random()))


def jitter_rng():
    '''
    Simulates jitter.

    Configs:
    "replicate_jitter" = false,
    "jitter_ping" = 80,
    "jitter_range" = 30,
    "jitter_max_seconds" = 1.0,

    '''
    replicate_jitter = get_config('replicate_jitter', False)
    jitter = 0
    if replicate_jitter:
        ping = get_config('jitter_ping', 80)
        ping_range = get_config('jitter_range', 30)

        ping = int(ping / 10) * 10
        ping_range = int(ping_range / 5) * 5
        ping = min(max(10, ping), 500)
        ping_range = min(max(10, ping_range), 100)
        mu_, sigma = lognormal_model()[ping][ping_range]
        jitter = lognormal(mu_, sigma)
        jitter = min(jitter, get_config('jitter_max_seconds', 1.0))
    return jitter


def human_reflex_rng():
    '''
    Simulates human reflexes.

    Configs:
    "replicate_reflex" = false,
    "reflex_time" = 270,
    "reflex_range" = 100,
    "reflex_max_seconds" = 1.0,

    '''
    reflex_time = 0
    if get_config('replicate_reflex', False):
        reflex_mean = get_config('reflex_time', 270)
        reflex_range = get_config('reflex_range', 100)
        mu_, sigma = lognormal_model()[reflex_mean][reflex_range]
        reflex_time = min(lognormal(mu_, sigma), get_config('reflex_max_seconds', 1.0))
    return reflex_time


def gps_noise_rng():
    '''
    Simulates gps noise. This may cause problem, so we need test.
    
    Configs:
    "replicate_gps_noise" = false,
    "gps_noise_radius = 0.00075"
    
    '''
    radius = get_config('gps_noise_radius', 0.00075)
    lat_noise = 0
    lng_noise = 0
    if get_config('replicate_gps_noise', False):
        lat_noise = gauss(0, radius/3.0)
        lat_noise = min(max(-radius, lat_noise), radius)
        
        lng_noise = gauss(0, radius/3.0)
        lng_noise = min(max(-radius, lng_noise), radius)

    return lat_noise, lng_noise


def aim_rng(target, std=0.05):
    '''
    noise from the target point should be approximated by gaussian,
    we can wait for the missed reticles etc, which means we get
    another chance to try...

    TODO: add nice conf name for this...
    
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
def normalized_reticle_size_rng():
    '''
    Reticle rng.

    Configs:
    "replicate_ball_throw_reticle" = "human",
    "normalized_reticle_size" = 0.9,

    '''
    factor = get_config('normalized_reticle_size', 0.9)
    if 'exact' == mode:
        return factor
    elif 'uniform' == mode:
        minimum = 1.0
        maximum = 1.950
        return uniform(
            minimum + (maximum - minimum) * factor,
            maximum)
    elif 'human' == mode:
        rnd = gauss(factor, 0.05)
        # mirror the bounds
        rnd = rnd%1.0
        return 1.950 * rnd
    return 1.950


# Humanized `spin_modifier` parameter for `catch_pokemon` API.
# 0.0 => normal ball, 1.0 => super spin curve ball
def spin_modifier_rng():
    '''
    Spin rng.

    Configs:
    "replicate_ball_throw_spin" = "human",
    "spin_modifier" = 0.9,

    '''
    factor = get_config('spin_modifier', 0.9)
    if 'exact' == mode:
        return 1.0
    elif 'uniform' == mode:
        minimum = 0.0
        maximum = 1.0
        return uniform(
            minimum + (maximum - minimum) * factor,
            maximum)
    elif 'human' == mode:
        return aim_rng(factor)
    return 1.0

"""
def _visualize():
    '''
    Visualize rng distributions.
    '''
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    K = 10000

    # lognormal simulations
    human_reflex = [human_reflex_rng() for x in range(K)]
    jitter = [jitter_rng(80,30) for x in range(K)]

    df_time = pd.DataFrame()
    df_time.loc[:,'time'] = human_reflex + jitter
    df_time.loc[:,'type'] = ['reflex']*len(human_reflex)+['jitter']*len(jitter)

    g = sns.FacetGrid(df_time, col='type')
    g.map(sns.distplot, 'time')
    sns.plt.savefig('time.png')


    # spin simulation
    spin9 = [spin_modifier(.9) for x in range(K)]
    spin5 = [spin_modifier(.5) for x in range(K)]
    spin1 = [spin_modifier(.1) for x in range(K)]

    df_time = pd.DataFrame()
    df_time.loc[:,'value'] = spin9 + spin5 + spin1
    df_time.loc[:,'factor'] = ['0.9']*len(spin9)+['0.5']*len(spin5)+['0.1']*len(spin1)

    g = sns.FacetGrid(df_time, col='factor')
    g.map(sns.distplot, 'value')
    sns.plt.savefig('spin.png')

    # reticle simulation
    reti9 = [normalized_reticle_size(.9) for x in range(K)]
    reti5 = [normalized_reticle_size(.5) for x in range(K)]
    reti1 = [normalized_reticle_size(.1) for x in range(K)]

    df_time = pd.DataFrame()
    df_time.loc[:,'value'] = reti9 + reti5 + reti1
    df_time.loc[:,'factor'] = ['0.9']*len(spin9)+['0.5']*len(spin5)+['0.1']*len(spin1)

    g = sns.FacetGrid(df_time, col='factor')
    g.map(sns.distplot, 'value')
    sns.plt.savefig('reticle.png')


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
    # _precalc_lognormal_ping_param()
    # _visualize()
    pass
"""
