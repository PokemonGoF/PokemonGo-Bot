

import googlemaps
import json
import threading
import time
from pgoapi import PGoApi
from pgoapi.utilities import f2i, h2f
from math import radians, sqrt, sin, cos, atan2

GOOGLEMAPS_KEY = "AIzaSyAZzeHhs-8JZ7i18MjFuM35dJHq70n3Hx4"

working_thread=None
gmaps = googlemaps.Client(key=GOOGLEMAPS_KEY)
rest_time=1
pokemon_list=json.load(open('pokemon.json'))
item_list=json.load(open('items.json'))

def work_on_cell(cell,api,position,config):
	#print cell
	if 'catchable_pokemons' in cell:
		print 'Something rustles nearby!'
		for pokemon in cell['catchable_pokemons']:
			#print('catchable_pokemon {}'.format(pokemon))
			encount_and_catch_pokemon(pokemon,api,position,config)
	if 'wild_pokemons' in cell:
		for pokemon in cell['wild_pokemons']:
			#print('wild_pokemons {}'.format(pokemon))
			encount_and_catch_pokemon(pokemon,api,position,config)
			#encounter_id=pokemon['encounter_id']
			#api.encounter(encounter_id=encounter_id,player_latitude=position[0],player_longitude=position[1])
			#response_dict = api.call()
			#print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
			"""
	if 'spawn_points' in cell:
		for spawn_point in cell['spawn_points']:
			print spawn_point
			working.spawn_point_work(spawn_point,api,position)

			api.get_map_objects(latitude=f2i(position[0]), longitude=f2i(position[1]), since_timestamp_ms=timestamp, cell_id=cellid)

			response_dict = api.call()
			print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
			time.sleep(2)
			"""

	if config.spinstop:
		if 'forts' in cell:
			for fort in cell['forts']:
				if 'type' in fort:
					#print('This is PokeStop')
					hack_chain=search_seen_fort(fort,api,position,config)
					if hack_chain > 10:
						print('need a rest')
						break
				#else:
					#print('This is Gym')

def spawn_point_work(spawn_point,api,position):
	lat=spawn_point['latitude']
	lng=spawn_point['longitude']
	position=(lat,lng,0.0)
	api.set_position(*position)
	api.player_update(latitude=lat,longitude=lng)
	response_dict = api.call()
	print('Response dictionary 1: \n\r{}'.format(json.dumps(response_dict, indent=2)))
	time.sleep(2)
	api.player_update(latitude=lat,longitude=lng)
	response_dict = api.call()
	print('Response dictionary 1: \n\r{}'.format(json.dumps(response_dict, indent=2)))
	time.sleep(2)
def convert_toposition(lat,lng,art):
    return (lat, lng, art)
def encount_and_catch_pokemon(pokemon,api,position,config):
	encounter_id=pokemon['encounter_id']
	spawnpoint_id = pokemon['spawnpoint_id']
	player_latitude = pokemon['latitude']
	player_longitude = pokemon['longitude']
	api.encounter(encounter_id=encounter_id,spawnpoint_id=spawnpoint_id,player_latitude=player_latitude,player_longitude=player_longitude)
	response_dict = api.call()
	#print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
	if response_dict and 'responses' in response_dict:
		if 'ENCOUNTER' in response_dict['responses']:
			if 'status' in response_dict['responses']['ENCOUNTER']:
				if response_dict['responses']['ENCOUNTER']['status'] is 1:
					cp=0
					if 'wild_pokemon' in response_dict['responses']['ENCOUNTER']:
						pokemon=response_dict['responses']['ENCOUNTER']['wild_pokemon']
						if 'pokemon_data' in pokemon and 'cp' in pokemon['pokemon_data']:
							cp=pokemon['pokemon_data']['cp']
							pokemon_num=int(pokemon['pokemon_data']['pokemon_id'])-1
							pokemon_name=pokemon_list[int(pokemon_num)]['Name']
							print('A Wild ' + str(pokemon_name) + ' appeared! [CP ' + str(cp) + ']')
					while(True):
						api.catch_pokemon(encounter_id = encounter_id,
							pokeball = 1,
							normalized_reticle_size = 1.950,
							spawn_point_guid = spawnpoint_id,
							hit_pokemon = 1,
							spin_modifier = 1,
							NormalizedHitPosition = 1)
						response_dict = api.call()
						#print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))

						if response_dict and \
							'responses' in response_dict and \
							'CATCH_POKEMON' in response_dict['responses'] and \
							'status' in response_dict['responses']['CATCH_POKEMON']:
							status = response_dict['responses']['CATCH_POKEMON']['status']
							if status is 2:
								print('[-] Attempted to capture ' + str(pokemon_name) + ' - failed.. trying again!')
								time.sleep(1.25)
								continue
							if status is 1:
								if cp < config.cp:
									print('Captured ' + str(pokemon_name) + '! [CP' + str(cp) + '] - exchanging for candy')
									transfer_low_cp_pokomon(api,config.cp)
								else:
									print('Captured ' + str(pokemon_name) + '! [CP' + str(cp) + ']')
						break
	time.sleep(5)
