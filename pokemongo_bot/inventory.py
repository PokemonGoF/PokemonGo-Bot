import json
import logging
import os
from collections import OrderedDict

from pokemongo_bot.base_dir import _base_dir

'''
Helper class for updating/retrieving Inventory data

Interesting info and formulas:
https://drive.google.com/file/d/0B0TeYGBPiuzaenhUNE5UWnRCVlU/view
https://www.reddit.com/r/pokemongodev/comments/4w7mdg/combat_damage_calculation_formula_exactly/
'''


#
# Abstraction

class _StaticInventoryComponent(object):
    STATIC_DATA_FILE = None  # optionally load static data from file,
                             # dropping the data in a static variable named STATIC_DATA
    STATIC_DATA = None

    def __init__(self):
        if self.STATIC_DATA_FILE is not None:
            self.init_static_data()

    @classmethod
    def init_static_data(cls):
        if not hasattr(cls, 'STATIC_DATA') or cls.STATIC_DATA is None:
            cls.STATIC_DATA = cls.process_static_data(
                json.load(open(cls.STATIC_DATA_FILE)))

    @classmethod
    def process_static_data(cls, data):
        # optional hook for processing the static data
        # default is to use the data directly
        return data


class _BaseInventoryComponent(_StaticInventoryComponent):
    TYPE = None  # base key name for items of this type
    ID_FIELD = None  # identifier field for items of this type

    def __init__(self):
        self._data = {}
        super(_BaseInventoryComponent, self).__init__()

    def parse(self, item):
        # optional hook for parsing the dict for this item
        # default is to use the dict directly
        return item

    def retrieve_data(self, inventory):
        assert self.TYPE is not None
        assert self.ID_FIELD is not None
        ret = {}
        for item in inventory:
            data = item['inventory_item_data']
            if self.TYPE in data:
                item = data[self.TYPE]
                key = item[self.ID_FIELD]
                ret[key] = self.parse(item)
        return ret

    def refresh(self, inventory):
        self._data = self.retrieve_data(inventory)

    def get(self, object_id):
        return self._data.get(object_id)

    def all(self):
        return list(self._data.values())


#
# Inventory Components

class Candies(_BaseInventoryComponent):
    TYPE = 'candy'
    ID_FIELD = 'family_id'

    @classmethod
    def family_id_for(cls, pokemon_id):
        return Pokemons.first_evolution_id_for(pokemon_id)

    def get(self, pokemon_id):
        family_id = self.family_id_for(pokemon_id)
        return self._data.setdefault(family_id, Candy(family_id, 0))

    def parse(self, item):
        candy = item['candy'] if 'candy' in item else 0
        return Candy(item['family_id'], candy)


class Pokedex(_BaseInventoryComponent):
    TYPE = 'pokedex_entry'
    ID_FIELD = 'pokemon_id'

    def seen(self, pokemon_id):
        return pokemon_id in self._data

    def captured(self, pokemon_id):
        if not self.seen(pokemon_id):
            return False
        return self._data[pokemon_id]['times_captured'] > 0


class Items(_BaseInventoryComponent):
    TYPE = 'item'
    ID_FIELD = 'item_id'
    STATIC_DATA_FILE = os.path.join(_base_dir, 'data', 'items.json')

    def parse(self, item_data):
        item_id = item_data.get(Items.ID_FIELD, None)
        item_count = item_data['count'] if 'count' in item_data else 0
        return Item(item_id, item_count)

    def get(self, item_id):
        return self._data.setdefault(item_id, Item(item_id, 0))

    @classmethod
    def name_for(cls, item_id):
        return cls.STATIC_DATA[str(item_id)]

    @classmethod
    def get_space_used(cls):
        """
        Counts the space used in item inventory.
        :return: The space used in item inventory.
        :rtype: int
        """
        space_used = 1
        for item_in_inventory in _inventory.items.all():
            space_used += item_in_inventory.count
        return space_used

    @classmethod
    def get_space_left(cls):
        """
        Compute the space  left in item inventory.
        :return: The space left in item inventory.
        :rtype: int
        """
        _inventory.retrieve_item_inventory_size()
        return _inventory.item_inventory_size - cls.get_space_used()


