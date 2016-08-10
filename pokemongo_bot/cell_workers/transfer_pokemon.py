import json
import os

from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.inventory import Pokemons


class TransferPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def work(self):
        pokemon_groups = self._release_pokemon_get_groups()
        for pokemon_id, group in pokemon_groups.iteritems():
            pokemon_name = Pokemons.name_for(pokemon_id)
            keep_best, keep_best_cp, keep_best_iv = self._validate_keep_best_config(pokemon_name)

            if keep_best:
                best_pokemon_ids = set()
                order_criteria = 'none'
                if keep_best_cp >= 1:
                    cp_limit = keep_best_cp
                    best_cp_pokemons = sorted(group, key=lambda x: (x.cp, x.iv), reverse=True)[:cp_limit]
                    best_pokemon_ids = set(pokemon.id for pokemon in best_cp_pokemons)
                    order_criteria = 'cp'

                if keep_best_iv >= 1:
                    iv_limit = keep_best_iv
                    best_iv_pokemons = sorted(group, key=lambda x: (x.iv, x.cp), reverse=True)[:iv_limit]
                    best_pokemon_ids |= set(pokemon.id for pokemon in best_iv_pokemons)
                    if order_criteria == 'cp':
                        order_criteria = 'cp and iv'
                    else:
                        order_criteria = 'iv'

                # remove best pokemons from all pokemons array
                all_pokemons = group
                best_pokemons = []
                for best_pokemon_id in best_pokemon_ids:
                    for pokemon in all_pokemons:
                        if best_pokemon_id == pokemon.id:
                            all_pokemons.remove(pokemon)
                            best_pokemons.append(pokemon)

                transfer_pokemons = [pokemon for pokemon in all_pokemons if self.should_release_pokemon(pokemon,True)]

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
                        self.release_pokemon(pokemon)
            else:
                group = sorted(group, key=lambda x: x.cp, reverse=True)
                for pokemon in group:
                    if self.should_release_pokemon(pokemon):
                        self.release_pokemon(pokemon)

    def _release_pokemon_get_groups(self):
        pokemon_groups = {}
        for pokemon in inventory.pokemons(True).all():
            if pokemon.in_fort or pokemon.is_favorite:
                continue

            group_id = pokemon.pokemon_id

            if group_id not in pokemon_groups:
                pokemon_groups[group_id] = []

            pokemon_groups[group_id].append(pokemon)

        return pokemon_groups

    def should_release_pokemon(self, pokemon, keep_best_mode = False):
        release_config = self._get_release_config_for(pokemon.name)

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
        if pokemon.cp < release_cp:
            release_results['cp'] = True

        release_iv = release_config.get('release_below_iv', 0)
        if pokemon.iv < release_iv:
            release_results['iv'] = True

        logic_to_function = {
            'or': lambda x, y: x or y,
            'and': lambda x, y: x and y
        }

        if logic_to_function[cp_iv_logic](*release_results.values()):
            self.emit_event(
                'future_pokemon_release',
                formatted="Releasing {pokemon} [CP {cp}] [IV {iv}] based on rule: CP < {below_cp} {cp_iv_logic} IV < {below_iv}",
                data={
                    'pokemon': pokemon.name,
                    'cp': pokemon.cp,
                    'iv': pokemon.iv,
                    'below_cp': release_cp,
                    'cp_iv_logic': cp_iv_logic.upper(),
                    'below_iv': release_iv
                }
            )

        return logic_to_function[cp_iv_logic](*release_results.values())

    def release_pokemon(self, pokemon):
        try:
            if self.bot.config.test:
                candy_awarded = 1
            else:
                response_dict = self.bot.api.release_pokemon(pokemon_id=pokemon.id)
                candy_awarded = response_dict['responses']['RELEASE_POKEMON']['candy_awarded']
        except KeyError:
            return

        # We could refresh here too, but adding 1 saves a inventory request
        candy = inventory.candies().get(pokemon.pokemon_id)
        candy.add(candy_awarded)
        self.bot.metrics.released_pokemon()
        self.emit_event(
            'pokemon_release',
            formatted='Exchanged {pokemon} [CP {cp}] [IV {iv}] for candy.',
            data={
                'pokemon': pokemon.name,
                'cp': pokemon.cp,
                'iv': pokemon.iv
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
