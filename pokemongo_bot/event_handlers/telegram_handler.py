# -*- coding: utf-8 -*-
from pokemongo_bot.event_manager import EventHandler
from pokemongo_bot.base_dir import _base_dir
import json
import os
import time
import telegram
import thread
import re
from pokemongo_bot.datastore import Datastore
import pprint


DEBUG_ON = False

class FileIOException(Exception):
    pass

class TelegramClass:

    update_id = None


    def __init__(self, bot, master, pokemons, config):
        self.bot = bot
        with self.bot.database as conn:
            # initialize the DB table if it does not exist yet
            initiator = TelegramDBInit(bot.database)

            if master == None: # no master supplied
                self.master = master
            # if master is not numeric, try to fetch it from the database
            elif unicode(master).isnumeric(): # master is numeric
                self.master = master
                self.bot.logger.info("Telegram master is valid (numeric): {}".format(master))
            else:
                self.bot.logger.info("Telegram master is not numeric: {}".format(master))
                c = conn.cursor()
                # do we already have a user id?
                srchmaster = re.sub(r'^@', '', master)
                c.execute("SELECT uid from telegram_uids where username in ('{}', '@{}')".format(srchmaster, srchmaster))
                results = c.fetchall()
                if len(results) > 0: # woohoo, we already saw a message from this master and therefore have a uid
                    self.bot.logger.info("Telegram master UID from datastore: {}".format(results[0][0]))
                    self.master = results[0][0]
                else: # uid not known yet
                    self.bot.logger.info("Telegram master UID not in datastore yet")
                    self.master = master

        self.pokemons = pokemons
        self._tbot = None
        self.config = config

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
    def send_player_stats_to_chat(self, chat_id):
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
            self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="\n".join(res))
            self.sendLocation(chat_id=chat_id, latitude=self.bot.api._position_lat, longitude=self.bot.api._position_lng)
        else:
            self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="Stats not loaded yet\n")
    def grab_uid(self, update):
        with self.bot.database as conn:
            conn.execute("replace into telegram_uids (uid, username) values (?, ?)", (update.message.chat_id, update.message.from_user.username))
            conn.commit()

    def isMasterFromConfigFile(self, chat_id):
        if not hasattr(self, "master") or not self.master:
            return False
        if unicode(self.master).isnumeric():
            return unicode(chat_id) == unicode(self.master)
        else:
            with self.bot.database as conn:
                cur = conn.cursor()
                cur.execute("select username from telegram_uids where uid = ?", [chat_id])
                res = cur.fetchone()
                return res != None and unicode(res[0]) == unicode(re.replace(r'^@', '', self.master))

    def isMasterFromActiveLogins(self, chat_id):
        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("select count(1) from telegram_logins where uid = ?", [chat_id])
            res = cur.fetchone()
            if res[0] == 1:
                return True
            else:
                return False

    def isAuthenticated(self, chat_id):
        return self.isMasterFromConfigFile(chat_id) or self.isMasterFromActiveLogins(chat_id)

    def deauthenticate(self, update):
        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("delete from telegram_logins where uid = ?", [update.message.chat_id])
            conn.commit()
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Logout completed")
        return

    def authenticate(self, update):
        (command, password) = update.message.text.split(' ')
        if password != self.config.get('password', None):
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Invalid password")
        else:
            with self.bot.database as conn:
                cur = conn.cursor()
                cur.execute("delete from telegram_logins where uid = ?", [update.message.chat_id])
                cur.execute("insert into telegram_logins(uid) values(?)", [update.message.chat_id])
                conn.commit()
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Authentication successful, you can now use all commands")
        return

    def run(self):
        time.sleep(1)
        while True:
            for update in self._tbot.getUpdates(offset=self.update_id, timeout=10):
                self.update_id = update.update_id+1
                if update.message:
                    self.bot.logger.info("Telegram message from {} ({}): {}".format(update.message.from_user.username, update.message.from_user.id, update.message.text))
                    if update.message.text == "/start" or update.message.text == "/help":
                        res = (
                            "Commands: ",
                            "/info - info about bot",
                            "/login <password> - authenticate with the bot; once authenticated, your ID will be registered with the bot and survive bot restarts",
                            "/logout - remove your ID from the 'authenticated' list",
                            "/sub <event_name> [<parameters>] - subscribe to event_name, with optional parameters, event name=all will subscribe to ALL events (LOTS of output!)",
                            "/unsub <event_name> [<parameters>] - unsubscribe from event_name; parameters must match the /sub parameters",
                            "/unsub everything - will remove all subscriptions for this uid",
                            "/showsubs - show current subscriptions",
                            "/events - show available events"
                        )
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="\n".join(res))
                        continue

                    if self.config.get('password', None) == None and (not hasattr(self, "master") or not self.master): # no auth provided in config
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="No password nor master configured in TelegramTask section, bot will not accept any commands")
                        continue
                    if re.match(r'^/login [^ ]+', update.message.text):
                        self.authenticate(update)
                        continue
                    if not self.isAuthenticated(update.message.from_user.id) and hasattr(self, "master") and self.master and not unicode(self.master).isnumeric() and unicode(self.master) == unicode(update.message.from_user.username):
                        outMessage = "Telegram message received from correct user, but master is not numeric, updating datastore."
                        self.bot.logger.warn(outMessage)
                        # the "master" is not numeric, set self.master to update.message.chat_id and re-instantiate the handler
                        newconfig = self.config
                        newconfig['master'] = update.message.chat_id
                        # insert chat id into database
                        self.grab_uid(update)
                        # remove old handler
                        self.bot.event_manager._handlers = filter(lambda x: not isinstance(x, TelegramHandler), self.bot.event_manager._handlers)
                        # add new handler (passing newconfig as parameter)
                        self.bot.event_manager.add_handler(TelegramHandler(self.bot, newconfig))
                        continue
                    if not self.isAuthenticated(update.message.from_user.id):
                        # Reject message if sender does not match defined master in config
                        outMessage = "Telegram message received from unknown sender. Please either make sure your username or ID is in TelegramTask/master, or a password is set in TelegramTask section and /login is issued"
                        self.bot.logger.error(outMessage)
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Please /login first")
                        continue
                    # one way or another, the user is now authenticated
                    if update.message.text == "/info":
                        self.send_player_stats_to_chat(update.message.chat_id)
                        continue
                    if update.message.text == "/events":
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML', text=(", ".join(self.bot.event_manager._registered_events.keys())))
                        continue
                    if update.message.text == "/logout":
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML', text=("Logged out."))
                        self.deauthenticate(update)
                        continue
                    if re.match(r'^/sub ', update.message.text):
                        self.chsub(update.message.text, update.message.chat_id)
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML', text=("Subscriptions updated."))
                        continue
                    if re.match(r'^/unsub ', update.message.text):
                        self.chsub(update.message.text, update.message.chat_id)
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML', text=("Subscriptions updated."))
                        continue
                    if re.match(r'^/showsubs', update.message.text):
                        self.showsubs(update.message.chat_id)
                        continue

                    self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Unrecognized command: {}".format(update.message.text))
    def showsubs(self, chatid):
        subs = []
        with self.bot.database as conn:
            for sub in conn.execute("select uid, event_type, parameters from telegram_subscriptions where uid = ?", [chatid]).fetchall():
                subs.append("{} -&gt; {}".format(sub[1], sub[2]))
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="\n".join(subs))

    def chsub(self, msg, chatid):
        (cmd, evt, params) = self.tokenize(msg, 3)
        if cmd == "/sub":
            sql = "replace into telegram_subscriptions(uid, event_type, parameters) values (?, ?, ?)"
        else:
            if evt == "everything":
                sql = "delete from telegram_subscriptions where uid = ? and (event_type = ? or parameters = ? or 1 = 1)" # does not look very elegant, but makes unsub'ing everythign possible
            else:
                sql = "delete from telegram_subscriptions where uid = ? and event_type = ? and parameters = ?"

        with self.bot.database as conn:
            conn.execute(sql, [chatid, evt, params])
            conn.commit()
        return

    def tokenize(self, string, maxnum):
        spl = string.split(' ', maxnum-1)
        while len(spl) < maxnum:
            spl.append(" ")
        return spl