class Pokemons(_BaseInventoryComponent):
    TYPE = 'pokemon_data'
    ID_FIELD = 'id'
    STATIC_DATA_FILE = os.path.join(_base_dir, 'data', 'pokemon.json')

    @classmethod
    def process_static_data(cls, data):
        data = [PokemonInfo(d) for d in data]

        # process evolution info
        for p in data:
            next_all = p.next_evolutions_all
            if len(next_all) <= 0:
                continue

            # only next level evolutions, not all possible
            p.next_evolution_ids = [idx for idx in next_all
                                    if data[idx-1].prev_evolution_id == p.id]

            # only final evolutions
            p.last_evolution_ids = [idx for idx in next_all
                                    if not data[idx-1].has_next_evolution]
            assert len(p.last_evolution_ids) > 0

        return data

    @classmethod
    def data_for(cls, pokemon_id):
        # type: (int) -> PokemonInfo
        return cls.STATIC_DATA[pokemon_id - 1]

    @classmethod
    def name_for(cls, pokemon_id):
        return cls.data_for(pokemon_id).name

    @classmethod
    def first_evolution_id_for(cls, pokemon_id):
        return cls.data_for(pokemon_id).first_evolution_id

    @classmethod
    def prev_evolution_id_for(cls, pokemon_id):
        return cls.data_for(pokemon_id).prev_evolution_id

    @classmethod
    def next_evolution_ids_for(cls, pokemon_id):
        return cls.data_for(pokemon_id).next_evolution_ids

    @classmethod
    def last_evolution_ids_for(cls, pokemon_id):
        return cls.data_for(pokemon_id).last_evolution_ids

    @classmethod
    def has_next_evolution(cls, pokemon_id):
        return cls.data_for(pokemon_id).has_next_evolution

    @classmethod
    def evolution_cost_for(cls, pokemon_id):
        return cls.data_for(pokemon_id).evolution_cost

    def parse(self, item):
        if 'is_egg' in item:
            return Egg(item)
        return Pokemon(item)

    def all(self):
        # by default don't include eggs in all pokemon (usually just
        # makes caller's lives more difficult)
        return [p for p in super(Pokemons, self).all() if not isinstance(p, Egg)]

    def add(self, pokemon):
        if pokemon.id <= 0:
            raise ValueError("Can't add a pokemin whitout id")
        if pokemon.id in self._data:
            raise ValueError("Pokemon already present in the inventory")
        self._data[pokemon.id] = pokemon

    def remove(self, pokemon_id):
        if pokemon_id not in self._data:
            raise ValueError("Pokemon not present in the inventory")
        self._data.pop(pokemon_id)


#
# Static Components

class Types(_StaticInventoryComponent):
    """
    Types of attacks and pokemons

    See more information:
    https://i.redd.it/oy7lrixl8r9x.png
    https://www.reddit.com/r/TheSilphRoad/comments/4t8seh/pokemon_go_type_advantage_chart/
    https://github.com/jehy/Pokemon-Go-Weakness-calculator/blob/master/app/src/main/java/ru/jehy/pokemonweaknesscalculator/MainActivity.java#L31
    """

    STATIC_DATA_FILE = os.path.join(_base_dir, 'data', 'types.json')

    @classmethod
    def process_static_data(cls, data):
        # create instances
        ret = OrderedDict()
        for t in sorted(data, key=lambda x: x["name"]):
            name = str(t["name"])
            ret[name] = Type(name, t["effectiveAgainst"], t["weakAgainst"])

        # additional manipulations
        size = len(ret)
        by_effectiveness = {}
        by_resistance = {}
        for t in ret.itervalues():  # type: Type
            t.attack_effective_against = [ret[name] for name in t.attack_effective_against]
            t.attack_weak_against = [ret[name] for name in t.attack_weak_against]

            # group types effective against, weak against specific types
            for l, d in (t.attack_effective_against, by_effectiveness), \
                        (t.attack_weak_against, by_resistance):
                for tt in l:
                    if tt not in d:
                        d[tt] = set()
                    d[tt].add(t)

            # calc average factor for damage of this type relative to all types
            t.rate = (size
                      + ((EFFECTIVENESS_FACTOR-1) * len(t.attack_effective_against))
                      - ((1-RESISTANCE_FACTOR) * len(t.attack_weak_against))) / size

        # set pokemon type resistance/weakness info
        for t in ret.itervalues():  # type: Type
            t.pokemon_resistant_to = by_resistance[t]
            t.pokemon_vulnerable_to = by_effectiveness[t]

        return ret

    @classmethod
    def get(cls, type_name):
        # type: (Union[string, Type]) -> Type
        type_name = str(type_name)
        if type_name not in cls.STATIC_DATA:
            raise ValueError("Unknown type: {}".format(type_name))
        return cls.STATIC_DATA[type_name]

    @classmethod
    def all(cls):
        return cls.STATIC_DATA.values()

    @classmethod
    def rating(cls):
        return sorted(cls.all(), key=lambda x: x.rate, reverse=True)


