import json

from pokemongo_bot.human_behaviour import sleep, action_delay
from pokemongo_bot import logger

class PokemonTransferWorker(object):

    def __init__(self, bot):
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.api = bot.api
        self.bot = bot

    def work(self):
        if not self.config.release_pokemon:
            return

        pokemon_groups = self._release_pokemon_get_groups()
        for id in pokemon_groups:
            group_cp = pokemon_groups[id].keys()

            if len(group_cp) > 1:
                group_cp.sort()
                group_cp.reverse()

                for x in range(1, len(group_cp)):
                    pokemon_name = self.pokemon_list[id - 1]['Name']
                    pokemon_cp = group_cp[x]
                    pokemon_data = pokemon_groups[id][pokemon_cp]
                    pokemon_potential = self.get_pokemon_potential(pokemon_data)
                    #logger.log('Checking {} [CP {}] [Potential {}] for release!'.format(pokemon_name, pokemon_cp, pokemon_potential))
                    if self.should_release_pokemon(pokemon_name, pokemon_cp, pokemon_potential):
                        logger.log('Exchanging {} for candy!'.format(
                            pokemon_name), 'green')
                        self.release_pokemon(pokemon_data['id'])
                        action_delay(self.config.action_wait_min, self.config.action_wait_max)

    def _release_pokemon_get_groups(self):
        pokemon_groups = {}
        try:
            self.api.get_player().get_inventory()
            inventory_req = self.api.call()
            inventory_dict = inventory_req['responses']['GET_INVENTORY'][
                'inventory_delta']['inventory_items']
        except KeyError:
            return pokemon_groups

        user_web_inventory = 'web/inventory-%s.json' % (self.config.username)
        with open(user_web_inventory, 'w') as outfile:
            json.dump(inventory_dict, outfile)

        for pokemon in inventory_dict:
            try:
                reduce(dict.__getitem__, [
                    "inventory_item_data", "pokemon_data", "pokemon_id"
                ], pokemon)
            except KeyError:
                continue

            pokemon_data = pokemon['inventory_item_data']['pokemon_data']
            group_id = pokemon_data['pokemon_id']
            group_pokemon_cp = pokemon_data['cp']

            if group_id not in pokemon_groups:
                pokemon_groups[group_id] = {}

            pokemon_groups[group_id].update({group_pokemon_cp: pokemon_data})
        return pokemon_groups

    def get_pokemon_potential(self, pokemon_data):
        total_iv = 0
        iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']
        for individual_stat in iv_stats:
            try:
                total_iv += pokemon_data[individual_stat]
            except Exception:
                continue
        return round((total_iv / 45.0), 2)

    def should_release_pokemon(self, pokemon_name, cp, iv):
        release_config = self._get_release_config_for(pokemon_name)
        cp_iv_logic = release_config.get('logic')
        if not cp_iv_logic:
            cp_iv_logic = self._get_release_config_for('any').get('logic', 'and')

        release_results = {
            'cp': False,
            'iv': False,
        }

        if release_config.get('never_release', False):
            return False

        if release_config.get('always_release', False):
            return True

        release_cp = release_config.get('release_below_cp', 0)
        if cp < release_cp:
            release_results['cp'] = True

        release_iv = release_config.get('release_below_iv', 0)
        if iv < release_iv:
            release_results['iv'] = True

        logic_to_function = {
            'or': lambda x, y: x or y,
            'and': lambda x, y: x and y
        }

        if logic_to_function[cp_iv_logic](*release_results.values()):
            logger.log(
                "Release config for {}: Conf, CP {} {} IV {} - Poke, CP {} IV {}".format(
                    pokemon_name,
                    release_cp,
                    cp_iv_logic,
                    release_iv,
                    cp,
                    iv
                ), 'yellow'
            )

        return logic_to_function[cp_iv_logic](*release_results.values())

    def check_stronger_pokemon(self, pokemon_name, pokemon_data, max_criteria_pokemon_list):
        if not self.config.release_pokemon:
            return

        release_config = self._get_release_config_for(pokemon_name)
        if release_config.get('keep_best_cp', False) or release_config.get('keep_best_iv', False):
            if release_config.get('keep_best_cp', False) and release_config.get('keep_best_iv', False):
                logger.log("keep_best_cp and keep_best_iv can't be set true at the same time. Ignore this settings",
                           "red")
            else:
                pokemon_id = pokemon_data['pokemon_id']
                display_pokemon = '{} [CP {}] [Potential {}]'.format(pokemon_name,
                                                                     pokemon_data['cp'],
                                                                     self.pokemon_potential(pokemon_data))
                if pokemon_id in max_criteria_pokemon_list:
                    owned = max_criteria_pokemon_list[pokemon_id]
                    owned_display = '{} [CP {}] [Potential {}]'.format(pokemon_name,
                                                                       owned['cp'],
                                                                       self.pokemon_potential(owned))

                    better = self.is_greater_by_criteria(pokemon_data, owned)
                    if better:
                        logger.log('Owning weaker {}. Replacing it with {}!'.format(owned_display, display_pokemon), 'blue')
                        action_delay(self.config.action_wait_min, self.config.action_wait_max)
                        self.release_pokemon(pokemon_data['pokemon_id'])
                        logger.log('Weaker {} has been exchanged for candy!'.format(owned_display), 'blue')
                        return False
                    else:
                        logger.log('Owning better {} already!'.format(owned_display), 'blue')
                        return True
                else:
                    logger.log('Not owning {}. Keeping it!'.format(display_pokemon), 'blue')
                    return False

    def is_greater_by_criteria(self, pokemon, other_pokemon):
        pokemon_num = int(pokemon['pokemon_id']) - 1
        pokemon_name = self.pokemon_list[int(pokemon_num)]['Name']

        release_config = self._get_release_config_for(pokemon_name)
        if release_config.get('keep_best_cp', False):
            return pokemon['cp'] > other_pokemon['cp']
        elif release_config.get('keep_best_iv', False):
            return self.pokemon_potential(pokemon) > self.pokemon_potential(other_pokemon)
        else:
            return False

    def pokemon_potential(self, pokemon_data):
        total_iv = 0
        iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']

        for individual_stat in iv_stats:
            try:
                total_iv += pokemon_data[individual_stat]
            except:
                pokemon_data[individual_stat] = 0
                continue

        return round((total_iv / 45.0), 2)

    def release_pokemon(self, pokemon_id):
        self.api.release_pokemon(pokemon_id=pokemon_id)
        response_dict = self.api.call()

    def _get_release_config_for(self, pokemon):
        release_config = self.config.release.get(pokemon)
        if not release_config:
            release_config = self.config.release.get('any')
        if not release_config:
            release_config = {}
        return release_config
