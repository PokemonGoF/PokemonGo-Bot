#!/usr/bin/env python
import requests
import re
import struct
import json
import argparse
import os
import pokemon_pb2

from gpsoauth import perform_master_login, perform_oauth
from datetime import datetime
from geopy.geocoders import GoogleV3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

API_URL = 'https://pgorelease.nianticlabs.com/plfe/rpc'
LOGIN_URL = 'https://sso.pokemon.com/sso/login?service=https%3A%2F%2Fsso.pokemon.com%2Fsso%2Foauth2.0%2FcallbackAuthorize'
LOGIN_OAUTH = 'https://sso.pokemon.com/sso/oauth2.0/accessToken'
PTC_CLIENT_SECRET = 'w8ScCUXJQc6kXKw8FiOhd8Fixzht18Dq3PEVkUCP5ZPxtgyWsbTvWHFLm2wNY0JR'
CONFIG = "config.json"

SESSION = requests.session()
SESSION.headers.update({'User-Agent': 'Niantic App'})
SESSION.verify = False

DEBUG = True
COORDS_LATITUDE = 0
COORDS_LONGITUDE = 0
COORDS_ALTITUDE = 0

ANDROID_ID = '9774d56d682e549c'
SERVICE= 'audience:server:client_id:848232511240-7so421jotr2609rmqakceuu1luuq0ptb.apps.googleusercontent.com'
APP = 'com.nianticlabs.pokemongo'
CLIENT_SIG = '321187995bc7cdc2b5fc91b11a96e2baa8602c62'

def f2i(float):
  return struct.unpack('<Q', struct.pack('<d', float))[0]

def f2h(float):
  return hex(struct.unpack('<Q', struct.pack('<d', float))[0])

def h2f(hex):
  return struct.unpack('<d', struct.pack('<Q', int(hex,16)))[0]

def set_location(location_name):
    geolocator = GoogleV3()
    loc = geolocator.geocode(location_name)

    print('[!] Your given location: {}'.format(loc.address.encode('utf-8')))
    print('[!] lat/long/alt: {} {} {}'.format(loc.latitude, loc.longitude, loc.altitude))
    set_location_coords(loc.latitude, loc.longitude, loc.altitude)

def set_location_coords(lat, long, alt):
    global COORDS_LATITUDE, COORDS_LONGITUDE, COORDS_ALTITUDE
    COORDS_LATITUDE = f2i(lat)
    COORDS_LONGITUDE = f2i(long)
    COORDS_ALTITUDE = f2i(alt)

def get_location_coords():
    return (COORDS_LATITUDE, COORDS_LONGITUDE, COORDS_ALTITUDE)

def api_req(service, api_endpoint, access_token, req):
    try:
        p_req = pokemon_pb2.RequestEnvelop()
        p_req.unknown1 = 2
        p_req.rpc_id = 8145806132888207460

        p_req.requests.MergeFrom(req)

        p_req.latitude, p_req.longitude, p_req.altitude = get_location_coords()

        p_req.unknown12 = 989
        p_req.auth.provider = service
        p_req.auth.token.contents = access_token
        p_req.auth.token.unknown13 = 59
        protobuf = p_req.SerializeToString()

        r = SESSION.post(api_endpoint, data=protobuf, verify=False)

        p_ret = pokemon_pb2.ResponseEnvelop()
        p_ret.ParseFromString(r.content)
        return p_ret
    except Exception,e:
        if DEBUG:
            print(e)
        return None


def get_api_endpoint(service, access_token):
    req = pokemon_pb2.RequestEnvelop()

    req1 = req.requests.add()
    req1.type = 2
    req2 = req.requests.add()
    req2.type = 126
    req3 = req.requests.add()
    req3.type = 4
    req4 = req.requests.add()
    req4.type = 129
    req5 = req.requests.add()
    req5.type = 5
    req5.message.unknown4 = "4a2e9bc330dae60e7b74fc85b98868ab4700802e"

    p_ret = api_req(service, API_URL, access_token, req.requests)

    try:
        return ('https://%s/rpc' % p_ret.api_url)
    except:
        return None


def get_profile(service, api_endpoint, access_token):
    req = pokemon_pb2.RequestEnvelop()

    req1 = req.requests.add()
    req1.type = 2

    return api_req(service, api_endpoint, access_token, req.requests)