class TelegramDBInit:
    def __init__(self, conn):
        self.conn = conn
        self.initDBstructure()
        return

    def initDBstructure(self):
        db_structure = {
                "telegram_uids": "CREATE TABLE telegram_uids(uid text constraint upk primary key, username text not null)",
                "tuids_username": "CREATE INDEX tuids_username on telegram_uids(username)",
                "telegram_logins": "CREATE TABLE telegram_logins(uid text constraint tlupk primary key, logindate integer(4) default (strftime('%s', 'now')))",
                "telegram_subscriptions": "CREATE TABLE telegram_subscriptions(uid text, event_type text, parameters text, constraint tspk primary key(uid, event_type, parameters))",
                "ts_uid": "CREATE INDEX ts_uid on telegram_subscriptions(uid)"
        }
        for objname in db_structure:
            self.initDBobject(objname, db_structure[objname])
        return

    def initDBobject(self, name, sql):
        res = self.conn.execute("select sql,type from sqlite_master where name = ?", [name]).fetchone() # grab objects definition

        if res and len(res) > 0 and res[0] != sql: # object exists and sql not matching
            self.conn.execute("drop {} {}".format(res[1], name)) # drop it

        if res is None or len(res) == 0 or res[0] != sql: # object missing or sql not matching
            self.conn.execute(sql)
        return


