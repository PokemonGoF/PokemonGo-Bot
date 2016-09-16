# -*- coding: utf-8 -*-
import re
from pokemongo_bot import inventory

DEBUG_ON = False


class ChatHandler:
    def __init__(self, bot, pokemons):
        self.bot = bot
        self.pokemons = pokemons

    def get_player_stats(self):
        stats = inventory.player().player_stats
        if stats:
            with self.bot.database as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT DISTINCT COUNT(encounter_id) FROM catch_log WHERE dated >= datetime('now','-1 day')")
                catch_day = cur.fetchone()[0]
                cur.execute("SELECT DISTINCT COUNT(pokestop) FROM pokestop_log WHERE dated >= datetime('now','-1 day')")
                ps_day = cur.fetchone()[0]
                res = (
                    "*" + self.bot.config.username + "*",
                    "_Level:_ " + str(stats["level"]),
                    "_XP:_ " + str(stats["experience"]) + "/" + str(stats["next_level_xp"]),
                    "_Pokemons Captured:_ " + str(stats["pokemons_captured"]) + " (" + str(catch_day) + " _last 24h_)",
                    "_Poke Stop Visits:_ " + str(stats["poke_stop_visits"]) + " (" + str(ps_day) + " _last 24h_)",
                    "_KM Walked:_ " + str("%.2f" % stats["km_walked"])
                )
            return (res)
        else:
            return ("Stats not loaded yet\n")

    def get_event(self, event, formatted_msg, data):
        if event == 'level_up':
            msg = "level up ({})".format(data["current_level"])
        elif event == 'pokemon_caught':
            if isinstance(self.pokemons, list):  # alert_catch is a plain list
                if data["pokemon"] in self.pokemons or "all" in self.pokemons:
                    msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"], data["cp"], data["iv"])
                else:
                    return "Catch error 1"
            else:  # alert_catch is a dict
                if data["pokemon"] in self.pokemons:
                    trigger = self.pokemons[data["pokemon"]]
                elif "all" in self.pokemons:
                    trigger = self.pokemons["all"]
                else:
                    return
                if (not "operator" in trigger or trigger["operator"] == "and") and data["cp"] >= trigger["cp"] and data[
                    "iv"] >= trigger["iv"] or ("operator" in trigger and trigger["operator"] == "or" and (
                        data["cp"] >= trigger["cp"] or data["iv"] >= trigger["iv"])):
                    msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"], data["cp"], data["iv"])
                else:
                    return "Catch error 2"
        elif event == 'egg_hatched':
            msg = "Egg hatched with a {} CP: {}, IV: {} {}".format(data["name"], data["cp"], data["iv_ads"],
                                                                   data["iv_pct"])
        elif event == 'bot_sleep':
            msg = "I am too tired, I will take a sleep till {}.".format(data["wake"])
        elif event == 'catch_limit':
            msg = "*You have reached your daily catch limit, quitting.*"
        elif event == 'spin_limit':
            msg = "*You have reached your daily spin limit, quitting.*"
        else:
            return formatted_msg

        return msg

    def display_events(self, update):
        cmd = update.message.text.split(" ", 1)
        if len(cmd) > 1:
            # we have a filter
            event_filter = ".*{}-*".format(cmd[1])
        else:
            # no filter
            event_filter = ".*"
        events = filter(lambda k: re.match(event_filter, k), self.bot.event_manager._registered_events.keys())
        events.remove('vanish_log')
        events.remove('eggs_hatched_log')
        events.remove('catch_log')
        events.remove('pokestop_log')
        events.remove('load_cached_location')
        events.remove('location_cache_ignored')
        events.remove('softban_log')
        events.remove('loaded_cached_forts')
        events.remove('login_log')
        events.remove('evolve_log')
        events.remove('transfer_log')
        events.remove('catchable_pokemon')
        return "\n".join(events)


    def showtop(self, chatid, num, order):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        if order not in ["cp", "iv"]:
            order = "iv"

        pkmns = sorted(inventory.pokemons().all(), key=lambda p: getattr(p, order), reverse=True)[:num]

        outMsg = "\n".join(["{} CP:{} IV:{} ID:{} Candy:{}".format(p.name, p.cp, p.iv, p.unique_id,
                                                                   inventory.candies().get(p.pokemon_id).quantity) for p
                            in pkmns])
        return outMsg

    def evolve(self, chatid, uid):
        # TODO: here comes evolve logic (later)
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Evolve logic not implemented yet")
        return

    def upgrade(self, chatid, uid):
        # TODO: here comes upgrade logic (later)
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Upgrade logic not implemented yet")
        return
