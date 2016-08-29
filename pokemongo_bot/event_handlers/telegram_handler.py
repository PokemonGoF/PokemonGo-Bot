# -*- coding: utf-8 -*-
from pokemongo_bot.event_manager import EventHandler
import thread
import re

DEBUG_ON = False

class TelegramHandler(EventHandler):
    def __init__(self, tbot,master,pokemons):
        self.tbot = tbot
        self.master=master
        self.pokemons=pokemons
        self.whoami="TelegramHandler"

    def handle_event(self, event, sender, level, formatted_msg, data):
        if self.master:
            if not re.match(r'^[0-9]+$', str(self.master)):
                return
            master = self.master

            if event == 'level_up':
                msg = "level up ({})".format(data["current_level"])
            elif event == 'pokemon_caught':
                if isinstance(self.pokemons, list):
                    if data["pokemon"] in self.pokemons or "all" in self.pokemons:
                        msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"],data["cp"],data["iv"])
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
                        msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"],data["cp"],data["iv"])
                    else:
                        return
            else:
                return
            self.tbot.sendMessage(chat_id=master, parse_mode='Markdown', text=msg)