class LevelToCPm(_StaticInventoryComponent):
    """
    Data for the CP multipliers at different levels
    See http://pokemongo.gamepress.gg/cp-multiplier
    See https://github.com/justinleewells/pogo-optimizer/blob/edd692d/data/game/level-to-cpm.json
    """

    STATIC_DATA_FILE = os.path.join(_base_dir, 'data', 'level_to_cpm.json')
    MAX_LEVEL = 40
    MAX_CPM = .0
    # half of the lowest difference between CPMs
    HALF_DIFF_BETWEEN_HALF_LVL = 14e-3

    @classmethod
    def init_static_data(cls):
        super(LevelToCPm, cls).init_static_data()
        cls.MAX_CPM = cls.cp_multiplier_for(cls.MAX_LEVEL)
        assert cls.MAX_CPM > .0

    @classmethod
    def cp_multiplier_for(cls, level):
        # type: (Union[float, int, string]) -> float
        level = float(level)
        level = str(int(level) if level.is_integer() else level)
        return cls.STATIC_DATA[level]

    @classmethod
    def level_from_cpm(cls, cp_multiplier):
        # type: (float) -> float
        for lvl, cpm in cls.STATIC_DATA.iteritems():
            diff = abs(cpm - cp_multiplier)
            if diff <= cls.HALF_DIFF_BETWEEN_HALF_LVL:
                return float(lvl)
        raise ValueError("Unknown cp_multiplier: {}".format(cp_multiplier))


class _Attacks(_StaticInventoryComponent):
    BY_NAME = {}  # type: Dict[string, Attack]
    BY_TYPE = {}  # type: Dict[List[Attack]]
    BY_DPS = []  # type: List[Attack]

    @classmethod
    def process_static_data(cls, moves):
        ret = {}
        by_type = {}
        by_name = {}
        fast = cls is FastAttacks
        for attack in moves:
            attack = Attack(attack) if fast else ChargedAttack(attack)
            ret[attack.id] = attack
            by_name[attack.name] = attack

            attack_type = str(attack.type)
            if attack_type not in by_type:
                by_type[attack_type] = []
            by_type[attack_type].append(attack)

        for t in by_type.iterkeys():
            attacks = sorted(by_type[t], key=lambda m: m.dps, reverse=True)
            min_dps = attacks[-1].dps
            max_dps = attacks[0].dps - min_dps
            if max_dps > .0:
                for attack in attacks:  # type: Attack
                    attack.rate_in_type = (attack.dps - min_dps) / max_dps
            by_type[t] = attacks

        cls.BY_NAME = by_name
        cls.BY_TYPE = by_type
        cls.BY_DPS = sorted(ret.values(), key=lambda m: m.dps, reverse=True)

        return ret

    @classmethod
    def data_for(cls, attack_id):
        # type: (int) -> Attack
        if attack_id not in cls.STATIC_DATA:
            raise ValueError("Attack {} not found in {}".format(
                attack_id, cls.__name__))
        return cls.STATIC_DATA[attack_id]

    @classmethod
    def by_name(cls, name):
        # type: (string) -> Attack
        return cls.BY_NAME[name]

    @classmethod
    def list_for_type(cls, type_name):
        # type: (Union[string, Type]) -> List[Attack]
        """
        :return: Attacks sorted by DPS in descending order
        """
        return cls.BY_TYPE[str(type_name)]

    @classmethod
    def all(cls):
        return cls.STATIC_DATA.values()

    @classmethod
    def all_by_dps(cls):
        return cls.BY_DPS


class FastAttacks(_Attacks):
    STATIC_DATA_FILE = os.path.join(_base_dir, 'data', 'fast_moves.json')


class ChargedAttacks(_Attacks):
    STATIC_DATA_FILE = os.path.join(_base_dir, 'data', 'charged_moves.json')


#
# Instances

