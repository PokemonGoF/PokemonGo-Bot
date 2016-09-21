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
        msg = None
        if event == 'level_up':
            msg = "level up ({})".format(data["current_level"])
        elif event == 'pokemon_caught':
            trigger = None
            if data["pokemon"] in self.pokemons:		
                trigger = self.pokemons[data["pokemon"]]		
            elif "all" in self.pokemons:		
                trigger = self.pokemons["all"]
            if trigger:
                if ((not "operator" in trigger or trigger["operator"] == "and") and data["cp"] >= trigger["cp"] and data["iv"] >= trigger["iv"]) or \
                        ("operator" in trigger and trigger["operator"] == "or" and (data["cp"] >= trigger["cp"] or data["iv"] >= trigger["iv"])):
                    msg = "Caught {} CP: {}, IV: {}".format(data["pokemon"], data["cp"], data["iv"])
        elif event == 'egg_hatched':
            msg = "Egg hatched with a {} CP: {}, IV: {} (A/D/S {})".format(data["name"], data["cp"], data["iv_pct"], data["iv_ads"])
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
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML', text="\n".join(
            sorted(filter(lambda k: re.match(event_filter, k), self.bot.event_manager._registered_events.keys()))))

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

        outMsg = "\n".join(["*{}* (_CP:_ {}) (_IV:_ {}) (Candy:{})".format(p.name, p.cp, p.iv,
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
            outMsg = ''
            if evolved:
                for x in evolved:
                    outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[2])) + ') (_IV:_ ' + str(x[1]) + ')\n'
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="".join(str(outMsg)))
            else:
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="No Evolutions Found.\n")

    def get_softban(self, chat_id):
        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM softban_log")
            softban = cur.fetchall()
            outMsg = ''
            if softban:
                for x in softban:
                    outMsg += '*' + x[0] + '* ' + '(' + str(x[2]) + ')\n'
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="".join(str(outMsg)))
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
            outMsg = ''
            if hatched:
                for x in hatched:
                    outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[1])) + ') (_IV:_ ' + str(x[2]) + ')\n'
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="".join(str(outMsg)))
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
            outMsg = ''
            if caught:
                for x in caught:
                    outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[2])) + ') (_IV:_ ' + str(x[1]) + ')\n'
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="".join(str(outMsg)))
            else:
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="No Pokemon Caught Yet.\n")

    def get_pokestops(self, chat_id, num):
        with self.bot.database as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pokestop_log ORDER BY dated DESC LIMIT " + str(num))
            pokestop = cur.fetchall()
            outMsg = ''
            if pokestop:
                for x in pokestop:
                    outMsg += '*' + x[0] + '* ' + '(_XP:_ ' + str(x[1]) + ') (_Items:_ ' + str(x[2]) + ')\n'
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="".join(str(outMsg)))
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
            outMsg = ''
            if transfer:
                for x in transfer:
                    outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[2])) + ') (_IV:_ ' + str(x[1]) + ')\n'
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="".join(str(outMsg)))
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
            outMsg = ''
            if vanished:
                for x in vanished:
                    outMsg += '*' + x[0] + '* ' + '(_CP:_ ' + str(int(x[1])) + ') (_IV:_ ' + str(x[2]) + ')\n'
                self.sendMessage(chat_id=chat_id, parse_mode='Markdown', text="".join(str(outMsg)))
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
    def showsubs(self, chatid):
        subs = []
        with self.bot.database as conn:
            for sub in conn.execute("select uid, event_type, parameters from telegram_subscriptions where uid = ?", [chatid]).fetchall():
                subs.append("{} -&gt; {}".format(sub[1], sub[2]))
        if subs == []: subs.append("No subscriptions found. Subscribe using /sub EVENTNAME. For a list of events, send /events")
        self.chat_handler.sendMessage(chat_id=chatid, parse_mode='HTML', text="\n".join(subs))

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

    def deauthenticate(self,  update):
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Logout completed")

    def authenticate(self, update):
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Invalid password")

    def invalid_password(self, update):
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Invalid password")

    def authentication_successful(self, update):
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Authentication successful, you can now use all commands")

    def update_message(self, update):
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

    def do_not_accept(self, update):
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="No password nor master configured in TelegramTask section, bot will not accept any commands")

    def login_first(self, update):
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Please /login first")

    def sub_message(self, update):
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML', text=("Subscriptions updated."))

    def unrecognized_command(self, update):
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='Markdown', text="Unrecognized command: {}".format(update.message.text))

    def tbot_test(self, msg, uid):
        self.sendMessage(chat_id=uid, parse_mode='Markdown', text=msg)