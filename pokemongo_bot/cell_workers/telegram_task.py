# -*- coding: utf-8 -*-
import telegram
import os
import logging
import json
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.event_handlers import TelegramHandler

from pprint import pprint
import re

class TelegramTask(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1
    update_id = None
    tbot = None

    def initialize(self):
        if not self.enabled:
            return
        self.logger = logging.getLogger(type(self).__name__)
        api_key = self.bot.config.telegram_token
        if api_key == None:
            self.emit_event(
                'config_error',
                formatted='api_key not defined.'
            )
            return
        self.tbot = telegram.Bot(api_key)
        if self.config.get('master',None):
            self.bot.event_manager.add_handler(TelegramHandler(self.tbot,self.config.get('master',None),self.config.get('alert_catch')))
        try:
            self.update_id = self.tbot.getUpdates()[0].update_id
        except IndexError:
            self.update_id = None

    def work(self):
        if not self.enabled:
            return
        for update in self.tbot.getUpdates(offset=self.update_id, timeout=10):
            self.update_id = update.update_id+1
            if update.message:
                self.logger.info("message from {} ({}): {}".format(update.message.from_user.username, update.message.from_user.id, update.message.text))
                if self.config.get('master',None) and self.config.get('master',None) not in [update.message.from_user.id, "@{}".format(update.message.from_user.username)]:
                    self.emit_event( 
                            'debug', 
                            formatted="Master wrong: expecting {}, got {}({})".format(self.config.get('master',None), update.message.from_user.username, update.message.from_user.id))
                    continue
                else:
                    if not re.match(r'^[0-9]+$', "{}".format(self.config['master'])): # master was not numeric...
                        self.config['master'] = update.message.chat_id
                        idx = (i for i,v in enumerate(self.bot.event_manager._handlers) if type(v) is TelegramHandler).next()
                        self.bot.event_manager._handlers[idx] = TelegramHandler(self.tbot,self.config['master'], self.config.get('alert_catch'))
                        


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
                                "_KM Walked:_ "+str(stats["km_walked"])
                            )
                            self.tbot.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="\n".join(res))
                            self.tbot.send_location(chat_id=update.message.chat_id, latitude=self.bot.api._position_lat, longitude=self.bot.api._position_lng)
                    else:
                        self.tbot.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Stats not loaded yet\n")
                elif update.message.text == "/start" or update.message.text == "/help":
                    res = (
                        "Commands: ",
                        "/info - info about bot"
                    )
                    self.tbot.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="\n".join(res))

    def _get_player_stats(self):
        """
        Helper method parsing the bot inventory object and returning the player stats object.
        :return: The player stats object.
        :rtype: dict
        """
        web_inventory = os.path.join(_base_dir, "web", "inventory-%s.json" % self.bot.config.username)
        with open(web_inventory, "r") as infile:
            json_inventory = json.load(infile)
            infile.close()
        return next((x["inventory_item_data"]["player_stats"]
                     for x in json_inventory
                     if x.get("inventory_item_data", {}).get("player_stats", {})),
                    None)