class Type(object):
    def __init__(self, name, effective_against, weak_against):
        # type: (string, Iterable[Type], Iterable[Type]) -> None

        self.name = name

        # effective way to represent type with one character
        # for example it's very useful for nicknaming pokemon
        #  using its attack types
        #
        # if first char is unique - use it, in other case
        #  use suitable substitute
        type_to_one_char_map = {
            'Bug': 'B',
            'Dark': 'K',
            'Dragon': 'D',
            'Electric': 'E',
            'Fairy': 'Y',
            'Fighting': 'T',
            'Fire': 'F',
            'Flying': 'L',
            'Ghost': 'H',
            'Grass': 'A',
            'Ground': 'G',
            'Ice': 'I',
            'Normal': 'N',
            'Poison': 'P',
            'Psychic': 'C',
            'Rock': 'R',
            'Steel': 'S',
            'Water': 'W',
        }
        self.as_one_char = type_to_one_char_map[name]

        # attack of this type is effective against ...
        self.attack_effective_against = set(effective_against)
        # attack of this type is weak against ...
        self.attack_weak_against = set(weak_against)
        # pokemon of this type is resistant to ...
        self.pokemon_resistant_to = set()  # type: Set[Type]
        # pokemon of this type is vulnerable to ...
        self.pokemon_vulnerable_to = set()  # type: Set[Type]

        # average factor for damage of this type relative to all types
        self.rate = 1.

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Candy(object):
    def __init__(self, family_id, quantity):
        self.type = Pokemons.name_for(family_id)
        self.quantity = quantity

    def consume(self, amount):
        if self.quantity < amount:
            raise Exception('Tried to consume more {} candy than you have'.format(self.type))
        self.quantity -= amount

    def add(self, amount):
        if amount < 0:
            raise Exception('Must add positive amount of candy')
        self.quantity += amount


class Item(object):
    def __init__(self, item_id, item_count):
        self.id = item_id
        self.name = Items.name_for(self.id)
        self.count = item_count

    def remove(self, amount):
        if self.count < amount:
            raise Exception('Tried to remove more {} than you have'.format(self.name))
        self.count -= amount

    def add(self, amount):
        if amount < 0:
            raise Exception('Must add positive amount of {}'.format(self.name))
        self.count += amount


class Egg(object):
    def __init__(self, data):
        self._data = data

    def has_next_evolution(self):
        return False


