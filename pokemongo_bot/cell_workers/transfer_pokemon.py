import json

from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.cell_workers.base_task import BaseTask
from pokemongo_bot.cell_workers.utils import get_candies


class TransferPokemon(BaseTask):
    def work(self):
        pokemon_groups = self._release_pokemon_get_groups()
        candies = get_candies(self.bot)
        evolvable = 0
        for pokemon_id in pokemon_groups:
            group = pokemon_groups[pokemon_id]

            if len(group) > 0:
                pokemon_name = self.bot.pokemon_list[pokemon_id - 1]['Name']
                keep_best, keep_best_cp, keep_best_iv, keep_for_evo = self._validate_keep_best_config(pokemon_name)

                if keep_best:
                    best_pokemon_ids = set()
                    order_criteria = 'none'
                    if keep_best_cp >= 1:
                        cp_limit = keep_best_cp
                        best_cp_pokemons = sorted(group, key=lambda x: (x['cp'], x['iv']), reverse=True)[:cp_limit]
                        best_pokemon_ids = set(pokemon['pokemon_data']['id'] for pokemon in best_cp_pokemons)
                        order_criteria = 'cp'

                    if keep_best_iv >= 1:
                        iv_limit = keep_best_iv
                        best_iv_pokemons = sorted(group, key=lambda x: (x['iv'], x['cp']), reverse=True)[:iv_limit]
                        best_pokemon_ids |= set(pokemon['pokemon_data']['id'] for pokemon in best_iv_pokemons)
                        if order_criteria == 'cp':
                            order_criteria = 'cp and iv'
                        else:
                            order_criteria = 'iv'

                    # remove best pokemons from all pokemons array
                    best_pokemon = []
                    for best_pokemon_id in best_pokemon_ids:
                        for pokemon in group:
                            if best_pokemon_id == pokemon['pokemon_data']['id']:
                                group.remove(pokemon)
                                best_pokemon.append(pokemon)

                    if len(best_pokemon) > 0:
                        logger.log("Keep {} best {}, based on {}".format(len(best_pokemon),
                                                                         pokemon_name,
                                                                         order_criteria), "green")
                        for best_pokemon in best_pokemon:
                            logger.log("{} [CP {}] [Potential {}]".format(pokemon_name,
                                                                          best_pokemon['cp'],
                                                                          best_pokemon['iv']), 'green')

                high_pokemon = []
                for pokemon in group:
                    if self.should_release_pokemon(pokemon_name, pokemon['cp'], pokemon['iv']):
                        group.remove(pokemon)
                        high_pokemon.append(pokemon)
                if len(high_pokemon) > 0:
                    logger.log("Keep {} {}, based on cp/iv criteria".format(len(high_pokemon),
                                                                            pokemon_name), "green")
                    for high_pokemon in high_pokemon:
                        logger.log("{} [CP {}] [Potential {}]".format(pokemon_name,
                                                                      high_pokemon['cp'],
                                                                      high_pokemon['iv']), 'green')

                if keep_for_evo and len(group) > 0:
                    if 'Previous evolution(s)' in self.bot.pokemon_list[pokemon_id - 1]:
                        logger.log(
                            '{} has previous evolution stages. This focuses on 1st stage because they use less '
                            'candy'.format(pokemon_name), 'red')
                        continue

                    if candies == {}:
                        logger.log("Api call for candies failed, try again")
                        return
                    candy = candies[pokemon_id]
                    if 'Next Evolution Requirements' in self.bot.pokemon_list[pokemon_id - 1]:
                        req_candy = self.bot.pokemon_list[pokemon_id - 1]['Next Evolution Requirements']['Amount']
                        num_keep = (len(group) + candy) / (req_candy + 1)

                        if len(group) > num_keep:
                            group.sort(key=lambda x: x['iv'], reverse=True)
                            evo_pokemon = group[:num_keep]
                            group = group[num_keep:]
                        else:
                            evo_pokemon = group
                            group = []

                        evolvable += len(evo_pokemon)
                        if len(evo_pokemon) > 0:
                            logger.log("Keep {} {}, for evolution - {} candies".format(len(evo_pokemon),
                                                                                       pokemon_name, candy), "green")
                            for evo_pokemon in evo_pokemon:
                                logger.log("{} [CP {}] [Potential {}]".format(pokemon_name,
                                                                              evo_pokemon['cp'],
                                                                              evo_pokemon['iv']), 'green')

                logger.log("Transferring {} {}".format(len(group), pokemon_name), "green")

                for pokemon in group:
                    self.release_pokemon(pokemon_name, pokemon['cp'], pokemon['iv'], pokemon['pokemon_data']['id'])

        logger.log("{} pokemon transferred total. {} evolutions ready (based on pokemons additional to the ones kept"
                   " with cp/iv criteria)".format(len(group), evolvable), "green")

    def _release_pokemon_get_groups(self):
        pokemon_groups = {}
        self.bot.api.get_player().get_inventory()
        inventory_req = self.bot.api.call()

        if inventory_req.get('responses', False) is False:
            return pokemon_groups

        inventory_dict = inventory_req['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

        user_web_inventory = 'web/inventory-%s.json' % (self.bot.config.username)
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

            # pokemon in fort, so we cant transfer it
            if 'deployed_fort_id' in pokemon_data and pokemon_data['deployed_fort_id']:
                continue

            # favorite pokemon can't transfer in official game client
            if pokemon_data.get('favorite', 0) is 1:
                continue

            group_id = pokemon_data['pokemon_id']
            group_pokemon_cp = pokemon_data['cp']
            group_pokemon_iv = self.get_pokemon_potential(pokemon_data)

            if group_id not in pokemon_groups:
                pokemon_groups[group_id] = []

            pokemon_groups[group_id].append({
                'cp': group_pokemon_cp,
                'iv': group_pokemon_iv,
                'pokemon_data': pokemon_data
            })

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

        release_strings = ['never_release', 'always_release', 'release_below_cp', 'release_below_iv']
        keep_strings = ['keep_best_cp', 'keep_best_iv']
        if not any(x in release_config for x in release_strings):
            if any(x in release_config for x in keep_strings):
                return True
            else:
                return False

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
                "Releasing {} with CP {} and IV {}. Matching release rule: CP < {} {} IV < {}. ".format(
                    pokemon_name,
                    cp,
                    iv,
                    release_cp,
                    cp_iv_logic.upper(),
                    release_iv
                ), 'yellow'
            )

        return logic_to_function[cp_iv_logic](*release_results.values())

    def release_pokemon(self, pokemon_name, cp, iv, pokemon_id):
        logger.log('Exchanging {} [CP {}] [Potential {}] for candy!'.format(pokemon_name,
                                                                            cp,
                                                                            iv), 'green')
        self.bot.api.release_pokemon(pokemon_id=pokemon_id)
        response_dict = self.bot.api.call()
        action_delay(self.bot.config.action_wait_min, self.bot.config.action_wait_max)

    def _get_release_config_for(self, pokemon):
        release_config = self.bot.config.release.get(pokemon)
        if not release_config:
            release_config = self.bot.config.release.get('any')
        if not release_config:
            release_config = {}
        return release_config

    def _validate_keep_best_config(self, pokemon_name):
        keep_best = False

        release_config = self._get_release_config_for(pokemon_name)

        keep_best_cp = release_config.get('keep_best_cp', 0)
        keep_best_iv = release_config.get('keep_best_iv', 0)
        keep_for_evo = release_config.get('keep_for_evo', False)

        if keep_best_cp or keep_best_iv:
            keep_best = True
            try:
                keep_best_cp = int(keep_best_cp)
            except ValueError:
                keep_best_cp = 0

            try:
                keep_best_iv = int(keep_best_iv)
            except ValueError:
                keep_best_iv = 0

            if keep_best_cp < 0 or keep_best_iv < 0:
                logger.log("Keep best can't be < 0. Ignore it.", "red")
                keep_best = False

            if keep_best_cp == 0 and keep_best_iv == 0:
                keep_best = False

        return keep_best, keep_best_cp, keep_best_iv, keep_for_evo
