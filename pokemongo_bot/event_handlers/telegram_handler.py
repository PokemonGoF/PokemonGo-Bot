# -*- coding: utf-8 -*-
from pokemongo_bot.event_manager import EventHandler
import thread

DEBUG_ON = False

class TelegramHandler(EventHandler):
    def __init__(self, tbot,master,pokemons):
        self.tbot = tbot
        self.master=master
        self.pokemons=pokemons

    def handle_event(self, event, sender, level, formatted_msg, data):
        if self.master:
            if event == 'level_up':
                self.tbot.sendMessage(chat_id=self.master, parse_mode='Markdown', text="level up ({})".format(data["current_level"]))
            elif event == 'pokemon_caught':
                if data["pokemon"] in self.pokemons or self.pokemons[0]=="all":
                    self.tbot.sendMessage(chat_id=self.master, parse_mode='Markdown', 
                      text="Caught {} CP: {}, IV: {}".format(data["pokemon"],data["cp"],data["iv"])
                    )