class PokemonInfo(object):
    """
    Static information about pokemon kind
    """
    def __init__(self, data):
        self._data = data
        self.id = int(data["Number"])
        self.name = data['Name']  # type: string
        self.classification = data['Classification']  # type: string

        # prepare types
        self.type1 = Types.get(data['Type I'][0])
        self.type2 = None
        self.types = [self.type1]  # required type
        for t in data.get('Type II', []):
            self.type2 = Types.get(t)
            self.types.append(self.type2)  # second type
            break

        # base chance to capture pokemon
        self.capture_rate = data['CaptureRate']
        # chance of the pokemon to flee away
        self.flee_rate = data['FleeRate']

        # prepare attacks (moves)
        self.fast_attacks = self._process_attacks()
        self.charged_attack = self._process_attacks(charged=True)

        # prepare movesets
        self.movesets = self._process_movesets()

        # Basic Values of the pokemon (identical for all pokemons of one kind)
        self.base_attack = data['BaseAttack']
        self.base_defense = data['BaseDefense']
        self.base_stamina = data['BaseStamina']

        # calculate maximum CP for the pokemon (best IVs, lvl 40)
        self.max_cp = _calc_cp(self.base_attack, self.base_defense,
                               self.base_stamina)

        #
        # evolutions info for this pokemon

        # id of the very first level evolution
        self.first_evolution_id = self.id
        # id of the previous evolution (one level only)
        self.prev_evolution_id = None
        # ids of all available previous evolutions in the family
        self.prev_evolutions_all = []
        if 'Previous evolution(s)' in data:
            ids = [int(e['Number']) for e in data['Previous evolution(s)']]
            self.first_evolution_id = ids[0]
            self.prev_evolution_id = ids[-1]
            self.prev_evolutions_all = ids

        # Number of candies for the next evolution (if possible)
        self.evolution_cost = 0
        # next evolution flag
        self.has_next_evolution = 'Next evolution(s)' in data \
                                  or 'Next Evolution Requirements' in data
        # ids of the last level evolutions
        self.last_evolution_ids = [self.id]
        # ids of the next possible evolutions (one level only)
        self.next_evolution_ids = []
        # ids of all available next evolutions in the family
        self.next_evolutions_all = []
        if self.has_next_evolution:
            ids = [int(e['Number']) for e in data['Next evolution(s)']]
            self.next_evolutions_all = ids
            self.evolution_cost = int(data['Next Evolution Requirements']['Amount'])

    @property
    def family_id(self):
        return self.first_evolution_id

    @property
    def is_seen(self):
        return pokedex().seen(self.id)

    @property
    def is_captured(self):
        return pokedex().captured(self.id)

    def _process_movesets(self):
        # type: () -> List[Moveset]
        """
        The optimal moveset is the combination of two moves, one quick move
        and one charge move, that deals the most damage over time.

        Because each quick move gains a certain amount of energy (different
        for different moves) and each charge move requires a different amount
        of energy to use, sometimes, a quick move with lower DPS will be
        better since it charges the charge move faster.  On the same note,
        sometimes a charge move that has lower DPS will be more optimal since
        it may require less energy or it may last for a longer period of time.

        Attacker have STAB (Same-type attack bonus - x1.25) pokemon have the
        same type as attack. So we add it to the "Combo DPS" of the moveset.

        The defender attacks in intervals of 1 second for the first 2 attacks,
        and then in intervals of 2 seconds for the remainder of the attacks.
        This explains why we see two consecutive quick attacks at the beginning
        of the match.  As a result, we add +2 seconds to the DPS calculation
        for defender DPS output.

        So to determine an optimal defensive moveset, we follow the same  method
        as we did for optimal offensive movesets, but instead calculate  the
        highest "Combo DPS" with an added 2 seconds to the quick move cool down.

        Note: critical hits have not yet been implemented in the game

        See http://pokemongo.gamepress.gg/optimal-moveset-explanation
        See http://pokemongo.gamepress.gg/defensive-tactics
        """

        # Prepare movesets
        movesets = []
        for fm in self.fast_attacks:
            for chm in self.charged_attack:
                movesets.append(Moveset(fm, chm, self.types, self.id))
        assert len(movesets) > 0

        # Calculate attack perfection for each moveset
        movesets = sorted(movesets, key=lambda m: m.dps_attack)
        worst_dps = movesets[0].dps_attack
        best_dps = movesets[-1].dps_attack
        if best_dps > worst_dps:
            for moveset in movesets:
                current_dps = moveset.dps_attack
                moveset.attack_perfection = \
                    (current_dps - worst_dps) / (best_dps - worst_dps)

        # Calculate defense perfection for each moveset
        movesets = sorted(movesets, key=lambda m: m.dps_defense)
        worst_dps = movesets[0].dps_defense
        best_dps = movesets[-1].dps_defense
        if best_dps > worst_dps:
            for moveset in movesets:
                current_dps = moveset.dps_defense
                moveset.defense_perfection = \
                    (current_dps - worst_dps) / (best_dps - worst_dps)

        return sorted(movesets, key=lambda m: m.dps, reverse=True)

    def _process_attacks(self, charged=False):
        # type: (bool) -> List[Attack]
        key = 'Fast Attack(s)' if not charged else 'Special Attack(s)'
        moves_dict = (ChargedAttacks if charged else FastAttacks).BY_NAME
        moves = []
        for name in self._data[key]:
            if name not in moves_dict:
                raise KeyError('Unknown {} attack: "{}"'.format(
                    'charged' if charged else 'fast', name))
            moves.append(moves_dict[name])
        moves = sorted(moves, key=lambda m: m.dps, reverse=True)
        assert len(moves) > 0
        return moves


