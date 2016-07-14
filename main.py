import requests
import base64
import re
import json
import random
import pokemon_pb2

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

api_url='https://pgorelease.nianticlabs.com/plfe/rpc'
login_url='https://sso.pokemon.com/sso/login?service=https%3A%2F%2Fsso.pokemon.com%2Fsso%2Foauth2.0%2FcallbackAuthorize'
login_oauth='https://sso.pokemon.com/sso/oauth2.0/accessToken'

s=requests.session()
s.headers.update({'User-Agent':'Niantic App'})
s.verify=False

def get_api_endpoint(access_token):
        try:
                pok = pokemon_pb2.RequestEnvelop()
		pok.unknown1 = 2
		pok.rpc_id = 8145806132888207460

		req1 = pok.requests.add()
		req1.type = 2
		req2 = pok.requests.add()
		req2.type = 126
		req3 = pok.requests.add()
		req3.type = 4
		req4 = pok.requests.add()
		req4.type = 129
		req5 = pok.requests.add()
		req5.type = 5
		req5.message.unknown4 = "4a2e9bc330dae60e7b74fc85b98868ab4700802e"

		pok.gps_x = 0x404aca0660000000
		pok.gps_y = 0x40241f55a0000000
		pok.gps_z = 0x4048000000000000
		pok.unknown12 = 989
		pok.auth.provider = 'ptc'
		pok.auth.token.contents = access_token
		pok.auth.token.unknown13 = 59
		protobuf = pok.SerializeToString()

                r = s.post(api_url,data=protobuf,verify=False)

                p_ret = pokemon_pb2.ResponseEnvelop()
                p_ret.ParseFromString(r.content)
                return ('https://%s/rpc' % p_ret.api_url)
        except:
                print( '[-] RPC server offline' )
		return False

def get_profile(api_endpoint, access_token):
        try:
                pok = pokemon_pb2.RequestEnvelop()
		pok.unknown1 = 2
		pok.rpc_id = 8145806132888207460

		req1 = pok.requests.add()
		req1.type = 2

		pok.gps_x = 0x404aca0660000000
		pok.gps_y = 0x40241f55a0000000
		pok.gps_z = 0x4048000000000000
		pok.unknown12 = 989
		pok.auth.provider = 'ptc'
		pok.auth.token.contents = access_token
		pok.auth.token.unknown13 = 59
		protobuf = pok.SerializeToString()

                r = s.post(api_endpoint, data=protobuf, verify=False)

                p_ret = pokemon_pb2.ResponseEnvelop()
                p_ret.ParseFromString(r.content)

		return p_ret
        except:
                print( '[-] RPC server offline' )
		return False


def login_pokemon(user,passw):
	print( '[!] login for: %s' % user )
	head={'User-Agent':'niantic'}
	r=s.get(login_url,headers=head)
	jdata=json.loads(r.content)
	data={'lt':jdata['lt'],
		'execution':jdata['execution'],
		'_eventId':'submit',
		'username':user,
		'password':passw}
	r1=s.post(login_url,data=data,headers=head)
	ticket=re.sub('.*ticket=','',r1.history[0].headers['Location'])
	data1={'client_id':'mobile-app_pokemon-go',
			'redirect_uri':'https://www.nianticlabs.com/pokemongo/error',
			'client_secret':'w8ScCUXJQc6kXKw8FiOhd8Fixzht18Dq3PEVkUCP5ZPxtgyWsbTvWHFLm2wNY0JR',
			'grant_type':'refresh_token',
			'code':ticket}
	r2=s.post(login_oauth,data=data1)
	access_token=re.sub('&expires.*','',r2.content)
	access_token=re.sub('.*access_token=','',access_token)
	return access_token
	
def main():
	access_token= login_pokemon('yourusername','yourpass')
	print( '[+] RPC Session Token: %s ...' % access_token[:25] )
	api_endpoint = get_api_endpoint(access_token)
	if api_endpoint is False:
		return
	print( '[+] Received API endpoint: %s' % api_endpoint )

	profile = get_profile(api_endpoint, access_token)
        if profile:
		print( '[+] Login successful' )
		print( '[+] Username: %s' % profile.payload[0].profile.username )
		for curr in profile.payload[0].profile.currency:
			print( '[+] %s: %s' % (curr.type, curr.amount) )
	else:
	    print( '[-] Ooops...' )

	
if __name__ == '__main__':
	main()
