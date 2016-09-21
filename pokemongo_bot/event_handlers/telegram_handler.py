# -*- coding: utf-8 -*-
from pokemongo_bot.event_manager import EventHandler
import telegram
import thread
import re
import time
import pprint
from telegram.utils import request
from chat_handler import ChatHandler


DEBUG_ON = False


class TelegramClass:
    update_id = None

    def __init__(self, bot, pokemons, config):
        self.bot = bot
        request.CON_POOL_SIZE = 16
        self.config = config
        self.chat_handler = ChatHandler(self.bot, pokemons)
        self.master = self.config.get('master')

        with self.bot.database as conn:
            # initialize the DB table if it does not exist yet
            initiator = TelegramDBInit(bot.database)
            if unicode(self.master).isnumeric():  # master is numeric
                self.bot.logger.info("Telegram master is valid (numeric): {}".format(self.master))
            elif self.master is not None:  # Master is not numeric, fetch from db
                self.bot.logger.info("Telegram master is not numeric: {}".format(self.master))
                c = conn.cursor()
                srchmaster = re.sub(r'^@', '', self.master)
                c.execute("SELECT uid from telegram_uids where username = '{}'".format(srchmaster))
                results = c.fetchall()
                if len(results) > 0:  # woohoo, we already saw a message from this master and therefore have a uid
                    self.bot.logger.info("Telegram master UID from datastore: {}".format(results[0][0]))
                    self.master = results[0][0]
                else:  # uid not known yet
                    self.bot.logger.info("Telegram master UID not in datastore yet")

        self.pokemons = pokemons
        self._tbot = None
        self.config = config
        self._tbot = telegram.Bot(self.bot.config.telegram_token)

    def connect(self):
        if DEBUG_ON: self.bot.logger.info("Not connected. Reconnecting")

        try:
            self.update_id = self._tbot.getUpdates()[0].update_id
        except IndexError:
            self.update_id = None

    def grab_uid(self, update):
        with self.bot.database as conn:
            conn.execute("replace into telegram_uids (uid, username) values (?, ?)",
                         (update.message.chat_id, update.message.from_user.username))
            conn.commit()
        self.master = update.message.chat_id

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
        args = update.message.text.split(' ')
        if len(args) != 2:
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Invalid password")
            return
        password = args[1]
        if password != self.config.get('password', None):
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Invalid password")
        else:
            with self.bot.database as conn:
                cur = conn.cursor()
                cur.execute("delete from telegram_logins where uid = ?", [update.message.chat_id])
                cur.execute("insert into telegram_logins(uid) values(?)", [update.message.chat_id])
                conn.commit()
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                             text="Authentication successful, you can now use all commands")
        return

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
        stats = self.chat_handler.get_player_stats()
        if stats:
            self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="\n".join(stats))
            self.sendLocation(chat_id=chat_id, latitude=self.bot.api._position_lat,
                              longitude=self.bot.api._position_lng)
        else:
            self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="Stats not loaded yet\n")

    def evolve(self, chatid, uid):
        # TODO: here comes evolve logic (later)
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Evolve logic not implemented yet")
        return

    def upgrade(self, chatid, uid):
        # TODO: here comes upgrade logic (later)
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Upgrade logic not implemented yet")
        return

    def get_event(self, event, formatted_msg, data):
        return self.chat_handler.get_event(event, formatted_msg, data)

    def get_events(self, update):
        return self.chat_handler.get_events(update)

    def run(self):
        time.sleep(1)
        while True:
            if DEBUG_ON: self.bot.logger.info("Telegram loop running")
            if self._tbot is None:
                self.connect()

            for update in self._tbot.getUpdates(offset=self.update_id, timeout=10):
                self.update_id = update.update_id + 1
                if update.message:
                    self.bot.logger.info("Telegram message from {} ({}): {}".format(update.message.from_user.username,
                                                                                    update.message.from_user.id,
                                                                                    update.message.text))
                    if update.message.text == "/start" or update.message.text == "/help":
                        res = (
                            "*Commands: *",
                            "/info - info about bot",
                            "/login <password> - authenticate with the bot; once authenticated, your ID will be registered with the bot and survive bot restarts",
                            "/logout - remove your ID from the 'authenticated' list",
                            "/sub <eventName> <parameters> - subscribe to eventName, with optional parameters, event name=all will subscribe to ALL events (LOTS of output!)",
                            "/unsub <eventName> <parameters> - unsubscribe from eventName; parameters must match the /sub parameters",
                            "/unsub everything - will remove all subscriptions for this uid",
                            "/showsubs - show current subscriptions",
                            "/events <filter> - show available events, filtered by regular expression  <filter>",
                            "/top <num> <cp-or-iv-or-dated> - show top X pokemons, sorted by CP, IV, or Date",
                            "/evolved <num> <cp-or-iv-or-dated> - show top x pokemon evolved, sorted by CP, IV, or Date",
                            "/hatched <num> <cp-or-iv-or-dated> - show top x pokemon hatched, sorted by CP, IV, or Date",
                            "/caught <num> <cp-or-iv-or-dated> - show top x pokemon caught, sorted by CP, IV, or Date",
                            "/pokestops - show last x pokestops visited",
                            "/released <num> <cp-or-iv-or-dated> - show top x released, sorted by CP, IV, or Date",
                            "/vanished <num> <cp-or-iv-or-dated> - show top x vanished, sorted by CP, IV, or Date",
                            "/softbans - info about possible softbans"
                        )
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="\n".join(res))
                        continue

                    if self.config.get('password', None) == None and (
                        not hasattr(self, "master") or not self.config.get('master',
                                                                           None)):  # no auth provided in config
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                         text="No password nor master configured in TelegramTask section, bot will not accept any commands")
                        continue
                    if re.match(r'^/login [^ ]+', update.message.text):
                        self.authenticate(update)
                        continue
                    if not self.isAuthenticated(update.message.from_user.id) and hasattr(self,
                                                                                         "master") and self.master and not unicode(
                            self.master).isnumeric() and unicode(self.master) == unicode(
                            update.message.from_user.username):
                        outMessage = "Telegram message received from correct user, but master is not numeric, updating datastore."
                        self.bot.logger.warn(outMessage)
                        # the "master" is not numeric, set self.master to update.message.chat_id and re-instantiate the handler
                        newconfig = self.config
                        newconfig['master'] = update.message.chat_id
                        # insert chat id into database
                        self.grab_uid(update)
                        # remove old handler
                        self.bot.event_manager._handlers = filter(lambda x: not isinstance(x, TelegramHandler),
                                                                  self.bot.event_manager._handlers)
                        # add new handler (passing newconfig as parameter)
                        self.bot.event_manager.add_handler(TelegramHandler(self.bot, newconfig))
                        continue
                    if not self.isAuthenticated(update.message.from_user.id):
                        # Reject message if sender does not match defined master in config
                        outMessage = "Telegram message received from unknown sender. Please either make sure your username or ID is in TelegramTask/master, or a password is set in TelegramTask section and /login is issued"
                        self.bot.logger.error(outMessage)
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                         text="Please /login first")
                        continue
                    # one way or another, the user is now authenticated
                    # make sure uid is in database
                    self.grab_uid(update)
                    if update.message.text == "/info":
                        self.send_player_stats_to_chat(update.message.chat_id)
                        continue
                    if re.match(r'^/softbans ', update.message.text):
                        (cmd, num) = self.tokenize(update.message.text, 2)
                        softbans = self.chat_handler.get_softbans(num)
                        outMsg = ''
                        if softbans:
                            for x in softbans:
                                outMsg += '*' + x[0] + '* ' + '(' + str(x[2]) + ')\n'
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="".join(outMsg))
                        else:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="No Softbans found! Good job!\n")
                        continue
                    if re.match("^/events", update.message.text):
                        events = self.get_events(update)
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                         text="\n".join(events))
                        continue
                    if update.message.text == "/logout":
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text=("Logged out."))
                        self.deauthenticate(update)
                        continue
                    if re.match(r'^/sub ', update.message.text):
                        self.chsub(update.message.text, update.message.chat_id)
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML',
                                         text=("Subscriptions updated."))
                        continue
                    if re.match(r'^/unsub ', update.message.text):
                        self.chsub(update.message.text, update.message.chat_id)
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML',
                                         text=("Subscriptions updated."))
                        continue
                    if re.match(r'^/showsubs', update.message.text):
                        subs = self.showsubs(update.message.chat_id)
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="\n".join(subs))
                        continue
                    if re.match(r'^/top ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        pkmns = self.chat_handler.showto(num, order)
                        outMsg = "\n".join(["*{}* (_CP:_ {} _IV:_ {} Candy:{})".format(p.name, p.cp, p.iv, p.candy)])
                        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text=outMsg)
                        continue
                    if re.match(r'^/caught ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        caught = self.chat_handler.get_caught(num, order)
                        outMsg = ''
                        if caught:
                            for x in caught:
                                outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[1])) + ' _IV:_ ' + str(
                                    x[2]) + ')\n'
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="".join(outMsg))
                        else:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="No Pokemon Caught Yet.\n")
                        continue
                    if re.match(r'^/evolved ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        evolved = self.chat_handler.get_evolved(num, order)
                        outMsg = ''
                        if evolved:
                            for x in evolved:
                                outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[1])) + ' _IV:_ ' + str(
                                    x[2]) + ')\n'
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="".join(outMsg))
                        else:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="No Evolutions Found.\n")
                        continue
                    if re.match(r'^/pokestops ', update.message.text):
                        (cmd, num) = self.tokenize(update.message.text, 2)
                        pokestops = self.chat_handler.get_pokestops(num)
                        outMsg = ''
                        if pokestops:
                            for x in pokestops:
                                outMsg += '*' + x[0] + '* ' + '(_XP:_ ' + str(x[1]) + ' _Items:_ ' + str(x[2]) + ')\n'
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="".join(outMsg))
                        else:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="No Pokestops Encountered Yet.\n")
                        continue
                    if re.match(r'^/hatched ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        hatched = self.chat_handler.get_hatched(num, order)
                        outMsg = ''
                        if hatched:
                            for x in hatched:
                                outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[1])) + ' _IV:_ ' + str(
                                    x[2]) + ')\n'
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="".join(outMsg))
                        else:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="No Eggs Hatched Yet.\n")
                        continue
                    if re.match(r'^/released ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        released = self.chat_handler.get_released(num, order)
                        outMsg = ''
                        if released:
                            for x in released:
                                outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[2])) + ' _IV:_ ' + str(
                                    x[1]) + ')\n'
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="".join(outMsg))
                        else:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="No Pokemon Released Yet.\n")
                        continue

                    if re.match(r'^/vanished ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        vanished = self.chat_handler.get_vanished(num, order)
                        outMsg = ''
                        if vanished:
                            for x in vanished:
                                outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[1])) + ' _IV:_ ' + str(
                                    x[2]) + ')\n'
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text=outMsg)
                        continue
                    self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                     text="Unrecognized command: {}".format(update.message.text))

    def showsubs(self, chatid):
        subs = []
        with self.bot.database as conn:
            for sub in conn.execute("select uid, event_type, parameters from telegram_subscriptions where uid = ?",
                                    [chatid]).fetchall():
                subs.append("{} -&gt; {}".format(sub[1], sub[2]))
        if subs == []: subs.append(
            "No subscriptions found. Subscribe using /sub EVENTNAME. For a list of events, send /events")
        return subs

    def chsub(self, msg, chatid):
        (cmd, evt, params) = self.tokenize(msg, 3)
        if cmd == "/sub":
            sql = "replace into telegram_subscriptions(uid, event_type, parameters) values (?, ?, ?)"
        else:
            if evt == "everything":
                sql = "delete from telegram_subscriptions where uid = ? and (event_type = ? or parameters = ? or 1 = 1)"  # does not look very elegant, but makes unsub'ing everythign possible
            else:
                sql = "delete from telegram_subscriptions where uid = ? and event_type = ? and parameters = ?"

        with self.bot.database as conn:
            conn.execute(sql, [chatid, evt, params])
            conn.commit()
        return

    def tokenize(self, string, maxnum):
        spl = string.split(' ', maxnum - 1)
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
        res = self.conn.execute("select sql,type from sqlite_master where name = ?",
                                [name]).fetchone()  # grab objects definition

        if res and len(res) > 0 and res[0] != sql:  # object exists and sql not matching
            self.conn.execute("drop {} {}".format(res[1], name))  # drop it

        if res is None or len(res) == 0 or res[0] != sql:  # object missing or sql not matching
            self.conn.execute(sql)
        return