class Pokemon(object):
    def __init__(self, data):
        self._data = data
        # Unique ID for this particular Pokemon
        self.id = data.get('id', 0)
        # Id of the such pokemons in pokedex
        self.pokemon_id = data['pokemon_id']
        # Static information
        self.static = Pokemons.data_for(self.pokemon_id)

        # Combat points value
        self.cp = data['cp']
        # Base CP multiplier, fixed at the catch time
        self.cp_bm = data['cp_multiplier']
        # Changeable part of the CP multiplier, increasing at power up
        self.cp_am = data.get('additional_cp_multiplier', .0)
        # Resulting CP multiplier
        self.cp_m = self.cp_bm + self.cp_am

        # Current pokemon level (half of level is a normal value)
        self.level = LevelToCPm.level_from_cpm(self.cp_m)

        # Maximum health points
        self.hp_max = data['stamina_max']
        # Current health points
        self.hp = data.get('stamina', self.hp_max)
        assert 0 <= self.hp <= self.hp_max

        # Individial Values of the current specific pokemon (different for each)
        self.iv_attack = data.get('individual_attack', 0)
        self.iv_defense = data.get('individual_defense', 0)
        self.iv_stamina = data.get('individual_stamina', 0)

        # Basic Values of the pokemon (identical for all pokemons of one kind)
        base_attack = self.static.base_attack
        base_defense = self.static.base_defense
        base_stamina = self.static.base_stamina

        self.name = self.static.name
        self.nickname_raw = data.get('nickname', '')
        self.nickname = self.nickname_raw or self.name

        self.in_fort = 'deployed_fort_id' in data
        self.is_favorite = data.get('favorite', 0) is 1

        self.fast_attack = FastAttacks.data_for(data['move_1'])
        self.charged_attack = ChargedAttacks.data_for(data['move_2'])  # type: ChargedAttack

        # Individial values (IV) perfection percent
        self.iv = self._compute_iv_perfection()

        # IV CP perfection - kind of IV perfection percent but calculated
        #  using weight of each IV in its contribution to CP of the best
        #  evolution of current pokemon
        # So it tends to be more accurate than simple IV perfection
        self.ivcp = self._compute_cp_perfection()

        # Exact value of current CP (not rounded)
        self.cp_exact = _calc_cp(
            base_attack, base_defense, base_stamina,
            self.iv_attack, self.iv_defense, self.iv_stamina, self.cp_m)
        assert max(int(self.cp_exact), 10) == self.cp

        # Percent of maximum possible CP
        self.cp_percent = self.cp_exact / self.static.max_cp

        # Get moveset instance with calculated DPS and perfection percents
        self.moveset = self._get_moveset()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def update_nickname(self, new_nickname):
        self.nickname_raw = new_nickname
        self.nickname = self.nickname_raw or self.name

    def can_evolve_now(self):
        return self.has_next_evolution() and \
               self.candy_quantity >= self.evolution_cost

    def has_next_evolution(self):
        return self.static.has_next_evolution

    def has_seen_next_evolution(self):
        for pokemon_id in self.next_evolution_ids:
            if pokedex().captured(pokemon_id):
                return True
        return False

    @property
    def family_id(self):
        return self.static.family_id

    @property
    def first_evolution_id(self):
        return self.static.first_evolution_id

    @property
    def prev_evolution_id(self):
        return self.static.prev_evolution_id

    @property
    def next_evolution_ids(self):
        return self.static.next_evolution_ids

    @property
    def last_evolution_ids(self):
        return self.static.last_evolution_ids

    @property
    def candy_quantity(self):
        return candies().get(self.pokemon_id).quantity

    @property
    def evolution_cost(self):
        return self.static.evolution_cost

    @property
    def iv_display(self):
        return '{}/{}/{}'.format(self.iv_attack, self.iv_defense, self.iv_stamina)

    def _compute_iv_perfection(self):
        total_iv = self.iv_attack + self.iv_defense + self.iv_stamina
        iv_perfection = round((total_iv / 45.0), 2)
        return iv_perfection

    def _compute_cp_perfection(self):
        """
        CP perfect percent is more accurate than IV perfect

        We know attack plays an important role in CP, and different
        pokemons have different base value, that's means 15/14/15 is
        better than 14/15/15 for lot of pokemons, and if one pokemon's
        base def is more than base sta, 15/15/14 is better than 15/14/15.

        See https://github.com/jabbink/PokemonGoBot/issues/469

        So calculate CP perfection at final level for the best of the final
        evolutions of the pokemon.
        """
        variants = []
        iv_attack = self.iv_attack
        iv_defense = self.iv_defense
        iv_stamina = self.iv_stamina
        cp_m = LevelToCPm.MAX_CPM
        last_evolution_ids = self.last_evolution_ids
        for pokemon_id in last_evolution_ids:
            poke_info = Pokemons.data_for(pokemon_id)
            base_attack = poke_info.base_attack
            base_defense = poke_info.base_defense
            base_stamina = poke_info.base_stamina

            # calculate CP variants at maximum level
            worst_cp = _calc_cp(base_attack, base_defense, base_stamina,
                                0, 0, 0, cp_m)
            perfect_cp = _calc_cp(base_attack, base_defense, base_stamina,
                                  cp_multiplier=cp_m)
            current_cp = _calc_cp(base_attack, base_defense, base_stamina,
                                  iv_attack, iv_defense, iv_stamina, cp_m)
            cp_perfection = (current_cp - worst_cp) / (perfect_cp - worst_cp)
            variants.append(cp_perfection)

        # get best value (probably for the best evolution)
        cp_perfection = max(variants)
        return cp_perfection

    def _get_moveset(self):
        move1 = self.fast_attack
        move2 = self.charged_attack
        movesets = self.static.movesets
        current_moveset = None
        for moveset in movesets:  # type: Moveset
            if moveset.fast_attack == move1 and moveset.charged_attack == move2:
                current_moveset = moveset
                break

        if current_moveset is None:
            error = "Unexpected moveset [{}, {}] for #{} {}," \
                    " please update info in pokemon.json and create issue/PR" \
                .format(move1, move2, self.pokemon_id, self.name)
            # raise ValueError(error)
            logging.getLogger(type(self).__name__).error(error)
            current_moveset = Moveset(
                move1, move2, self.static.types, self.pokemon_id)

        return current_moveset