def _transfer_low_cp_pokemon(api,value,pokemon):
	if 'cp' in pokemon and pokemon['cp'] < value:
		#print('need release this pokemon({}): {}'.format(value,pokemon))
		api.release_pokemon(pokemon_id=pokemon['id'])
		response_dict = api.call()
		#print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
		print('Exchanged successfuly!')
def transfer_low_cp_pokomon_with_dict(api,value,response_dict):
	#print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
	if 'responses' in response_dict:
		if 'GET_INVENTORY' in response_dict['responses']:
			if 'inventory_delta' in response_dict['responses']['GET_INVENTORY']:
				if 'inventory_items' in response_dict['responses']['GET_INVENTORY']['inventory_delta']:
					for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
						#print('item {}'.format(item))
						if 'inventory_item_data' in item:
							if 'pokemon' in item['inventory_item_data']:
								pokemon = item['inventory_item_data']['pokemon']
								_transfer_low_cp_pokemon(api,value,pokemon)
								time.sleep(1.2)
def transfer_low_cp_pokomon(api,value):
	api.get_inventory()
	response_dict = api.call()
	transfer_low_cp_pokomon_with_dict(api,value,response_dict)
def search_seen_fort(fort,api,position,config):
	lat=fort['latitude']
	lng=fort['longitude']
	fortID=fort['id']
	distant=geocalc(position[0],position[1],lat,lng)*1000
	global rest_time
	#if --rest_time > 0:
	#	print('dont keep search the fort before have a way to check items')
	#	return 11
	print('Found fort {} at distance {}m'.format(fortID, distant))
	if distant > 10:
		print('Need to move closer to Pokestop')
		position=convert_toposition(lat, lng, 0.0)
		#print(position,fortID)
        if config.walk > 0:
            api.walk(config.walk, *position)
        else:
        	api.set_position(*position)
		api.player_update(latitude=lat,longitude=lng)
		response_dict = api.call()
		print('Teleported to Pokestop')
		#print('Response dictionary 1: \n\r{}'.format(json.dumps(response_dict, indent=2)))
		time.sleep(1.2)

	api.fort_details(fort_id=fort['id'], latitude=position[0], longitude=position[1])
	response_dict = api.call()
	fort_details = response_dict['responses']['FORT_DETAILS']
	print('Now at Pokestop: ' + fort_details['name'] + ' - Spinning...')
	#print('Response dictionary 2: \n\r{}'.format(json.dumps(response_dict, indent=2)))
	time.sleep(2)
	api.fort_search(fort_id=fort['id'], fort_latitude=lat, fort_longitude=lng, player_latitude=f2i(position[0]), player_longitude=f2i(position[1]))
	response_dict = api.call()
	#print('Response dictionary 3: \n\r{}'.format(json.dumps(response_dict, indent=2)))

	if 'responses' in response_dict and \
		'FORT_SEARCH' in response_dict['responses']:

		spin_details = response_dict['responses']['FORT_SEARCH']
		
		if spin_details['result'] is 1:
			print("- Loot: ")
			print("- " + str(spin_details['experience_awarded']) + " xp")
			for item in spin_details['items_awarded']:
				item_id = str(item['item_id'])
				item_name = item_list[item_id]
				print("- " + str(item['item_count']) + "x " + item_name)


		if spin_details['result'] is 2:
			print("- Pokestop out of range")

		if spin_details['result'] is 3:
			print("- Pokestop on cooldown")

		if spin_details['result'] is 4:
			print("- Inventory is full!")

		if 'chain_hack_sequence_number' in response_dict['responses']['FORT_SEARCH']:
			time.sleep(2)
			return response_dict['responses']['FORT_SEARCH']['chain_hack_sequence_number']
		else:
			print('may search too often, lets have a rest')
			rest_time = 50
			return 11
	time.sleep(8)
	return 0
def geocalc(lat1, lon1, lat2, lon2):
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon1 - lon2

    EARTH_R = 6372.8

    y = sqrt(
        (cos(lat2) * sin(dlon)) ** 2
        + (cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)) ** 2
        )
    x = sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(dlon)
    c = atan2(y, x)
    return EARTH_R * c

def start_working():
    global working_thread

    print('register_background_thread: queueing')
    working_thread = threading.Timer(30, pokemon_working)  # delay, in seconds

    working_thread.daemon = True
    working_thread.name = 'working_thread'
    working_thread.start()
def pokemon_working():
    directions_result = gmaps.directions((49.004, 8.456),
                                         (49.004, 8.469),
                                         mode="walking")
    if directions_result and len(directions_result) > 0:
        """
        print directions_result[0]
        for ka, va in directions_result[0].iteritems():
            print ka+'\n'
            print va
        exit(0)
        """
        steps = directions_result[0]['legs'][0]['steps']
        print len(steps)
        for index, item in enumerate(steps):
            print index,item['start_location'],'-->',item['end_location'],'duration: ',item['duration']['value'],'sec'
#start_working();
