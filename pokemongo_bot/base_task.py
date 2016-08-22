import logging
from pokemongo_bot import inventory
from pokemongo_bot.inventory import Pokemon

ITEM_POKEBALL = 1
ITEM_GREATBALL = 2
ITEM_ULTRABALL = 3

LOGIC_TO_FUNCTION = {
    'or': lambda x, y, z: x or y or z,
    'and': lambda x, y, z: x and y and z,
    'orand': lambda x, y, z: x or y and z,
    'andor': lambda x, y, z: x and y or z
}

ENOUGH_POKEBALL_FOR_ALL = 1
ENOUGH_POKEBALL_FOR_VIP = 2
NOT_ENOUGH_POKEBALL = 3

class BaseTask(object):
  TASK_API_VERSION = 1

  def __init__(self, bot, config):
    """

    :param bot:
    :type bot: pokemongo_bot.PokemonGoBot
    :param config:
    :return:
    """
    self.bot = bot
    self.config = config
    self._validate_work_exists()
    self.logger = logging.getLogger(type(self).__name__)
    self.enabled = config.get('enabled', True)
    self.initialize()

  def _validate_work_exists(self):
    method = getattr(self, 'work', None)
    if not method or not callable(method):
      raise NotImplementedError('Missing "work" method')

  def emit_event(self, event, sender=None, level='info', formatted='', data={}):
    if not sender:
      sender=self
    self.bot.event_manager.emit(
      event,
      sender=sender,
      level=level,
      formatted=formatted,
      data=data
    )

  def initialize(self):
    pass


  def _is_vip_pokemon(self, pokemon):
    # having just a name present in the list makes them vip
    if self.bot.config.vips.get(pokemon.name) == {}:
      return True
    return self._pokemon_matches_config(self.bot.config.vips, pokemon, default_logic='or')

  def _pokemon_matches_config(self, config, pokemon, default_logic='and'):
    pokemon_config = config.get(pokemon.name, config.get('any'))

    if not pokemon_config:
      return False

    catch_results = {
      'ncp': False,
      'cp': False,
      'iv': False,
    }

    if pokemon_config.get('never_catch', False):
      return False

    if pokemon_config.get('always_catch', False):
      return True

    catch_ncp = pokemon_config.get('catch_above_ncp', 0.8)
    if pokemon.cp_percent > catch_ncp:
      catch_results['ncp'] = True

    catch_cp = pokemon_config.get('catch_above_cp', 1200)
    if pokemon.cp > catch_cp:
      catch_results['cp'] = True

    catch_iv = pokemon_config.get('catch_above_iv', 0.8)
    if pokemon.iv > catch_iv:
      catch_results['iv'] = True

    return LOGIC_TO_FUNCTION[pokemon_config.get('logic', default_logic)](*catch_results.values())

  def _check_enough_pokeball(self):
    self.min_ultraball_to_keep = self.config.get('min_ultraball_to_keep', 10)
    if inventory.items().get(ITEM_POKEBALL).count == 0:
      if inventory.items().get(ITEM_GREATBALL).count == 0:
        if inventory.items().get(ITEM_ULTRABALL).count == 0:
          return NOT_ENOUGH_POKEBALL
        elif inventory.items().get(ITEM_ULTRABALL).count <= self.min_ultraball_to_keep:
          return ENOUGH_POKEBALL_FOR_VIP
    return ENOUGH_POKEBALL_FOR_ALL
