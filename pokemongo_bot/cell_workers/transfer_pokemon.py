import json
import os

from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.base_task import BaseTask


class TransferPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def work(self):
        pokemon_groups = self._release_pokemon_get_groups()
        for pokemon_id in pokemon_groups:
            group = pokemon_groups[pokemon_id]

            if len(group) > 0:
                pokemon_name = self.bot.pokemon_list[pokemon_id - 1]['Name']
                keep_best, keep_best_cp, keep_best_iv = self._validate_keep_best_config(pokemon_name)

                if keep_best:
                    release_config = self._get_release_config_for(pokemon_name)

                    order_criteria = 'none'

                    release_not_move_1 = release_config.get("release_not_move_1", 0)
                    release_not_move_2 = release_config_get("release_not_move_2", 0)
                    keep_best_group = []
                    if release_not_move_1 != 0 and release_not_move_2 != 0:
                        for pokemon in group:
                            if pokemon['pokemon_data']['move_2'] == release_not_move_1 and pokemon['pokemon_data']['move_2'] == release_not_move_2:
                                keep_best_group.append(pokemon)
                                order_criteria = 'moves'
                    else:
                        keep_best_group = group

                    best_pokemon_ids = set()

                    if keep_best_cp >= 1:
                        cp_limit = keep_best_cp
                        best_cp_pokemons = sorted(keep_best_group, key=lambda x: (x['cp'], x['iv']), reverse=True)[:cp_limit]
                        best_pokemon_ids = set(pokemon['pokemon_data']['id'] for pokemon in best_cp_pokemons)
                        if order_criteria == 'moves':
                            order_criteria = 'moves and cp'
                        else:
                            order_criteria = 'cp'

                    if keep_best_iv >= 1:
                        iv_limit = keep_best_iv
                        best_iv_pokemons = sorted(keep_best_group, key=lambda x: (x['iv'], x['cp']), reverse=True)[:iv_limit]
                        best_pokemon_ids |= set(pokemon['pokemon_data']['id'] for pokemon in best_iv_pokemons)
                        if order_criteria == 'cp':
                            order_criteria = 'cp and iv'
                        elif order_criteria == 'moves':
                            order_criteria = 'moves and iv'
                        elif order_criteria == 'moves and cp':
                            order_criteria = 'moves, cp and iv'
                        else:
                            order_criteria = 'iv'

                    # remove best pokemons from all pokemons array
                    all_pokemons = group
                    best_pokemons = []
                    for best_pokemon_id in best_pokemon_ids:
                        for pokemon in all_pokemons:
                            if best_pokemon_id == pokemon['pokemon_data']['id']:
                                all_pokemons.remove(pokemon)
                                best_pokemons.append(pokemon)

                    transfer_pokemons = [pokemon for pokemon in all_pokemons
                                         if self.should_release_pokemon(pokemon_name,
                                                                        pokemon['cp'],
                                                                        pokemon['iv'],
                                                                        pokemon['move_1'],
                                                                        pokemon['move_2'],
                                                                        True)]

                    if transfer_pokemons:
                        if best_pokemons:
                            self.emit_event(
                                'keep_best_release',
                                formatted="Keeping best {amount} {pokemon}, based on {criteria}",
                                data={
                                    'amount': len(best_pokemons),
                                    'pokemon': pokemon_name,
                                    'criteria': order_criteria
                                }
                            )
                        for pokemon in transfer_pokemons:
                            self.release_pokemon(pokemon_name, pokemon['cp'], pokemon['iv'], pokemon['move_1'], pokemon['move_2'], pokemon['pokemon_data']['id'])
                else:
                    group = sorted(group, key=lambda x: x['cp'], reverse=True)
                    for item in group:
                        pokemon_cp = item['cp']
                        pokemon_potential = item['iv']
                        pokemon_move_1 = item['move_1']
                        pokemon_move_2 = item['move_2']

                        if self.should_release_pokemon(pokemon_name, pokemon_cp, pokemon_potential, pokemon_move_1, pokemon_move_2):
                            self.release_pokemon(pokemon_name, item['cp'], item['iv'], item['move_1'], item['move_2'], item['pokemon_data']['id'])

    def _release_pokemon_get_groups(self):
        pokemon_groups = {}
        request = self.bot.api.create_request()
        request.get_player()
        request.get_inventory()
        inventory_req = request.call()

        if inventory_req.get('responses', False) is False:
            return pokemon_groups

        inventory_dict = inventory_req['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

        user_web_inventory = os.path.join(_base_dir, 'web', 'inventory-%s.json' % (self.bot.config.username))
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
            group_pokemon_move_1 = pokemon_data['move_1']
            group_pokemon_move_2 = pokemon_data['move_2']

            if group_id not in pokemon_groups:
                pokemon_groups[group_id] = []

            pokemon_groups[group_id].append({
                'cp': group_pokemon_cp,
                'iv': group_pokemon_iv,
                'move_1': group_pokemon_move_1,
                'move_2': group_pokemon_move_2,
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

    def should_release_pokemon(self, pokemon_name, cp, iv, move_1, move_2, keep_best_mode = False):
        release_config = self._get_release_config_for(pokemon_name)

        if (keep_best_mode
            and not release_config.has_key('never_release')
            and not release_config.has_key('always_release')
            and not release_config.has_key('release_below_cp')
            and not release_config.has_key('release_below_iv')):
            return True

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

        release_not_move_1 = release_config.get("release_not_move_1", 0)
        if release_not_move_1 != 0 and move_1 != release_not_move_1:
            self.emit_event(
                'future_pokemon_release',
                formatted="Releasing {pokemon} (CP {cp}/IV {iv}) based on rule: Move 1 != {release_not_move_1}",
                data={
                    'pokemon': pokemon_name,
                    'cp': cp,
                    'iv': iv,
                    'release_not_move_1': release_not_move_1
                }
            )
            return True

        release_not_move_2 = release_config.get("release_not_move_2", 0)
        if release_not_move_2 != 0 and move_2 != release_not_move_2:
            self.emit_event(
                'future_pokemon_release',
                formatted="Releasing {pokemon} (CP {cp}/IV {iv}) based on rule: Move 2 != {release_not_move_2}",
                data={
                    'pokemon': pokemon_name,
                    'cp': cp,
                    'iv': iv,
                    'release_not_move_2': release_not_move_2
                }
            )
            return True

        logic_to_function = {
            'or': lambda x, y: x or y,
            'and': lambda x, y: x and y
        }

        if logic_to_function[cp_iv_logic](*release_results.values()):
            self.emit_event(
                'future_pokemon_release',
                formatted="Releasing {pokemon} (CP {cp}/IV {iv}) based on rule: CP < {below_cp} {cp_iv_logic} IV < {below_iv}",
                data={
                    'pokemon': pokemon_name,
                    'cp': cp,
                    'iv': iv,
                    'below_cp': release_cp,
                    'cp_iv_logic': cp_iv_logic.upper(),
                    'below_iv': release_iv
                }
            )

        return logic_to_function[cp_iv_logic](*release_results.values())

    def release_pokemon(self, pokemon_name, cp, iv, move_1, move_2, pokemon_id):
        response_dict = self.bot.api.release_pokemon(pokemon_id=pokemon_id)
        self.bot.metrics.released_pokemon()
        self.emit_event(
            'pokemon_release',
            formatted='Exchanged {pokemon} [CP {cp}] [IV {iv}] [Move 1 {move_1}] [Move 2 {move_2}] for candy.',
            data={
                'pokemon': pokemon_name,
                'cp': cp,
                'iv': iv,
                'move_1': move_1,
                'move_2': move_2
            }
        )
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
                keep_best = False

            if keep_best_cp == 0 and keep_best_iv == 0:
                keep_best = False

        return keep_best, keep_best_cp, keep_best_iv
