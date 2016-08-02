import time
from datetime import timedelta


class Metrics(object):

    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.dust = {'start': None, 'latest': None}
        self.xp = {'start': None, 'latest': None}
        self.distance = {'start': None, 'latest': None}
        self.encounters = {'start': None, 'latest': None}
        self.throws = {'start': None, 'latest': None}
        self.captures = {'start': None, 'latest': None}
        self.visits = {'start': None, 'latest': None}
        self.unique_mons = {'start': None, 'latest': None}
        self.evolutions = {'start': None, 'latest': None}

        self.releases = 0
        self.highest_cp = {'cp': 0, 'desc': ''}
        self.most_perfect = {'potential': 0, 'desc': ''}

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

    def num_visits(self):
        return self.visits['latest'] - self.visits['start']

    def num_new_mons(self):
        return self.unique_mons['latest'] - self.unique_mons['start']

    def num_evolutions(self):
        return self.evolutions['latest'] - self.evolutions['start']

    def earned_dust(self):
        return self.dust['latest'] - self.dust['start']

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
        request = self.bot.api.create_request()
        request.get_inventory()
        request.get_player()
        response_dict = request.call()
        try:
            self.dust['latest'] = response_dict['responses']['GET_PLAYER']['player_data']['currencies'][1]['amount']
            if self.dust['start'] is None: self.dust['start'] = self.dust['latest']
            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                if 'inventory_item_data' in item:
                    if 'player_stats' in item['inventory_item_data']:
                        playerdata = item['inventory_item_data']['player_stats']

                        self.xp['latest'] = playerdata.get('experience', 0)
                        if self.xp['start'] is None: self.xp['start'] = self.xp['latest']

                        self.visits['latest'] = playerdata.get('poke_stop_visits', 0)
                        if self.visits['start'] is None: self.visits['start'] = self.visits['latest']

                        self.captures['latest'] = playerdata.get('pokemons_captured', 0)
                        if self.captures['start'] is None: self.captures['start'] = self.captures['latest']

                        self.distance['latest'] = playerdata.get('km_walked', 0)
                        if self.distance['start'] is None: self.distance['start'] = self.distance['latest']

                        self.encounters['latest'] = playerdata.get('pokemons_encountered', 0)
                        if self.encounters['start'] is None: self.encounters['start'] = self.encounters['latest']

                        self.throws['latest'] = playerdata.get('pokeballs_thrown', 0)
                        if self.throws['start'] is None: self.throws['start'] = self.throws['latest']

                        self.unique_mons['latest'] = playerdata.get('unique_pokedex_entries', 0)
                        if self.unique_mons['start'] is None: self.unique_mons['start'] = self.unique_mons['latest']

                        self.visits['latest'] = playerdata.get('poke_stop_visits', 0)
                        if self.visits['start'] is None: self.visits['start'] = self.visits['latest']

                        self.evolutions['latest'] = playerdata.get('evolutions', 0)
                        if self.evolutions['start'] is None: self.evolutions['start'] = self.evolutions['latest']
        except KeyError:
            # Nothing we can do if there's no player info.
            return
