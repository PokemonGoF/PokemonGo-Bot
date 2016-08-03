# -*- coding: utf-8 -*-

import time
from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import normalized_reticle_size, sleep, spin_modifier


CATCH_SUCCESS = 1
CATCH_FAILED = 2
CATCH_VANISHED = 3

ITEM_POKEBALL = 1
ITEM_GREATBALL = 2
ITEM_ULTRABALL = 3

RAZZ_BERRY_ID = 701

LOGIC_TO_FUNCTION = {
    'or': lambda x, y: x or y,
    'and': lambda x, y: x and y
}


class Pokemon(object):

    def __init__(self, pokemon_list, pokemon_data):
        self.num = int(pokemon_data['pokemon_id']) - 1
        self.name = pokemon_list[int(self.num)]['Name']
        self.cp = pokemon_data['cp']
        self.attack = pokemon_data.get('individual_attack', 0)
        self.defense = pokemon_data.get('individual_defense', 0)
        self.stamina = pokemon_data.get('individual_stamina', 0)

    @property
    def iv(self):
        return round((self.attack + self.defense + self.stamina) / 45.0, 2)

    @property
    def iv_display(self):
        return '{}/{}/{}'.format(self.attack, self.defense, self.stamina)


class PokemonCatchWorker(object):

    def __init__(self, pokemon, bot):
        self.pokemon = pokemon
        self.api = bot.api
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.item_list = bot.item_list
        self.inventory = bot.inventory
        self.spawn_point_guid = ''
        self.response_key = ''
        self.response_status_key = ''

    ############################################################################
    # public methods
    ############################################################################

    def work(self, response_dict=None):
        response_dict = response_dict or self.create_encounter_api_call()

        # validate response
        if not response_dict:
            return False
        try:
            responses = response_dict['responses']
            response = responses[self.response_key]
            if response[self.response_status_key] != 1:
                return False
        except KeyError:
            return False

        # get pokemon data
        pokemon_data = response['wild_pokemon']['pokemon_data'] if 'wild_pokemon' in response else response['pokemon_data']
        pokemon = Pokemon(self.pokemon_list, pokemon_data)

        # log encounter
        logger.log('A Wild {} appeared! [CP {}] [Potential {}]'.format(pokemon.name, pokemon.cp, pokemon.iv), 'yellow')
        logger.log('IV [Attack/Defense/Stamina] = [{}]'.format(pokemon.iv_display))

        # simulate app
        sleep(3)

        # check for VIP pokemon
        is_vip = self._is_vip_pokemon(pokemon)
        if is_vip:
            logger.log(
                '[-] {} is a VIP Pokemon! [CP {}] [Potential {}] Nice! Try our best to catch it!'.format(
                    pokemon_data['name'],
                    pokemon_data['cp'],
                    pokemon_data['iv']
                ), 'red')

        # skip ignored pokemon
        elif not self._should_catch_pokemon(pokemon):
            return False

        # catch that pokemon!
        encounter_id = self.pokemon['encounter_id']
        catch_rate_by_ball = [0] + response['capture_probability']['capture_probability']  # offset so item ids match indces
        self._do_catch(pokemon, encounter_id, catch_rate_by_ball, is_vip=is_vip)

        # simulate app
        time.sleep(5)

    def create_encounter_api_call(self):
        encounter_id = self.pokemon['encounter_id']
        player_latitude = self.pokemon['latitude']
        player_longitude = self.pokemon['longitude']

        request = self.api.create_request()
        if 'spawn_point_id' in self.pokemon:
            spawn_point_id = self.pokemon['spawn_point_id']
            self.spawn_point_guid = spawn_point_id
            self.response_key = 'ENCOUNTER'
            self.response_status_key = 'status'
            request.encounter(
                encounter_id=encounter_id,
                spawn_point_id=spawn_point_id,
                player_latitude=player_latitude,
                player_longitude=player_longitude
            )
        else:
            fort_id = self.pokemon['fort_id']
            self.spawn_point_guid = fort_id
            self.response_key = 'DISK_ENCOUNTER'
            self.response_status_key = 'result'
            request.disk_encounter(
                encounter_id=encounter_id,
                fort_id=fort_id,
                player_latitude=player_latitude,
                player_longitude=player_longitude
            )
        return request.call()

    ############################################################################
    # helpers
    ############################################################################

    def _pokemon_matches_config(self, config, pokemon, default_logic='and'):
        pokemon_config = config.get(pokemon.name, config.get('any'))

        if not pokemon_config:
            return False

        catch_results = {
            'cp': False,
            'iv': False,
        }

        if pokemon_config.get('never_catch', False):
            return False

        if pokemon_config.get('always_catch', False):
            return True

        catch_cp = pokemon_config.get('catch_above_cp', 0)
        if pokemon.cp > catch_cp:
            catch_results['cp'] = True

        catch_iv = pokemon_config.get('catch_above_iv', 0)
        if pokemon.iv > catch_iv:
            catch_results['iv'] = True

        return LOGIC_TO_FUNCTION[pokemon_config.get('logic', default_logic)](*catch_results.values())

    def _should_catch_pokemon(self, pokemon):
        return self._pokemon_matches_config(self.config.catch, pokemon)

    def _is_vip_pokemon(self, pokemon):
        return self._pokemon_matches_config(self.config.vips, pokemon, default_logic='or')

    def _get_current_pokemon_ids(self):
        # don't use cached bot.get_inventory() here because we need to have actual information in capture logic
        response_dict = self.api.get_inventory()

        try:
            inventory_items = response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
        except KeyError:
            return []  # no items

        id_list = []
        for item in inventory_items:
            try:
                pokemon = item['inventory_item_data']['pokemon_data']
            except KeyError:
                continue

            # ignore eggs
            if pokemon.get('is_egg'):
                continue

            id_list.append(pokemon['id'])

        return id_list

    def _pct(self, rate_by_ball):
        return '{0:.2f}'.format(rate_by_ball * 100)

    def _use_berry(self, berry_id, berries_count, encounter_id, catch_rate_by_ball, current_ball):
        new_catch_rate_by_ball = []

        logger.log(
            'Catch Rate with {} is low ({}%). Throwing a {}... ({} remain!)'.format(
                self.item_list[str(current_ball)],
                self._pct(catch_rate_by_ball[current_ball]),
                self.item_list[str(berry_id)],
                berries_count - 1
            ))

        response_dict = self.api.use_item_capture(
            item_id=berry_id,
            encounter_id=encounter_id,
            spawn_point_id=self.spawn_point_guid
        )
        responses = response_dict['responses']

        if response_dict and response_dict['status_code'] == 1 and 'item_capture_mult' in responses['USE_ITEM_CAPTURE']:
            for i in range(len(catch_rate_by_ball)):
                new_catch_rate_by_ball[i] = catch_rate_by_ball[i] * responses['USE_ITEM_CAPTURE']['item_capture_mult']
            logger.log('Threw a berry! Catch Rate with {} has increased to {}%'.format(
                self.item_list[str(current_ball)],
                self._pct(catch_rate_by_ball[current_ball])
            ))
        else:
            if response_dict['status_code'] is 1:
                logger.log('Fail to use berry. Seem like you are softbanned.', 'red')
            else:
                logger.log('Fail to use berry. Status Code: {}'.format(response_dict['status_code']), 'red')

        return new_catch_rate_by_ball

    def _do_catch(self, pokemon, encounter_id, catch_rate_by_ball, is_vip=False):
        # settings that may be exposed at some point
        berry_id = RAZZ_BERRY_ID
        maximum_ball = ITEM_ULTRABALL if is_vip else ITEM_GREATBALL
        catch_rate_before_throw = 0.9 if is_vip else 0.35

        berries_count = self.bot.item_inventory_count(berry_id)
        items_stock = self.bot.current_inventory()

        while True:

            # find lowest available ball
            current_ball = ITEM_POKEBALL
            while items_stock[current_ball] == 0 and current_ball < maximum_ball:
                current_ball += 1
            if items_stock[current_ball] == 0:
                logger.log('No pokeballs to use!')
                break

            # check future ball count
            num_next_balls = 0
            next_ball = current_ball
            while next_ball < maximum_ball:
                next_ball += 1
                num_next_balls += items_stock[next_ball]

            # check if we've got berries to spare
            berries_to_spare = berries_count > 0 if is_vip else berries_count > num_next_balls + 30

            # use a berry if we are under our ideal rate and have berries to spare
            used_berry = False
            if catch_rate_by_ball[current_ball] < catch_rate_before_throw and berries_to_spare:
                catch_rate_by_ball = self._use_berry(berry_id, berries_count, encounter_id, catch_rate_by_ball, current_ball)
                berries_count -= 1
                used_berry = True

            # pick the best ball to catch with
            best_ball = current_ball
            while best_ball < maximum_ball:
                best_ball += 1
                if catch_rate_by_ball[current_ball] < catch_rate_before_throw and items_stock[best_ball] > 0:
                    # if current ball chance to catch is under our ideal rate, and player has better ball - then use it
                    current_ball = best_ball

            # if the rate is still low and we didn't throw a berry before, throw one
            if catch_rate_by_ball[current_ball] < catch_rate_before_throw and berries_count > 0 and not used_berry:
                catch_rate_by_ball = self._use_berry(berry_id, berries_count, encounter_id, catch_rate_by_ball, current_ball)
                berries_count -= 1

            # get current pokemon list before catch
            pokemon_before_catch = self._get_current_pokemon_ids()

            # try to catch pokemon!
            items_stock[current_ball] -= 1
            logger.log('Using {} (chance: {}%)... ({} remain!)'.format(
                self.item_list[str(current_ball)],
                self._pct(catch_rate_by_ball[current_ball]),
                items_stock[current_ball]
            ))

            reticle_size_parameter = normalized_reticle_size(self.config.catch_randomize_reticle_factor)
            spin_modifier_parameter = spin_modifier(self.config.catch_randomize_spin_factor)

            response_dict = self.api.catch_pokemon(
                encounter_id=encounter_id,
                pokeball=current_ball,
                normalized_reticle_size=reticle_size_parameter,
                spawn_point_id=self.spawn_point_guid,
                hit_pokemon=1,
                spin_modifier=spin_modifier_parameter,
                normalized_hit_position=1
            )

            try:
                catch_pokemon_status = response_dict['responses']['CATCH_POKEMON']['status']
            except KeyError:
                break

            # retry failed pokemon
            if catch_pokemon_status is CATCH_FAILED:
                logger.log('[-] Attempted to capture {} - failed.. trying again!'.format(pokemon.name), 'red')
                sleep(2)
                continue

            # abandon if pokemon vanished
            if catch_pokemon_status is CATCH_VANISHED:
                logger.log('Oh no! {} vanished! :('.format(pokemon.name), 'red')
                if self._pct(catch_rate_by_ball[current_ball]) == 100:
                    self.bot.softban = True

            if catch_pokemon_status is CATCH_SUCCESS:
                self.bot.metrics.captured_pokemon(pokemon.name, pokemon.cp, pokemon.iv_display, pokemon.iv)

                logger.log('Captured {}! [CP {}] [Potential {}] [{}] [+{} exp]'.format(
                    pokemon.name,
                    pokemon.cp,
                    pokemon.iv,
                    pokemon.iv_display,
                    sum(response_dict['responses']['CATCH_POKEMON']['capture_award']['xp'])
                ), 'blue')
                self.bot.softban = False

                # evolve pokemon if necessary
                if self.config.evolve_captured and (self.config.evolve_captured[0] == 'all' or pokemon.name in self.config.evolve_captured):
                    pokemon_after_catch = self._get_current_pokemon_ids()

                    pokemon_to_evolve = list(set(pokemon_after_catch) - set(pokemon_before_catch))
                    if len(pokemon_to_evolve) == 0:
                        break

                    self._do_evolve(pokemon, pokemon_to_evolve[0])

            break

    def _do_evolve(self, pokemon, new_pokemon_id):
        response_dict = self.api.evolve_pokemon(pokemon_id=new_pokemon_id)
        catch_pokemon_status = response_dict['responses']['EVOLVE_POKEMON']['result']
        if catch_pokemon_status == 1:
            logger.log('{} has been evolved!'.format(pokemon.name), 'green')
        else:
            logger.log('Failed to evolve {}!'.format(pokemon.name))
