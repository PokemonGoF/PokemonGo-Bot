# -*- coding: utf-8 -*-
from pokemongo_bot.event_manager import EventHandler
from pokemongo_bot.base_dir import _base_dir
import json
import os
import time
import telegram
import thread
import re

DEBUG_ON = False

class FileIOException(Exception):
    pass

class TelegramClass:

    update_id = None

    def __init__(self, bot, master, pokemons):
        self.bot = bot
        self.master = master
        self.pokemons = pokemons
        self._tbot = None

    def sendMessage(self, chat_id=None, parse_mode='Markdown', text=None):
        self._tbot.sendMessage(chat_id=chat_id, parse_mode=parse_mode, text=text)

    def connect(self):
        self._tbot = telegram.Bot(self.bot.config.telegram_token)
        try:
            self.update_id = self._tbot.getUpdates()[0].update_id
        except IndexError:
            self.update_id = None

    def _get_player_stats(self):
        web_inventory = os.path.join(_base_dir, "web", "inventory-%s.json" % self.bot.config.username)
        try:
            with open(web_inventory, "r") as infile:
                json_inventory = json.load(infile)
        except ValueError as exception:
            self.bot.logger.info('[x] Error while opening inventory file for read: %s' % exception)
            json_inventory = []
        except:
            raise FileIOException("Unexpected error reading from {}".format(web_inventory))
        return next((x["inventory_item_data"]["player_stats"]
                for x in json_inventory
                if x.get("inventory_item_data", {}).get("player_stats", {})),
            None)

    def run(self):
        time.sleep(1)
        while True:
            try:
                for update in self._tbot.getUpdates(offset=self.update_id, timeout=10):
                    self.update_id = update.update_id+1
                    if update.message:
                        self.bot.logger.info("message from {} ({}): {}".format(update.message.from_user.username, update.message.from_user.id, update.message.text))
                        if self.master and self.master not in [update.message.from_user.id, "@{}".format(update.message.from_user.username)]:
                            continue
                        if update.message.text == "/info":
                            stats = self._get_player_stats()
                            if stats:
                                with self.bot.database as conn:
                                    cur = conn.cursor()
                                    cur.execute("SELECT DISTINCT COUNT(encounter_id) FROM catch_log WHERE dated >= datetime('now','-1 day')")
                                    catch_day = cur.fetchone()[0]
                                    cur.execute("SELECT DISTINCT COUNT(pokestop) FROM pokestop_log WHERE dated >= datetime('now','-1 day')")
                                    ps_day = cur.fetchone()[0]
                                    res = (
                                        "*"+self.bot.config.username+"*",
                                        "_Level:_ "+str(stats["level"]),
                                        "_XP:_ "+str(stats["experience"])+"/"+str(stats["next_level_xp"]),
                                        "_Pokemons Captured:_ "+str(stats["pokemons_captured"])+" ("+str(catch_day)+" _last 24h_)",
                                        "_Poke Stop Visits:_ "+str(stats["poke_stop_visits"])+" ("+str(ps_day)+" _last 24h_)",
                                        "_KM Walked:_ "+str("%.2f" % stats["km_walked"])
                                    )
                                self._tbot.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="\n".join(res))
                                self._tbot.send_location(chat_id=update.message.chat_id, latitude=self.bot.api._position_lat, longitude=self.bot.api._position_lng)
                            else:
                                self._tbot.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Stats not loaded yet\n")
                        elif update.message.text == "/start" or update.message.text == "/help":
                            res = (
                                "Commands: ",
                                "/info - info about bot"
                            )
                            self._tbot.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="\n".join(res))
            except telegram.error.NetworkError:
                time.sleep(1)
            except telegram.error.Unauthorized:
                self.update_id += 1

class TelegramHandler(EventHandler):
    def __init__(self, bot, config):
        self.bot = bot
        self.tbot = None
        self.master = config.get('master', None)
        self.pokemons = config.get('alert_catch', {})
        self.whoami = "TelegramHandler"

    def handle_event(self, event, sender, level, formatted_msg, data):
        if self.tbot is None:
            try:
                self.tbot = TelegramClass(self.bot, self.master, self.pokemons)
                self.tbot.connect()
                thread.start_new_thread(self.tbot.run)
            except Exception as inst:
                self.tbot = None
        if self.master:
            if not re.match(r'^[0-9]+$', str(self.master)):
                return
            master = self.master

            if event == 'level_up':
                msg = "level up ({})".format(data["current_level"])
            elif event == 'pokemon_caught':
                if isinstance(self.pokemons, list):
                    if data["pokemon"] in self.pokemons or "all" in self.pokemons:
                        msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"], data["cp"], data["iv"])
                    else:
                        return
                else:
                    if data["pokemon"] in self.pokemons:
                        trigger = self.pokemons[data["pokemon"]]
                    elif "all" in self.pokemons:
                        trigger = self.pokemons["all"]
                    else:
                        return
                    if (not "operator" in trigger or trigger["operator"] == "and") and data["cp"] >= trigger["cp"] and data["iv"] >= trigger["iv"] or ("operator" in trigger and trigger["operator"] == "or" and (data["cp"] >= trigger["cp"] or data["iv"] >= trigger["iv"])):
                        msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"], data["cp"], data["iv"])
                    else:
                        return
            else:
                return
            self.tbot.sendMessage(chat_id=master, parse_mode='Markdown', text=msg)