class Attack(object):
    def __init__(self, data):
        # self._data = data  # Not needed - all saved in fields
        self.id = data['id']
        self.name = data['name']
        self.type = Types.get(data['type'])
        self.damage = data['damage']
        self.duration = data['duration'] / 1000.0  # duration in seconds

        # Energy addition for fast attack
        # Energy cost for charged attack
        self.energy = data['energy']

        # Damage Per Second
        # recalc for better precision
        self.dps = self.damage / self.duration

        # Perfection of the attack in it's type (from 0 to 1)
        self.rate_in_type = .0

    @property
    def damage_with_stab(self):
        # damage with STAB (Same-type attack bonus)
        return self.damage * STAB_FACTOR

    @property
    def dps_with_stab(self):
        # DPS with STAB (Same-type attack bonus)
        return self.dps * STAB_FACTOR

    @property
    def effective_against(self):
        return self.type.attack_effective_against

    @property
    def weak_against(self):
        return self.type.attack_weak_against

    @property
    def energy_per_second(self):
        return self.energy / self.duration

    @property
    def dodge_window(self):
        # TODO:  Attack Dodge Window
        return NotImplemented

    @property
    def is_charged(self):
        return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class ChargedAttack(Attack):
    def __init__(self, data):
        super(ChargedAttack, self).__init__(data)

    @property
    def is_charged(self):
        return True


class Moveset(object):
    def __init__(self, fm, chm, pokemon_types=(), pokemon_id=-1):
        # type: (Attack, ChargedAttack, List[Type], int) -> None
        if len(pokemon_types) <= 0 < pokemon_id:
            pokemon_types = Pokemons.data_for(pokemon_id).types

        self.pokemon_id = pokemon_id
        self.fast_attack = fm
        self.charged_attack = chm

        # See Pokemons._process_movesets()
        # See http://pokemongo.gamepress.gg/optimal-moveset-explanation
        # See http://pokemongo.gamepress.gg/defensive-tactics

        fm_number = 100  # for simplicity we use 100

        fm_energy = fm.energy * fm_number
        fm_damage = fm.damage * fm_number
        fm_secs = fm.duration * fm_number

        # Defender attacks in intervals of 1 second for the
        #   first 2 attacks, and then in intervals of 2 seconds
        # So add 1.95 seconds to the quick move cool down for defense
        #   1.95 is something like an average here
        #   TODO: Do something better?
        fm_defense_secs = (fm.duration + 1.95) * fm_number

        chm_number = fm_energy / chm.energy
        chm_damage = chm.damage * chm_number
        chm_secs = chm.duration * chm_number

        damage_sum = fm_damage + chm_damage
        # raw Damage-Per-Second for the moveset
        self.dps = damage_sum / (fm_secs + chm_secs)
        # average DPS for defense
        self.dps_defense = damage_sum / (fm_defense_secs + chm_secs)

        # apply STAB (Same-type attack bonus)
        if fm.type in pokemon_types:
            fm_damage *= STAB_FACTOR
        if chm.type in pokemon_types:
            chm_damage *= STAB_FACTOR

        # DPS for attack (counting STAB)
        self.dps_attack = (fm_damage + chm_damage) / (fm_secs + chm_secs)

        # Moveset perfection percent for attack and for defense
        # Calculated for current pokemon kind only, not between all pokemons
        # So 100% perfect moveset can be weak if pokemon is weak (e.g. Caterpie)
        self.attack_perfection = .0
        self.defense_perfection = .0

        # TODO: True DPS for real combat (floor(Attack/200 * MovePower * STAB) + 1)
        # See http://pokemongo.gamepress.gg/pokemon-attack-explanation

    def __str__(self):
        return '[{}, {}]'.format(self.fast_attack, self.charged_attack)

    def __repr__(self):
        return '[{}, {}]'.format(self.fast_attack, self.charged_attack)