def login_google(username, password):
    print('[!] Google login for: {}'.format(username))
    r1 = perform_master_login(username, password, ANDROID_ID)
    r2 = perform_oauth(username, r1.get('Token', ''), ANDROID_ID, SERVICE, APP,
        CLIENT_SIG)

    return r2.get('Auth') # access token

def login_ptc(username, password):
    print('[!] PTC login for: {}'.format(username))
    head = {'User-Agent': 'niantic'}
    r = SESSION.get(LOGIN_URL, headers=head)
    jdata = json.loads(r.content)
    data = {
        'lt': jdata['lt'],
        'execution': jdata['execution'],
        '_eventId': 'submit',
        'username': username,
        'password': password,
    }
    r1 = SESSION.post(LOGIN_URL, data=data, headers=head)

    ticket = None
    try:
        ticket = re.sub('.*ticket=', '', r1.history[0].headers['Location'])
    except Exception,e:
        if DEBUG:
            print(r1.json()['errors'][0])
        return None

    data1 = {
        'client_id': 'mobile-app_pokemon-go',
        'redirect_uri': 'https://www.nianticlabs.com/pokemongo/error',
        'client_secret': PTC_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'code': ticket,
    }
    r2 = SESSION.post(LOGIN_OAUTH, data=data1)
    access_token = re.sub('&expires.*', '', r2.content)
    access_token = re.sub('.*access_token=', '', access_token)

    return access_token


def main():
    parser = argparse.ArgumentParser()

    # If config file exists, load variables from json
    load   = {}
    if os.path.isfile(CONFIG):
        with open(CONFIG) as data:
            load.update(json.load(data))

    # Read passed in Arguments
    required = lambda x: not x in load
    parser.add_argument("-a", "--auth_service", help="Auth Service",
        required=required("auth_service"))
    parser.add_argument("-u", "--username", help="Username", required=required("username"))
    parser.add_argument("-p", "--password", help="Password", required=required("password"))
    parser.add_argument("-l", "--location", help="Location", required=required("location"))
    parser.add_argument("-d", "--debug", help="Debug Mode", action='store_true')
    parser.add_argument("-s", "--client_secret", help="PTC Client Secret")
    parser.set_defaults(DEBUG=True)
    args = parser.parse_args()

    # Passed in arguments shoud trump
    for key in args.__dict__:
        if key in load and args.__dict__[key] == None:
            args.__dict__[key] = load[key]
    # Or
    # args.__dict__.update({key:load[key] for key in load if args.__dict__[key] == None and key in load})

    if args.auth_service not in ['ptc', 'google']:
      print('[!] Invalid Auth service specified')
      return

    if args.debug:
        global DEBUG
        DEBUG = True
        print('[!] DEBUG mode on')

    if args.client_secret is not None:
        global PTC_CLIENT_SECRET
        PTC_CLIENT_SECRET = args.client_secret

    set_location(args.location)

    if args.auth_service == 'ptc':
        access_token = login_ptc(args.username, args.password)
    else:
        access_token = login_google(args.username, args.password)

    if access_token is None:
        print('[-] Wrong username/password')
        return
    print('[+] RPC Session Token: {} ...'.format(access_token[:25]))

    api_endpoint = get_api_endpoint(args.auth_service, access_token)
    if api_endpoint is None:
        print('[-] RPC server offline')
        return
    print('[+] Received API endpoint: {}'.format(api_endpoint))

    profile = get_profile(args.auth_service, api_endpoint, access_token)
    if profile is not None:
        print('[+] Login successful')

        profile = profile.payload[0].profile
        print('[+] Username: {}'.format(profile.username))

        creation_time = datetime.fromtimestamp(int(profile.creation_time)/1000)
        print('[+] You are playing Pokemon Go since: {}'.format(
            creation_time.strftime('%Y-%m-%d %H:%M:%S'),
        ))

        print('[+] Poke Storage: {}'.format(profile.poke_storage))

        print('[+] Item Storage: {}'.format(profile.item_storage))

        for curr in profile.currency:
            print('[+] {}: {}'.format(curr.type, curr.amount))
    else:
        print('[-] Ooops...')


if __name__ == '__main__':
    main()
