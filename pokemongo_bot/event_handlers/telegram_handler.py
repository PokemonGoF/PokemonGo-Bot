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
                if data["pokemon"] in self.pokemons or self.pokemons[0]=="all":
                    msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"],data["cp"],data["iv"])
                else:
                    return
            else:
                return
            self.tbot.sendMessage(chat_id=master, parse_mode='Markdown', text=msg)