class TelegramHandler(EventHandler):
    def __init__(self, bot, config):
        initiator = TelegramDBInit(bot.database)
        self.bot = bot
        self.tbot = None
        master = config.get('master', None)
        self.pokemons = config.get('alert_catch', {})
        self.whoami = "TelegramHandler"
        self.config = config
        if master == None:
            self.master = None
            return

        with self.bot.database as conn:
            # if master is not numeric, try to fetch it from the database
            if not unicode(master).isnumeric():
                self.bot.logger.info("Telegram master is not numeric: {}".format(master))
                c = conn.cursor()
                # do we already have a user id?
                srchmaster = re.sub(r'^@', '', master)
                c.execute("SELECT uid from telegram_uids where username in ('{}', '@{}')".format(srchmaster, srchmaster))
                results = c.fetchall()
                if len(results) > 0: # woohoo, we already saw a message from this master and therefore have a uid
                    self.bot.logger.info("Telegram master UID from datastore: {}".format(results[0][0]))
                    self.master = results[0][0]
                else: # uid not known yet
                    self.bot.logger.info("Telegram master UID not in datastore yet")
                    self.master = master

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
        if self.tbot is None:
            try:
                if hasattr(self, "master"):
                    selfmaster = self.master
                else:
                    selfmaster = None
                self.bot.logger.info("Telegram bot not running, trying to spin it up")
                self.tbot = TelegramClass(self.bot, selfmaster, self.pokemons, self.config)
                self.tbot.connect()
                thread.start_new_thread(self.tbot.run)
            except Exception as inst:
                self.tbot = None
                self.bot.logger.error("Unable to spin Telegram bot; master: {}, exception: {}".format(selfmaster, pprint.pformat(inst)))
                return
        try:
            # prepare message to send
            if event == 'level_up':
                msg = "level up ({})".format(data["current_level"])
            elif event == 'pokemon_caught':
                msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"], data["cp"], data["iv"])
            elif event == 'egg_hatched':
                msg = "Egg hatched with a {} CP: {}, IV: {}".format(data["pokemon"], data["cp"], data["iv"])
            elif event == 'bot_sleep':
                msg = "I am too tired, I will take a sleep till {}.".format(data["wake"])
            elif event == 'catch_limit':
                msg = "*You have reached your daily catch limit, quitting.*"
            elif event == 'spin_limit':
                msg = "*You have reached your daily spin limit, quitting.*"
            else:
                msg = formatted_msg
        except KeyError:
            pass
        # first handle subscriptions; they are independent of master setting.
        with self.bot.database as conn:
            subs = conn.execute("select uid, parameters, event_type from telegram_subscriptions where event_type in (?,'all','debug')", [event]).fetchall()
            for sub in subs:
                (uid, params, event_type) = sub
                if event != 'pokemon_caught' or self.catch_notify(data["pokemon"], int(data["cp"]), float(data["iv"]), params):
                    if event_type == "debug":
                        self.bot.logger.info("[{}] {}".format(event, msg))
                    else:
                        self.tbot.sendMessage(chat_id=uid, parse_mode='Markdown', text=msg)



        if hasattr(self, "master") and self.master:
            if not unicode(self.master).isnumeric():
                # master not numeric?...
                # cannot send event notifications to non-numeric master (yet), so quitting
                return
            master = self.master

            if event == 'level_up':
                msg = "level up ({})".format(data["current_level"])
            elif event == 'pokemon_caught':
                if isinstance(self.pokemons, list): # alert_catch is a plain list
                    if data["pokemon"] in self.pokemons or "all" in self.pokemons:
                        msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"], data["cp"], data["iv"])
                    else:
                        return
                else: # alert_catch is a dict
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
            elif event == 'egg_hatched':
                try:
                    msg = "Egg hatched with a {} CP: {}, IV: {}".format(data["pokemon"], data["cp"], data["iv"])
                except KeyError:
                    return
            elif event == 'bot_sleep':
                msg = "I am too tired, I will take a sleep till {}.".format(data["wake"])
            elif event == 'catch_limit':
                self.tbot.send_player_stats_to_chat(master)
                msg = "*You have reached your daily catch limit, quitting.*"
            elif event == 'spin_limit':
                self.tbot.send_player_stats_to_chat(master)
                msg = "*You have reached your daily spin limit, quitting.*"
            else:
                return
            self.tbot.sendMessage(chat_id=master, parse_mode='Markdown', text=msg)
