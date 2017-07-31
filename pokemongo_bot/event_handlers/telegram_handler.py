# -*- coding: utf-8 -*-
from pokemongo_bot.event_manager import EventHandler
import time
import telegram
import thread
import re
from telegram.utils import request
from chat_handler import ChatHandler
from pokemongo_bot.inventory import Pokemons
from pokemongo_bot import inventory
from pokemongo_bot.item_list import Item
from pokemongo_bot.cell_workers.utils import wait_time_sec, distance, convert

DEBUG_ON = False
SUCCESS = 1
ERROR_XP_BOOST_ALREADY_ACTIVE = 3

class TelegramSnipe(object):
    ENABLED = False
    ID = int(0)
    POKEMON_NAME = ''
    LATITUDE = float(0)
    LONGITUDE = float(0)
    SNIPE_DISABLED = False

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
        self.master = None

    def connect(self):
        if DEBUG_ON: self.bot.logger.info("Not connected. Reconnecting")
        self._tbot = telegram.Bot(self.bot.config.telegram_token)
        try:
            self.update_id = self._tbot.getUpdates()[0].update_id
        except IndexError:
            self.update_id = None

    def grab_uid(self, update):
        with self.bot.database as conn:
            conn.execute("replace into telegram_uids (uid, username) values (?, ?)",
                         (update.message.chat_id, update.message.from_user.username))
            conn.commit()
        if self.master: self.master = update.message.chat_id

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
            if res[0] == 1: return True
            return False

    def isAuthenticated(self, chat_id):
        return self.isMasterFromConfigFile(chat_id) or self.isMasterFromActiveLogins(chat_id)
        
    def deauthenticate(self, update):
        with self.bot.database as conn:
            cur = conn.cursor()
            sql = "delete from telegram_logins where uid = {}".format(update.message.chat_id)
            cur.execute(sql)
            conn.commit()
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Logout completed")
        return

    def authenticate(self, update):
        args = update.message.text.split(' ')
        if len(args) != 2:
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                          text="Invalid password")
            return
        password = args[1]
        if password != self.config.get('password', None):
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                          text="Invalid password")
        else:
            with self.bot.database as conn:
                cur = conn.cursor()
                cur.execute("insert or replace into telegram_logins(uid) values(?)",[update.message.chat_id])
                conn.commit()
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                          text="Authentication successful, you can now use all commands")
        return

    def sendMessage(self, chat_id=None, parse_mode='Markdown', text=None):
        try:
            if self._tbot is None:
                self.connect()
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
            self.sendMessage(chat_id=chat_id,
                             parse_mode='Markdown',
                             text="*{}* \n_Level:_ {} \n_XP:_ {}/{} \n_Pokemons Captured:_ {} ({} _last 24h_) \n_Poke Stop Visits:_ {} ({} _last 24h_) \n_KM Walked:_ {} \n_Stardust:_ {}".format(
                                 stats[0], stats[1], stats[2], stats[3], stats[4], stats[5], stats[6], stats[7], stats[8], stats[9]))
            self.sendLocation(chat_id=chat_id, latitude=self.bot.api._position_lat,
                              longitude=self.bot.api._position_lng)
        else:
            self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="Stats not loaded yet\n")

    def send_event(self, event, formatted_msg, data):
        return self.chat_handler.get_event(event, formatted_msg, data)

    def send_events(self, update):
        events = self.chat_handler.get_events(update)
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML',
                         text="\n".join(events))

    def send_softbans(self, update, num):
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

    def send_subscription_updated(self, update):
        self.chsub(update.message.text, update.message.chat_id)
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML',
                                      text=("Subscriptions updated."))

    def send_info(self, update):
        self.send_player_stats_to_chat(update.message.chat_id)

    def send_logout(self, update):
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML', text=("Logged out."))
        self.deauthenticate(update)

    def send_caught(self, update, num, order):
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
                             
    def request_snipe(self, update, pkm, lat, lng):
        snipeSuccess = False
        try:
            id = Pokemons.id_for(pkm)
        except:
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Invaild Pokemon")
            return

        #Set Telegram Snipe to true and let sniper do its work
        TelegramSnipe.ENABLED = True
        TelegramSnipe.ID = int(id)
        TelegramSnipe.POKEMON_NAME = str(pkm)
        TelegramSnipe.LATITUDE = float(lat)
        TelegramSnipe.LONGITUDE = float(lng)
        
        outMsg = 'Catching pokemon: ' + TelegramSnipe.POKEMON_NAME + ' at Latitude: ' + str(TelegramSnipe.LATITUDE) + ' Longitude: ' + str(TelegramSnipe.LONGITUDE) + '\n'
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="".join(outMsg))
        
    def request_snipe_time(self, update, lat, lng):
        last_position = self.bot.position[0:2]
        snipe_distance = convert(distance(last_position[0],last_position[1],float(lat),float(lng)),"m","km")
        time_to_snipe = wait_time_sec(snipe_distance)/60
        if time_to_snipe <= 900:
            outMsg = "Estimate Time to Snipe: " + "{0:.2f}".format(time_to_snipe) + " Mins. Distance: " + "{0:.2f}".format(snipe_distance) + "KM"
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="".join(outMsg))
        else:
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Sniping distance is more than supported distance")
    
    def request_snipe_disable(self, update, config):
        if config.lower() == "true":
            TelegramSnipe.SNIPE_DISABLED = True
            return True
        else:
            TelegramSnipe.SNIPE_DISABLED = False
            return False
        
    def send_evolved(self, update, num, order):
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
                             
    def request_luckyegg_count(self,update):
        lucky_egg = inventory.items().get(Item.ITEM_LUCKY_EGG.value)  # @UndefinedVariable
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                         text="Lucky Egg Count: " + str(lucky_egg.count))

            
    def request_luckyegg(self,update):
        lucky_egg = inventory.items().get(Item.ITEM_LUCKY_EGG.value)  # @UndefinedVariable

        if lucky_egg.count == 0:
            return False

        response_dict = self.bot.use_lucky_egg()

        if not response_dict:
            self.bot.logger.info("Telegram Request: Failed to use lucky egg!")
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                             text="Failed to use lucky egg!\n")
            return False

        result = response_dict.get("responses", {}).get("USE_ITEM_XP_BOOST", {}).get("result", 0)

        if result == SUCCESS:
            lucky_egg.remove(1)
            self.bot.logger.info("Telegram Request: Used lucky egg, {} left.".format(lucky_egg.count))
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                             text="Used lucky egg, " + str(lucky_egg.count) + " left.")
            return True
        elif result == ERROR_XP_BOOST_ALREADY_ACTIVE:
            self.bot.logger.info("Telegram Request: Lucky egg already active, {} left.".format(lucky_egg.count))
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                             text="Lucky egg already active, " + str(lucky_egg.count) + " left.")
            return True
        else:
            self.bot.logger.info("Telegram Request: Failed to use lucky egg!")
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                             text="Failed to use lucky egg!\n")
            return False

    def send_pokestops(self, update, num):
        pokestops = self.chat_handler.get_pokestops( num)
        outMsg = ''
        if pokestops:
            for x in pokestops:
                outMsg += '*' + x[0] + '* ' + '(_XP:_ ' + str(x[1]) + ' _Items:_ ' + str(x[2]) + ')\n'
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                             text="".join(outMsg))
        else:
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                             text="No Pokestops Encountered Yet.\n")

    def send_hatched(self, update, num, order):
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

    def send_released(self, update, num, order):
        released = self.chat_handler.get_released(num, order)
        outMsg = ''
        if released:
            for x in released:
                outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[1])) + ' _IV:_ ' + str(
                    x[2]) + ')\n'
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                             text="".join(outMsg))
        else:
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                             text="No Pokemon Released Yet.\n")

    def send_vanished(self, update, num, order):
        vanished = self.chat_handler.get_vanished( num, order)
        outMsg = ''
        if vanished:
            for x in vanished:
                outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[1])) + ' _IV:_ ' + str(
                    x[2]) + ')\n'
            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                             text=outMsg)



    def send_top(self, update, num, order):
        top = self.chat_handler.get_top(num, order)
        outMsg = ''
        for x in top:
            outMsg += "*{}* _CP:_ {} _IV:_ {} (Candy: {})\n".format(x[0], x[1], x[2], x[3])
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text=outMsg)



    def showsubs(self, update):
        subs = []
        with self.bot.database as conn:
            for sub in conn.execute("select uid, event_type, parameters from telegram_subscriptions where uid = ?",
                                    [update.message.chat_id]).fetchall():
                subs.append("{} -&gt; {}".format(sub[1], sub[2]))
        if subs is []: subs.append(
            "No subscriptions found. Subscribe using /sub EVENTNAME. For a list of events, send /events")
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML', text="\n{}".join(subs))

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

    def send_start(self, update):
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
            "/snipe <PokemonName> <Lat> <Lng> - to snipe a pokemon at location Latitude, Longitude",
            "/snipetime <Lag> <Lng> - return time that will be teaken to snipe at given location",
            "/luckyegg - activate luckyegg",
            "/luckyeggcount - return number of luckyegg",
            "/softbans - info about possible softbans"
        )
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                         text="\n".join(res))

    def is_configured(self, update):
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                         text="No password nor master configured in TelegramTask section, bot will not accept any commands")

    def is_master_numeric(self, update):
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

    def is_known_sender(self, update):
        # Reject message if sender does not match defined master in config
        outMessage = "Telegram message received from unknown sender. Please either make sure your username or ID is in TelegramTask/master, or a password is set in TelegramTask section and /login is issued"
        self.bot.logger.error(outMessage)
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                         text="Please /login first")



    def tokenize(self, string, maxnum):
        spl = string.split(' ', maxnum - 1)
        while len(spl) < maxnum:
            spl.append(" ")
        return spl

    def evolve(self, chatid, uid):
        # TODO: here comes evolve logic (later)
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Evolve logic not implemented yet")
        return

    def upgrade(self, chatid, uid):
        # TODO: here comes upgrade logic (later)
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Upgrade logic not implemented yet")
        return

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

                    if re.match(r'^/login [^ ]+', update.message.text):
                        self.authenticate(update)
                        continue
                    if self.config.get('password', None) == None and (
                        not hasattr(self, "master") or not self.config.get('master', None)):# no auth provided in config
                        self.is_configured(update)
                        continue
                    if not self.isAuthenticated(update.message.from_user.id) and hasattr(self,
                            "master") and self.master and not unicode(self.master).isnumeric() and \
                            unicode(self.master) == unicode(update.message.from_user.username):
                        self.is_master_numeric(update)
                        continue
                    if not self.isAuthenticated(update.message.from_user.id):
                        self.is_known_sender(update)
                        continue
                    # one way or another, the user is now authenticated
                    # make sure uid is in database
                    self.grab_uid(update)
                    if update.message.text == "/start" or update.message.text == "/help":
                        self.send_start(update)
                        continue
                    if update.message.text == "/info":
                        self.send_info(update)
                        continue

                    if update.message.text == "/logout":
                        self.send_logout(update)
                        continue
                    if re.match("^/events", update.message.text):
                        self.send_events(update)
                        continue
                    if re.match(r'^/sub ', update.message.text):
                        self.send_subscription_updated(update)
                        continue
                    if re.match(r'^/unsub ', update.message.text):
                        self.send_subscription_updated(update)
                        continue
                    if re.match(r'^/showsubs', update.message.text):
                        self.showsubs(update)
                        continue
                    if re.match(r'^/top ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        self.send_top(update, num, order)
                        continue
                    if re.match(r'^/caught ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        self.send_caught(update, num, order)
                        continue
                    if re.match(r'^/evolved ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        self.send_evolved(update, num, order)
                        continue
                    if re.match(r'^/pokestops ', update.message.text):
                        (cmd, num) = self.tokenize(update.message.text, 2)
                        self.send_pokestops(update, num)
                        continue
                    if re.match(r'^/hatched ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        self.send_hatched(update, num, order)
                        continue
                    if re.match(r'^/released ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        self.send_released(update, num, order)
                        continue
                    if re.match(r'^/vanished ', update.message.text):
                        (cmd, num, order) = self.tokenize(update.message.text, 3)
                        self.send_vanished(update, num, order)
                        continue
                    if re.match(r'^/snipe ', update.message.text):
                        try:
                            (cmd, pkm, lat, lng) = self.tokenize(update.message.text, 4)
                            self.request_snipe(update, pkm, lat, lng)
                        except:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="An Error has occured")
                        continue
                    if re.match(r'^/snipetime ', update.message.text):
                        try:
                            (cmd, lat, lng) = self.tokenize(update.message.text, 3)
                            self.request_snipe_time(update, lat, lng)
                        except:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="An Error has occured")
                        continue
                        
                    if re.match(r'^/luckyeggcount', update.message.text):
                        try:
                            self.request_luckyegg_count(update)
                        except:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="An Error has occured")
                        continue
                    if re.match(r'^/luckyegg', update.message.text):
                        try:
                            if self.request_luckyegg(update):
                                self.bot.logger.info("Telegram has called for lucky egg. Success.")
                            else:
                                self.bot.logger.info("Telegram has called for lucky egg. Failed.")
                        except:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="An Error has occured")
                        continue
                    if re.match(r'^/snipedisabled ', update.message.text):
                        try:
                            (cmd, config) = self.tokenize(update.message.text, 2)
                            success = self.request_snipe_disable(update, config)
                            if success:
                                msg = "Sniper disabled"
                            else:
                                msg = "Sniper set as default"
                                
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text=msg)
                        except:
                            self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                             text="An Error has occured")
                        continue
                    if re.match(r'^/softbans ', update.message.text):
                        (cmd, num) = self.tokenize(update.message.text, 2)
                        self.send_softbans(update, num)
                        continue
                 
                    self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown',
                                     text="Unrecognized command: {}".format(update.message.text))


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
        self.tbot = None
        self.pokemons = config.get('alert_catch', {})
        self.whoami = "TelegramHandler"
        self.config = config
        self.chat_handler = ChatHandler(self.bot, self.pokemons)
        self._connect()

    def _connect(self):
        if self.tbot is None:
            self.bot.logger.info("Telegram bot not running. Starting")
            self.tbot = TelegramClass(self.bot, self.pokemons, self.config)
            thread.start_new_thread(self.tbot.run)
        return self.tbot

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
                if not self.tbot.isAuthenticated(uid): # UID has subs but not in auth list.
                    return
                if event != 'pokemon_caught' or self.catch_notify(data["pokemon"], int(data["cp"]), float(data["iv"]),
                                                                  params):
                    if DEBUG_ON:
                        self.bot.logger.info("Matched sub {} event {}".format(sub, event))
                    elif event_type == "debug":
                        self.bot.logger.info("[{}] {}".format(event, msg))
                    else:
                        msg = self.chat_handler.get_event(event, formatted_msg, data)

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

            if self.tbot is not None:  # tbot should be running, but just in case it hasn't started yet

                self.tbot.sendMessage(chat_id=uid, parse_mode='Markdown', text=msg)
