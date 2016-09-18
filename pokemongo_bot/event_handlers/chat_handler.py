# -*- coding: utf-8 -*-
import re
from pokemongo_bot import inventory
import telegram
import time
DEBUG_ON = False


class ChatHandler:
    def __init__(self, bot, pokemons):
        self.bot = bot
        self.pokemons = pokemons
        self._tbot = telegram.Bot(self.bot.config.telegram_token)

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

    def get_events(self, update):
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
        return events



    def sendMessage(self, chat_id=None, parse_mode='Markdown', text=None):
        try:
            self._tbot.sendMessage(chat_id=chat_id, parse_mode=parse_mode, text=text)
        except telegram.error.NetworkError:
            time.sleep(1)
        except telegram.error.TelegramError:
            time.sleep(10)
        except telegram.error.Unauthorized:
            self.update_id += 1

    def sendLocation(self, chat_id, latitude, longitude):
        try:
            self._tbot.send_location(chat_id=chat_id, latitude=latitude, longitude=longitude)
        except telegram.error.NetworkError:
            time.sleep(1)
        except telegram.error.TelegramError:
            time.sleep(10)
        except telegram.error.Unauthorized:
            self.update_id += 1

    def send_player_stats_to_chat(self, chat_id):
        stats = self.get_player_stats()
        if stats:
            self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="\n".join(stats))
            self.sendLocation(chat_id=chat_id, latitude=self.bot.api._position_lat, longitude=self.bot.api._position_lng)
        else:
            self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="Stats not loaded yet\n")

    def showtop(self, chatid, num, order):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        if order not in ["cp", "iv"]:
            order = "iv"

        pkmns = sorted(inventory.pokemons().all(), key=lambda p: getattr(p, order), reverse=True)[:num]

        outMsg = "\n".join(["*{}* \nCP:{} \nIV:{} \nCandy:{}\n".format(p.name, p.cp, p.iv,
                                                                   inventory.candies().get(p.pokemon_id).quantity) for p
                            in pkmns])
        self.sendMessage(chat_id=chatid, parse_mode='Markdown', text=outMsg)

    def evolve(self, chatid, uid):
        # TODO: here comes evolve logic (later)
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Evolve logic not implemented yet")
        return

    def upgrade(self, chatid, uid):
        # TODO: here comes upgrade logic (later)
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Upgrade logic not implemented yet")
        return
    def get_evolved(self, chat_id, num, order):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        if order not in ["cp", "iv"]:
            order = "iv"

        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM evolve_log ORDER BY " + order + " DESC LIMIT " + str(num))
            evolved = cur.fetchall()
            if evolved:
                for x in evolved:
                    res = (
                        "*"+str(x[0])+"*",
                        "_CP:_ " + str(x[2]),
                        "_IV:_ " + str(x[1]),
                        str(x[3])
                        )

                    self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="\n".join(res))
            else:
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="No Evolutions Found.\n")

    def get_softban(self, chat_id):
        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM softban_log")
            softban = cur.fetchall()
            if softban:
                for x in softban:
                    res = (
                        "*" + str(x[0]) + "*",
                        str(x[2]))
                    self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="\n".join(res))
            else:
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="No Softbans found! Good job!\n")

    def get_hatched(self, chat_id, num, order):
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
            if hatched:
                for x in hatched:
                    res = (
                        "*" + str(x[0]) + "*",
                        "_CP:_ " + str(x[1]),
                        "_IV:_ " + str(x[2]),
                        str(x[4])
                        )
                    self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="\n".join(res))
            else:
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="No Eggs Hatched Yet.\n")

    def get_caught(self, chat_id, num, order):
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
            if caught:
                for x in caught:
                    res = (
                        "*" + str(x[0]) + "*",
                        "_CP:_ " + str(x[1]),
                        "_IV:_ " + str(x[2]),
                        str(x[5])
                        )
                    self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="\n".join(res))
            else:
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="No Pokemon Caught Yet.\n")

    def get_pokestops(self, chat_id, num):
        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pokestop_log ORDER BY dated DESC LIMIT " + str(num))
            pokestop = cur.fetchall()
            if pokestop:
                for x in pokestop:
                    res = (
                        "*" + str(x[0] + "*"),
                        "_XP:_ " + str(x[1]),
                        "_Items:_ " + str(x[2]),
                        str(x[3])
                    )
                    self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="\n".join(res))
            else:
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="No Pokestops Encountered Yet.\n")

    def get_released(self, chat_id, num, order):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        if order not in ["cp", "iv"]:
            order = "iv"
        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM transfer_log ORDER BY " + order + " DESC LIMIT " + str(num))
            transfer = cur.fetchall()
            if transfer:
                for x in transfer:
                    res = (
                        "*" + str(x[0]) + "*",
                        "_CP:_ " + str(x[2]),
                        "_IV:_ " + str(x[1]),
                        str(x[3])
                    )
                    self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="\n".join(res))
            else:
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="No Pokemon Released Yet.\n")

    def get_vanished(self, chat_id, num, order):
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
            if vanished:
                for x in vanished:
                    res = (
                        "*" + str(x[0]) + "*",
                        "_CP:_ " + str(x[1]),
                        "_IV:_ " + str(x[2]),
                        "_NCP:_ " + str(x[4]),
                        str(x[5])
                    )
                    self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="\n".join(res))
            else:
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="No Pokemon Vanished Yet.\n")

        def evolve(self, chatid, uid):
            # TODO: here comes evolve logic (later)
            self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Evolve logic not implemented yet")
            return

        def upgrade(self, chatid, uid):
            # TODO: here comes upgrade logic (later)
            self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Upgrade logic not implemented yet")
            return