class Inventory(object):
    def __init__(self, bot):
        self.bot = bot
        self.pokedex = Pokedex()
        self.candy = Candies()
        self.items = Items()
        self.pokemons = Pokemons()
        self.refresh()
        self.item_inventory_size = None

    def refresh(self):
        # TODO: it would be better if this class was used for all
        # inventory management. For now, I'm just clearing the old inventory field
        self.bot.latest_inventory = None
        inventory = self.bot.get_inventory()['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
        for i in (self.pokedex, self.candy, self.items, self.pokemons):
            i.refresh(inventory)

        user_web_inventory = os.path.join(_base_dir, 'web', 'inventory-%s.json' % (self.bot.config.username))
        with open(user_web_inventory, 'w') as outfile:
            json.dump(inventory, outfile)
    def retrieve_item_inventory_size(self):
        """
        Retrieves the item inventory size
        :return: Nothing.
        :rtype: None
        """
        # TODO: Force update of _item_inventory_size if the player upgrades its size
        if self.item_inventory_size is None:
           self.item_inventory_size = self.bot.api.get_player()['responses']['GET_PLAYER']['player_data']['max_item_storage']


#
# Other

# STAB (Same-type attack bonus)
# Factor applied to attack of the same type as pokemon
STAB_FACTOR = 1.25
# Factor applied to attack when it's effective against defending pokemon type
EFFECTIVENESS_FACTOR = 1.25
# Factor applied to attack when it's weak against defending pokemon type
RESISTANCE_FACTOR = 0.8


_inventory = None  # type: Inventory


def _calc_cp(base_attack, base_defense, base_stamina,
             iv_attack=15, iv_defense=15, iv_stamina=15,
             cp_multiplier=.0):
    """
    CP calculation

    CP = (Attack * Defense^0.5 * Stamina^0.5 * CP_Multiplier^2) / 10
    CP = (BaseAtk+AtkIV) * (BaseDef+DefIV)^0.5 * (BaseStam+StamIV)^0.5 * Lvl(CPScalar)^2 / 10

    See https://www.reddit.com/r/TheSilphRoad/comments/4t7r4d/exact_pokemon_cp_formula/
    See https://www.reddit.com/r/pokemongodev/comments/4t7xb4/exact_cp_formula_from_stats_and_cpm_and_an_update/
    See http://pokemongo.gamepress.gg/pokemon-stats-advanced
    See http://pokemongo.gamepress.gg/cp-multiplier
    See http://gaming.stackexchange.com/questions/280491/formula-to-calculate-pokemon-go-cp-and-hp

    :param base_attack:   Pokemon BaseAttack
    :param base_defense:  Pokemon BaseDefense
    :param base_stamina:  Pokemon BaseStamina
    :param iv_attack:     Pokemon IndividualAttack (0..15)
    :param iv_defense:    Pokemon IndividualDefense (0..15)
    :param iv_stamina:    Pokemon IndividualStamina (0..15)
    :param cp_multiplier: CP Multiplier (0.79030001 is max - value for level 40)
    :return: CP as float
    """
    assert base_attack > 0
    assert base_defense > 0
    assert base_stamina > 0

    if cp_multiplier <= .0:
        cp_multiplier = LevelToCPm.MAX_CPM
        assert cp_multiplier > .0

    return (base_attack + iv_attack) \
        * ((base_defense + iv_defense)**0.5) \
        * ((base_stamina + iv_stamina)**0.5) \
        * (cp_multiplier ** 2) / 10


# Initialize static data in the right order
Types()  # init Types
LevelToCPm()  # init LevelToCPm
FastAttacks()  # init FastAttacks
ChargedAttacks()  # init ChargedAttacks
Pokemons()  # init Pokemons


#
# Usage helpers

def init_inventory(bot):
    global _inventory
    _inventory = Inventory(bot)


def refresh_inventory():
    _inventory.refresh()


def get_item_inventory_size():
    _inventory.retrieve_item_inventory_size()
    return _inventory.item_inventory_size


def pokedex():
    return _inventory.pokedex


def candies(refresh=False):
    if refresh:
        refresh_inventory()
    return _inventory.candy


def pokemons(refresh=False):
    if refresh:
        refresh_inventory()
    return _inventory.pokemons


def items():
    return _inventory.items


def types_data():
    return Types


def levels_to_cpm():
    return LevelToCPm


def fast_attacks():
    return FastAttacks


def charged_attacks():
    return ChargedAttacks
