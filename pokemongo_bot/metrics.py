import time
from datetime import timedelta
from pokemongo_bot.inventory import Pokemons

class Metrics(object):

    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.dust = {'start': -1, 'latest': -1}
        self.xp = {'start': -1, 'latest': -1}
        self.distance = {'start': -1, 'latest': -1}
        self.encounters = {'start': -1, 'latest': -1}
        self.throws = {'start': -1, 'latest': -1}
        self.captures = {'start': -1, 'latest': -1}
        self.visits = {'start': -1, 'latest': -1}
        self.unique_mons = {'start': -1, 'latest': -1}
        self.evolutions = {'start': -1, 'latest': -1}

        self.releases = 0
        self.highest_cp = {'cp': 0, 'desc': ''}
        self.most_perfect = {'potential': 0, 'desc': ''}
        self.eggs = {'hatched': 0, 'next_hatching_km': 0}

        self.uniq_pokemons_caught = None
        self.uniq_pokemons_list = None

    def runtime(self):
        return timedelta(seconds=round(time.time() - self.start_time))

    def xp_earned(self):
        return self.xp['latest'] - self.xp['start']

    def xp_per_hour(self):
        return self.xp_earned()/(time.time() - self.start_time)*3600

    def distance_travelled(self):
        return self.distance['latest'] - self.distance['start']

    def num_encounters(self):
        return self.encounters['latest'] - self.encounters['start']

    def num_throws(self):
        return self.throws['latest'] - self.throws['start']

    def num_captures(self):
        return self.captures['latest'] - self.captures['start']

    def uniq_caught(self):
        # generate pokemon string 'Snorlax, Pikachu' from list of ids
        return ', '.join([Pokemons.name_for(pok_id) for pok_id in self.uniq_pokemons_caught]) if self.uniq_pokemons_caught else ''

    def captures_per_hour(self):
        """
        Returns an estimated number of pokemon caught per hour.
        :return: An estimated number of pokemon caught per hour.
        :rtype: float
        """
        return self.num_captures() / (time.time() - self.start_time) * 3600

    def num_visits(self):
        return self.visits['latest'] - self.visits['start']

    def num_new_mons(self):
        return self.unique_mons['latest'] - self.unique_mons['start']

    def num_evolutions(self):
        return self.evolutions['latest'] - self.evolutions['start']

    def earned_dust(self):
        return self.dust['latest'] - self.dust['start']

    def hatched_eggs(self, update):
        if (update):
            self.eggs['hatched'] += update
        return self.eggs['hatched']

    def next_hatching_km(self, update):
        if (update):
            self.eggs['next_hatching_km'] = update
        return self.eggs['next_hatching_km']

    def captured_pokemon(self, name, cp, iv_display, potential):
        if cp > self.highest_cp['cp']:
            self.highest_cp = \
                {'cp': cp, 'desc': '{} [CP: {}] [IV: {}] Potential: {} '
                    .format(name, cp, iv_display, potential)}

        if potential > self.most_perfect['potential']:
            self.most_perfect = \
                {'potential': potential, 'desc': '{} [CP: {}] [IV: {}] Potential: {} '
                    .format(name, cp, iv_display, potential)}
        return

    def released_pokemon(self, count=1):
        self.releases += count

    def capture_stats(self):
        try:
            request = self.bot.api.create_request()
        except AttributeError:
            return

        request.get_inventory()
        request.get_player()
        response_dict = request.call()
        try:
            uniq_pokemon_list = set()

            self.dust['latest'] = response_dict['responses']['GET_PLAYER']['player_data']['currencies'][1]['amount']
            if self.dust['start'] < 0: self.dust['start'] = self.dust['latest']

            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                if 'inventory_item_data' in item:
                    if 'player_stats' in item['inventory_item_data']:
                        playerdata = item['inventory_item_data']['player_stats']

                        self.xp['latest'] = playerdata.get('experience', 0)
                        if self.xp['start'] < 0: self.xp['start'] = self.xp['latest']

                        self.visits['latest'] = playerdata.get('poke_stop_visits', 0)
                        if self.visits['start'] < 0: self.visits['start'] = self.visits['latest']

                        self.captures['latest'] = playerdata.get('pokemons_captured', 0)
                        if self.captures['start'] < 0: self.captures['start'] = self.captures['latest']

                        self.distance['latest'] = playerdata.get('km_walked', 0)
                        if self.distance['start'] < 0: self.distance['start'] = self.distance['latest']

                        self.encounters['latest'] = playerdata.get('pokemons_encountered', 0)
                        if self.encounters['start'] < 0: self.encounters['start'] = self.encounters['latest']

                        self.throws['latest'] = playerdata.get('pokeballs_thrown', 0)
                        if self.throws['start'] < 0: self.throws['start'] = self.throws['latest']

                        self.unique_mons['latest'] = playerdata.get('unique_pokedex_entries', 0)
                        if self.unique_mons['start'] < 0: self.unique_mons['start'] = self.unique_mons['latest']

                        self.visits['latest'] = playerdata.get('poke_stop_visits', 0)
                        if self.visits['start'] < 0: self.visits['start'] = self.visits['latest']

                        self.evolutions['latest'] = playerdata.get('evolutions', 0)
                        if self.evolutions['start'] < 0: self.evolutions['start'] = self.evolutions['latest']
                    elif 'pokedex_entry' in item['inventory_item_data']:
                        entry = item['inventory_item_data']['pokedex_entry'].get('pokemon_id')
                        if entry: uniq_pokemon_list.add(entry)

            if not self.uniq_pokemons_list:  # make set from pokedex entries on first run
                self.uniq_pokemons_list = uniq_pokemon_list
            else:
                # generate new entries for current bot session
                self.uniq_pokemons_caught = uniq_pokemon_list - self.uniq_pokemons_list

        except KeyError:
            # Nothing we can do if there's no player info.
            return
