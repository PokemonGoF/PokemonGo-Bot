import requests
import re
import json
import argparse
import pokemon_pb2

from datetime import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


API_URL = 'https://pgorelease.nianticlabs.com/plfe/rpc'
LOGIN_URL = 'https://sso.pokemon.com/sso/login?service=https%3A%2F%2Fsso.pokemon.com%2Fsso%2Foauth2.0%2FcallbackAuthorize'
LOGIN_OAUTH = 'https://sso.pokemon.com/sso/oauth2.0/accessToken'

SESSION = requests.session()
SESSION.headers.update({'User-Agent': 'Niantic App'})
SESSION.verify = False


def get_gps_coords():
    return (0x404aca0660000000, 0x40241f55a0000000, 0x4048000000000000)


def api_req(api_endpoint, access_token, req):
    try:
        p_req = pokemon_pb2.RequestEnvelop()
        p_req.unknown1 = 2
        p_req.rpc_id = 8145806132888207460

        p_req.requests.MergeFrom(req)

        p_req.latitude, p_req.longitude, p_req.altitude = get_gps_coords()

        p_req.unknown12 = 989
        p_req.auth.provider = 'ptc'
        p_req.auth.token.contents = access_token
        p_req.auth.token.unknown13 = 59
        protobuf = p_req.SerializeToString()

        r = SESSION.post(api_endpoint, data=protobuf, verify=False)

        p_ret = pokemon_pb2.ResponseEnvelop()
        p_ret.ParseFromString(r.content)
        return p_ret
    except:
        return None


def get_api_endpoint(access_token):
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

    p_ret = api_req(API_URL, access_token, req.requests)

    try:
        return ('https://%s/rpc' % p_ret.API_URL)
    except:
        return None


def get_profile(api_endpoint, access_token):
    req = pokemon_pb2.RequestEnvelop()

    req1 = req.requests.add()
    req1.type = 2

    return api_req(api_endpoint, access_token, req.requests)


def login_ptc(username, password):
    print('[!] login for: {}'.format(username))
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
    except:
        return False

    data1 = {
        'client_id': 'mobile-app_pokemon-go',
        'redirect_uri': 'https://www.nianticlabs.com/pokemongo/error',
        'client_secret': 'w8ScCUXJQc6kXKw8FiOhd8Fixzht18Dq3PEVkUCP5ZPxtgyWsbTvWHFLm2wNY0JR',
        'grant_type': 'refresh_token',
        'code': ticket,
    }
    r2 = SESSION.post(LOGIN_OAUTH, data=data1)
    access_token = re.sub('&expires.*', '', r2.content)
    access_token = re.sub('.*access_token=', '', access_token)

    return access_token


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="PTC Username", required=True)
    parser.add_argument("-p", "--password", help="PTC Password", required=True)
    args = parser.parse_args()

    access_token = login_ptc(args.username, args.password)
    if access_token is None:
        print('[-] Wrong username/password')
        return
    print('[+] RPC Session Token: {} ...'.format(access_token[:25]))

    api_endpoint = get_api_endpoint(access_token)
    if api_endpoint is None:
        print('[-] RPC server offline')
        return
    print('[+] Received API endpoint: {}'.format(api_endpoint))

    profile = get_profile(api_endpoint, access_token)
    if profile is not None:
        print('[+] Login successful')

        profile = profile.payload[0].profile
        print('[+] Username: {}'.format(profile.username))

        creation_time = datetime.fromtimestamp(int(profile.creation_time)/1000)
        print('[+] You are playing Pokemon Go since: {}'.format(
            creation_time.strftime('%Y-%m-%d %H:%M:%S'),
        ))

        for curr in profile.currency:
            print('[+] {}: {}'.format(curr.type, curr.amount))
    else:
        print('[-] Ooops...')


if __name__ == '__main__':
    main()
