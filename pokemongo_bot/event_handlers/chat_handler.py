# -*- coding: utf-8 -*-
from pokemongo_bot import inventory
import re
import telegram
import time
DEBUG_ON = False


class ChatHandler:
    def __init__(self, bot, pokemons):
        self.bot = bot
        self.pokemons = pokemons
        self._tbot = telegram.Bot(self.bot.config.telegram_token)

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
            cur.execute("SELECT * FROM catch_log DESC LIMIT " + str(num))
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

    def get_event(self, event, formatted_msg, data):
        msg = None
        if event == 'level_up':
            msg = "level up ({})".format(data["current_level"])
        elif event == 'pokemon_caught':
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
        elif event == 'egg_hatched':
            msg = "Egg hatched with a {} CP: {}, IV: {} (A/D/S {})".format(data["name"], data["cp"], data["iv_pct"],
                                                                           data["iv_ads"])
        elif event == 'bot_sleep':
            msg = "I am too tired, I will take a sleep till {}.".format(data["wake"])
        elif event == 'catch_limit':
            msg = "*You have reached your daily catch limit, quitting.*"
        elif event == 'spin_limit':
            msg = "*You have reached your daily spin limit, quitting.*"
        else:
            return formatted_msg

        return msg
