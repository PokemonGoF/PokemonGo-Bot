# -*- coding: utf-8 -*-
import re
from pokemongo_bot import inventory

DEBUG_ON = False


class ChatHandler:
    def __init__(self, bot, pokemons):
        self.bot = bot
        self.pokemons = pokemons

    def get_evolved(self, num, order):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        if order not in ["cp", "iv"]:
            order = "iv"

        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM catch_log ORDER BY " + order + " DESC LIMIT " + str(num))
            evolved = cur.fetchall()
            return evolved

    def get_softbans(self, num):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM softban_log DESC LIMIT " + str(num))
            softbans = cur.fetchall()
            return softbans

    def get_hatched(self, num, order):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        if order not in ["cp", "iv"]:
            order = "iv"

        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM eggs_hatched_log ORDER BY " + order + " DESC LIMIT " + str(num))
            hatched = cur.fetchall()
            return hatched

    def get_caught(self, num, order):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        if order not in ["cp", "iv"]:
            order = "iv"

        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM catch_log ORDER BY " + order + " DESC LIMIT " + str(num))
            caught = cur.fetchall()
            return caught

    def get_pokestops(self, num):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pokestop_log DESC LIMIT " + str(num))
            pokestops = cur.fetchall()
            return pokestops

    def get_released(self, num, order):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        if order not in ["cp", "iv"]:
            order = "iv"

        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM transfer_log ORDER BY " + order + " DESC LIMIT " + str(num))
            released = cur.fetchall()
            return released

    def get_vanished(self, num, order):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        if order not in ["cp", "iv"]:
            order = "iv"

        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM vanish_log ORDER BY " + order + " DESC LIMIT " + str(num))
            vanished = cur.fetchall()
            return vanished

    def get_player_stats(self):
        stats = inventory.player().player_stats
        if stats:
            with self.bot.database as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT COUNT(DISTINCT encounter_id) FROM catch_log WHERE dated >= datetime('now','-1 day')")
                catch_day = cur.fetchone()[0]
                cur.execute("SELECT COUNT(pokestop) FROM pokestop_log WHERE dated >= datetime('now','-1 day')")
                ps_day = cur.fetchone()[0]
                res = (
                    self.bot.config.username,
                    str(stats["level"]),
                    str(stats["experience"]),
                    str(stats["next_level_xp"]),
                    str(stats["pokemons_captured"]),
                    str(catch_day),
                    str(stats["poke_stop_visits"]),
                    str(ps_day),
                    str("%.2f" % stats["km_walked"])
                )
            return (res)

    def get_events(self, update):
        cmd = update.message.text.split(" ", 1)
        if len(cmd) > 1:
            # we have a filter
            event_filter = ".*{}-*".format(cmd[1])
        else:
            # no filter
            event_filter = ".*"
        events = filter(lambda k: re.match(event_filter, k), self.bot.event_manager._registered_events.keys())
        events = sorted(events)
        return events

    def get_event(self, event, formatted_msg, data):
        msg = None
        if event == 'level_up':
            msg = "level up ({})".format(data["current_level"])
        if event == 'pokemon_caught':
            trigger = None
            if data["pokemon"] in self.pokemons:
                trigger = self.pokemons[data["pokemon"]]
            elif "all" in self.pokemons:
                trigger = self.pokemons["all"]
            if trigger:
                if ((not "operator" in trigger or trigger["operator"] == "and") and data["cp"] >= trigger["cp"] and
                            data["iv"] >= trigger["iv"]) or \
                        ("operator" in trigger and trigger["operator"] == "or" and (
                                data["cp"] >= trigger["cp"] or data["iv"] >= trigger["iv"])):
                    msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"], data["cp"], data["iv"])
        if event == 'egg_hatched':
            msg = "Egg hatched with a {} CP: {}, IV: {} (A/D/S {})".format(data["name"], data["cp"], data["iv_pct"],
                                                                           data["iv_ads"])
        if event == 'bot_sleep':
            msg = "I am too tired, I will take a sleep till {}.".format(data["wake"])
        if event == 'catch_limit':
            msg = "*You have reached your daily catch limit, quitting.*"
        if event == 'spin_limit':
            msg = "*You have reached your daily spin limit, quitting.*"
        if msg == None:
            return formatted_msg
        else:
            return msg
