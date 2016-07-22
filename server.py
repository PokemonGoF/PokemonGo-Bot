import json 

from flask import Flask
from flask.ext.classy import FlaskView, route
#from bot import PokemonGoBot

from pgoapi import PGoApi

app = Flask(__name__)

global global_bot

class PokemonGoServer(object):
    def __init__(self, bot, port=5000):
        api_view = ApiView()
        api_view.set_bot(bot)
        api_view.register(app)
        self.port = port

    def start(self):
        app.run(host='0.0.0.0', port=self.port)

class ApiView(FlaskView):
    def set_bot(self, bot):
        global global_bot
        global_bot = bot

    @route("/player_info")
    def get_player_info(self):
        return global_bot.get_player_info(False)
