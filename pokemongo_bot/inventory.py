import json
import os

'''
Helper class for updating/retrieving Inventory data
'''

class _BaseInventoryComponent(object):
    TYPE = None  # base key name for items of this type
    ID_FIELD = None  # identifier field for items of this type
    STATIC_DATA_FILE = None  # optionally load static data from file,
                             # dropping the data in a static variable named STATIC_DATA

    def __init__(self):
        self._data = {}
        if self.STATIC_DATA_FILE is not None:
            self.init_static_data()

    @classmethod
    def init_static_data(cls):
        if not hasattr(cls, 'STATIC_DATA') or cls.STATIC_DATA is None:
            cls.STATIC_DATA = json.load(open(cls.STATIC_DATA_FILE))

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

    def get(self, id):
        return self._data(id)

    def all(self):
        return list(self._data.values())


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

class Candies(_BaseInventoryComponent):
    TYPE = 'candy'
    ID_FIELD = 'family_id'

    @classmethod
    def family_id_for(self, pokemon_id):
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
    STATIC_DATA_FILE = os.path.join('data', 'items.json')

    def count_for(self, item_id):
        return self._data[item_id].get('count', False)


class Pokemons(_BaseInventoryComponent):
    TYPE = 'pokemon_data'
    ID_FIELD = 'id'
    STATIC_DATA_FILE = os.path.join('data', 'pokemon.json')

    def parse(self, item):
        if 'is_egg' in item:
            return Egg(item)
        return Pokemon(item)

    @classmethod
    def data_for(cls, pokemon_id):
        return cls.STATIC_DATA[pokemon_id - 1]

    @classmethod
    def name_for(cls, pokemon_id):
        return cls.data_for(pokemon_id)['Name']

    @classmethod
    def first_evolution_id_for(cls, pokemon_id):
        data = cls.data_for(pokemon_id)
        if 'Previous evolution(s)' in data:
            return int(data['Previous evolution(s)'][0]['Number'])
        return pokemon_id

    @classmethod
    def next_evolution_id_for(cls, pokemon_id):
        try:
            return int(cls.data_for(pokemon_id)['Next evolution(s)'][0]['Number'])
        except KeyError:
            return None

    @classmethod
    def evolution_cost_for(cls, pokemon_id):
        try:
            return int(cls.data_for(pokemon_id)['Next Evolution Requirements']['Amount'])
        except KeyError:
            return

    def all(self):
        # by default don't include eggs in all pokemon (usually just
        # makes caller's lives more difficult)
        return [p for p in super(Pokemons, self).all() if not isinstance(p, Egg)]

class Egg(object):
    def __init__(self, data):
        self._data = data

    def has_next_evolution(self):
        return False


class Pokemon(object):
    def __init__(self, data):
        self._data = data
        self.id = data['id']
        self.pokemon_id = data['pokemon_id']
        self.cp = data['cp']
        self._static_data = Pokemons.data_for(self.pokemon_id)
        self.name = Pokemons.name_for(self.pokemon_id)
        self.iv = self._compute_iv()

    def can_evolve_now(self):
        return self.has_next_evolution and self.candy_quantity > self.evolution_cost

    def has_next_evolution(self):
        return 'Next Evolution Requirements' in self._static_data

    def has_seen_next_evolution(self):
        return pokedex().captured(self.next_evolution_id)

    @property
    def next_evolution_id(self):
        return Pokemons.next_evolution_id_for(self.pokemon_id)

    @property
    def first_evolution_id(self):
        return Pokemons.first_evolution_id_for(self.pokemon_id)

    @property
    def candy_quantity(self):
        return candies().get(self.pokemon_id).quantity

    @property
    def evolution_cost(self):
        return self._static_data['Next Evolution Requirements']['Amount']

    def _compute_iv(self):
        total_IV = 0.0
        iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']

        for individual_stat in iv_stats:
            try:
                total_IV += self._data[individual_stat]
            except Exception:
                self._data[individual_stat] = 0
                continue
        pokemon_potential = round((total_IV / 45.0), 2)
        return pokemon_potential


class Inventory(object):
    def __init__(self, bot):
        self.bot = bot
        self.pokedex = Pokedex()
        self.candy = Candies()
        self.items = Items()
        self.pokemons = Pokemons()
        self.refresh()

    def refresh(self):
        # TODO: it would be better if this class was used for all
        # inventory management. For now, I'm just clearing the old inventory field
        self.bot.latest_inventory = None
        inventory = self.bot.get_inventory()['responses']['GET_INVENTORY'][
            'inventory_delta']['inventory_items']
        for i in (self.pokedex, self.candy, self.items, self.pokemons):
            i.refresh(inventory)


_inventory = None

def init_inventory(bot):
    global _inventory
    _inventory = Inventory(bot)


def refresh_inventory():
    _inventory.refresh()


def pokedex():
    return _inventory.pokedex


def candies(refresh=False):
    if refresh:
        refresh_inventory()
    return _inventory.candy


def pokemons():
    return _inventory.pokemons


def items():
    return _inventory.items
