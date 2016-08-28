import json
import os

from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.inventory import Pokemons, Pokemon, Attack
from pokemongo_bot.datastore import Datastore
from operator import attrgetter
from random import randrange


class TransferPokemon(Datastore, BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(TransferPokemon, self).__init__(bot, config)

    def initialize(self):
        self.min_free_slot = self.config.get('min_free_slot', 5)
        self.transfer_wait_min = self.config.get('transfer_wait_min', 1)
        self.transfer_wait_max = self.config.get('transfer_wait_max', 4)

    def work(self):
        if not self._should_work():
            return

        pokemon_groups = self._release_pokemon_get_groups()
        for pokemon_id, group in pokemon_groups.iteritems():
            pokemon_name = Pokemons.name_for(pokemon_id)
            self._release_pokemon_worst_in_group(group, pokemon_name)

        if self.bot.config.release.get('all'):
            group = [p for p in inventory.pokemons().all()
                     if p.in_fort is False and p.is_favorite is False]
            self._release_pokemon_worst_in_group(group, 'all')

    def _should_work(self):
        random_number = randrange (0,20,1) 
        return inventory.Pokemons.get_space_left() <= self.min_free_slot - random_number

    def _release_pokemon_get_groups(self):
        pokemon_groups = {}
        for pokemon in inventory.pokemons().all():
            if pokemon.in_fort or pokemon.is_favorite:
                continue

            group_id = pokemon.pokemon_id

            if group_id not in pokemon_groups:
                pokemon_groups[group_id] = []

            pokemon_groups[group_id].append(pokemon)

        return pokemon_groups

    def _release_pokemon_worst_in_group(self, group, pokemon_name):
        keep_best, keep_best_cp, keep_best_iv = self._validate_keep_best_config(
            pokemon_name)
        # TODO continue list possible criteria
        keep_best_possible_criteria = ['cp', 'iv', 'iv_attack', 'iv_defense', 'iv_stamina',
                                       'moveset.attack_perfection', 'moveset.defense_perfection', 'hp', 'hp_max']
        keep_best_custom, keep_best_criteria, keep_amount = self._validate_keep_best_config_custom(
            pokemon_name, keep_best_possible_criteria)

        best_pokemon_ids = set()
        order_criteria = 'none'
        if keep_best:
            if keep_best_cp >= 1:
                cp_limit = keep_best_cp
                best_cp_pokemons = sorted(group, key=lambda x: (
                    x.cp, x.iv), reverse=True)[:cp_limit]
                best_pokemon_ids = set(
                    pokemon.unique_id for pokemon in best_cp_pokemons)
                order_criteria = 'cp'

            if keep_best_iv >= 1:
                iv_limit = keep_best_iv
                best_iv_pokemons = sorted(group, key=lambda x: (
                    x.iv, x.cp), reverse=True)[:iv_limit]
                best_pokemon_ids |= set(
                    pokemon.unique_id for pokemon in best_iv_pokemons)
                if order_criteria == 'cp':
                    order_criteria = 'cp and iv'
                else:
                    order_criteria = 'iv'
        elif keep_best_custom:
            limit = keep_amount
            # not sure if the u of unicode will stay, so make it go away
            keep_best_criteria = [str(keep_best_criteria[x])
                                  for x in range(len(keep_best_criteria))]
            best_pokemons = sorted(group, key=attrgetter(
                *keep_best_criteria), reverse=True)[:limit]
            best_pokemon_ids = set(
                pokemon.unique_id for pokemon in best_pokemons)
            order_criteria = ' then '.join(keep_best_criteria)

        if keep_best or keep_best_custom:
            # remove best pokemons from all pokemons array
            all_pokemons = group
            best_pokemons = []
            for best_pokemon_id in best_pokemon_ids:
                for pokemon in all_pokemons:
                    if best_pokemon_id == pokemon.unique_id:
                        all_pokemons.remove(pokemon)
                        best_pokemons.append(pokemon)

            transfer_pokemons = [
                pokemon for pokemon in all_pokemons if self.should_release_pokemon(pokemon, True)]

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

    def should_release_pokemon(self, pokemon, keep_best_mode=False):
        release_config = self._get_release_config_for(pokemon.name)

        if (keep_best_mode
                and not release_config.has_key('never_release')
                and not release_config.has_key('always_release')
                and not release_config.has_key('release_below_cp')
                and not release_config.has_key('release_below_iv')):
            return True

        cp_iv_logic = release_config.get('logic')
        if not cp_iv_logic:
            cp_iv_logic = self._get_release_config_for(
                'any').get('logic', 'and')

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
        """

        :type pokemon: Pokemon
        """
        try:
            if self.bot.config.test:
                candy_awarded = 1
            else:
                response_dict = self.bot.api.release_pokemon(
                    pokemon_id=pokemon.unique_id)
                candy_awarded = response_dict['responses'][
                    'RELEASE_POKEMON']['candy_awarded']
        except KeyError:
            return

        # We could refresh here too, but adding 1 saves a inventory request
        candy = inventory.candies().get(pokemon.pokemon_id)
        candy.add(candy_awarded)
        inventory.pokemons().remove(pokemon.unique_id)
        self.bot.metrics.released_pokemon()
        self.emit_event(
            'pokemon_release',
            formatted='Exchanged {pokemon} [IV {iv}] [CP {cp}] [{candy} candies]',
            data={
                'pokemon': pokemon.name,
                'iv': pokemon.iv,
                'cp': pokemon.cp,
                'candy': candy.quantity
            }
        )
        with self.bot.database as conn:
            c = conn.cursor()
            c.execute(
                "SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='transfer_log'")

        result = c.fetchone()

        while True:
            if result[0] == 1:
                conn.execute('''INSERT INTO transfer_log (pokemon, iv, cp) VALUES (?, ?, ?)''',
                             (pokemon.name, pokemon.iv, pokemon.cp))
                break
            else:
                self.emit_event(
                    'transfer_log',
                    sender=self,
                    level='info',
                    formatted="transfer_log table not found, skipping log"
                )
                break
        action_delay(self.transfer_wait_min, self.transfer_wait_max)

    def _get_release_config_for(self, pokemon):
        release_config = self.bot.config.release.get(pokemon)
        if not release_config:
            release_config = self.bot.config.release.get('any')
        if not release_config:
            release_config = {}
        return release_config

    def _validate_keep_best_config_custom(self, pokemon_name, keep_best_possible_custom):
        keep_best = False

        release_config = self._get_release_config_for(pokemon_name)
        keep_best_custom = release_config.get('keep_best_custom', '')
        keep_amount = release_config.get('amount', 0)

        if keep_best_custom and keep_amount:
            keep_best = True

            keep_best_custom = keep_best_custom.split(',')
            for _str in keep_best_custom:
                if _str not in keep_best_possible_custom:
                    keep_best = False
                    break

            try:
                keep_amount = int(keep_amount)
            except ValueError:
                keep_best = False

            if keep_amount < 0:
                keep_best = False

        return keep_best, keep_best_custom, keep_amount

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
