# -*- coding: utf-8 -*-
import re
from pokemongo_bot import inventory

DEBUG_ON = False

class ChatHandler:
    def __init__(self, bot):
        self.bot = bot

    def get_player_stats(self):
        stats = inventory.player().player_stats
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
            return(res)
        else:
            return("Stats not loaded yet\n")
            
    def display_events(self, update):
        cmd = update.message.text.split(" ", 1)
        if len(cmd) > 1:
            # we have a filter
            event_filter = ".*{}-*".format(cmd[1])
        else:
            # no filter
            event_filter = ".*"
        events = filter(lambda k: re.match(event_filter, k), self.bot.event_manager._registered_events.keys())
        self.sendMessage(chat_id=update.message.chat_id, parse_mode='HTML', text=("\n".join(events)))

    def showtop(self, chatid, num, order):
        if not num.isnumeric():
            num = 10
        else:
            num = int(num)

        if order not in ["cp", "iv"]:
            order = "iv"

        pkmns = sorted(inventory.pokemons().all(), key=lambda p: getattr(p, order), reverse=True)[:num]

        outMsg = "\n".join(["{} CP:{} IV:{} ID:{} Candy:{}".format(p.name, p.cp, p.iv, p.unique_id, inventory.candies().get(p.pokemon_id).quantity) for p in pkmns])
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text=outMsg)

        return

    def evolve(self, chatid, uid):
        # TODO: here comes evolve logic (later)
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Evolve logic not implemented yet")
        return

    def upgrade(self, chatid, uid):
        # TODO: here comes upgrade logic (later)
        self.sendMessage(chat_id=chatid, parse_mode='HTML', text="Upgrade logic not implemented yet")
        return

