# -*- coding: utf-8 -*-

from catch_lured_pokemon_worker import CatchLuredPokemonWorker
from catch_visible_pokemon_worker import CatchVisiblePokemonWorker
from evolve_all_worker import EvolveAllWorker
from incubate_eggs_worker import IncubateEggsWorker
from move_to_fort_worker import MoveToFortWorker
from pokemon_catch_worker import PokemonCatchWorker
from pokemon_transfer_worker import PokemonTransferWorker
from recycle_items_worker import RecycleItemsWorker
from seen_fort_worker import SeenFortWorker
from soft_ban_worker import SoftBanWorker


FORT_CACHE = {}

def fort_details(bot, fort_id, latitude, longitude):
    """
    Lookup fort metadata and (if possible) serve from cache.
    """

    if fort_id not in FORT_CACHE:
        """
        Lookup the fort details and cache the response for future use.
        """
        bot.api.fort_details(fort_id=fort_id, latitude=latitude, longitude=longitude)

        try:
            response_dict = bot.api.call()
            FORT_CACHE[fort_id] = response_dict['responses']['FORT_DETAILS']
        except Exception:
            pass

    # Just to avoid KeyErrors
    return FORT_CACHE.get(fort_id, {})
