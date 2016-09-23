# -*- coding: utf-8 -*-
from pokemongo_bot.event_manager import EventHandler
from pokemongo_bot.base_dir import _base_dir
import json
import os
import time
import discord_simple
import thread
import re
from pokemongo_bot.datastore import Datastore
from pokemongo_bot import inventory
from chat_handler import ChatHandler
import pprint


DEBUG_ON = False

class FileIOException(Exception):
    pass

class DiscordClass:

    def __init__(self, bot, master, pokemons, config):
        self.bot = bot
        self.pokemons = pokemons
        self._dbot = None
        self.config = config

    def sendMessage(self, to=None, text=None):
        self._dbot.send_message(to, text)

    def connect(self):
        self._dbot = discord_simple.Bot(self.bot.config.discord_token,on_message=self.on_message)

    def _get_player_stats(self):
        json_inventory = inventory.jsonify_inventory()
        return next((x["inventory_item_data"]["player_stats"]
                     for x in json_inventory
                     if x.get("inventory_item_data", {}).get("player_stats", {})),
                    None)

    def send_player_stats_to_chat(self, chat_id):
        stats = self.chat_handler.get_player_stats()
        if stats:
            self.sendMessage(to=chat_id, text="\n".join(stats))
        else:
            self.sendMessage(to=chat_id, text="Stats not loaded yet\n")

    def on_message(self,message):
        if message.content == "/help":
            res = (
                "Commands: ",
                "/info - info about bot"
            )
            self.sendMessage(to=str(message.author), text="\n".join(res))
        elif message.content == "/info":
            self.send_player_stats_to_chat(message.author)

    def run(self):
      self._dbot.forever_loop()

class DiscordHandler(EventHandler):
    def __init__(self, bot, config):
        self.bot = bot
        self.dbot = None
        self.master = config.get('master', None)
        if self.master == None:
            return
        self.pokemons = config.get('alert_catch', {})
        self.whoami = "DiscordHandler"
        self.config = config
        self.chat_handler = ChatHandler(self.bot, [])
    def catch_notify(self, pokemon, cp, iv, params):
        if params == " ":
            return True
        try:
            oper = re.search(r'operator:([^ ]+)', params).group(1)
            rule_cp = int(re.search(r'cp:([0-9]+)', params).group(1))
            rule_iv = float(re.search(r'iv:([0-9.]+)', params).group(1))
            rule_pkmn = re.search(r'pokemon:([^ ]+)', params).group(1)
            return rule_pkmn == pokemon and (oper == "or" and (cp >= rule_cp or iv >= rule_iv) or cp >= rule_cp and iv >= rule_iv)
        except:
            return False

    def handle_event(self, event, sender, level, formatted_msg, data):
        if self.dbot is None:
            try:
                self.bot.logger.info("Discord bot not running, Starting..")
                self.dbot = DiscordClass(self.bot, self.master, self.pokemons, self.config)
                self.dbot.connect()
                thread.start_new_thread(self.dbot.run)
            except Exception as inst:
                self.dbot = None
                self.bot.logger.error("Unable to start Discord bot; master: {}, exception: {}".format(self.master, pprint.pformat(inst)))
                return
        # prepare message to send
        msg = None
        msg = self.chat_handler.get_event(event, formatted_msg, data)
        if msg:
            self.dbot.sendMessage(to=self.master, text=msg)