class TelegramHandler(EventHandler):
    def __init__(self, bot, config):
        initiator = TelegramDBInit(bot.database)
        self.bot = bot
        self.tbot = telegram.Bot(self.bot.config.telegram_token)
        self.pokemons = config.get('alert_catch', {})
        self.whoami = "TelegramHandler"
        self.config = config
        self.chat_handler = ChatHandler(self.bot, self.pokemons)
        self._connect()

    def _connect(self):
        self.bot.logger.info("Telegram bot not running. Starting")
        self.tbot = TelegramClass(self.bot, self.pokemons, self.config)
        thread.start_new_thread(self.tbot.run)

    def catch_notify(self, pokemon, cp, iv, params):
        if params == " ":
            return True
        try:
            oper = re.search(r'operator:([^ ]+)', params).group(1)
            rule_cp = int(re.search(r'cp:([0-9]+)', params).group(1))
            rule_iv = float(re.search(r'iv:([0-9.]+)', params).group(1))
            rule_pkmn = re.search(r'pokemon:([^ ]+)', params).group(1)
            return rule_pkmn == pokemon and (
            oper == "or" and (cp >= rule_cp or iv >= rule_iv) or cp >= rule_cp and iv >= rule_iv)
        except:
            return False

    def handle_event(self, event, sender, level, formatted_msg, data):
        msg = None
        # first handle subscriptions; they are independent of master setting.
        with self.bot.database as conn:
            subs = conn.execute(
                "select uid, parameters, event_type from telegram_subscriptions where event_type in (?,'all','debug')",
                [event]).fetchall()
            for sub in subs:
                if DEBUG_ON: self.bot.logger.info("Processing sub {}".format(sub))
                (uid, params, event_type) = sub
                if event != 'pokemon_caught' or self.catch_notify(data["pokemon"], int(data["cp"]), float(data["iv"]),
                                                                  params):
                    if DEBUG_ON:
                        self.bot.logger.info("Matched sub {} event {}".format(sub, event))
                    elif event_type == "debug":
                        self.bot.logger.info("[{}] {}".format(event, msg))
                    else:
                        msg = self.tbot.get_event(event, formatted_msg, data)

                    if DEBUG_ON: self.bot.logger.info("Telegram message {}".format(msg))

                    if msg is None: return
                else:
                    if DEBUG_ON: self.bot.logger.info("No match sub {} event {}".format(sub, event))

        if msg is not None:
            if self.tbot is None:  # instantiate tbot (TelegramClass) if not already set
                if DEBUG_ON:
                    self.bot.logger.info("handle_event Telegram bot not running.")
                try:
                    self._connect()
                except Exception as inst:
                    self.bot.logger.error("Unable to start Telegram bot; exception: {}".format(pprint.pformat(inst)))
                    self.tbot = None
                    return

            else:
                if self.tbot is not None:  # tbot should be running, but just in case it hasn't started yet
                    self.tbot.sendMessage(chat_id=uid, parse_mode='Markdown', text=msg)
