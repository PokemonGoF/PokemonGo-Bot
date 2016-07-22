import json 
import logging 

from flask import Flask
from flask_classy import FlaskView, route
from pokemongo_bot import PokemonGoBot

app = Flask(__name__)

global global_bot

class PokemonGoServer(object):
    def __init__(self, bot, config, port=5000):
        api_view = ApiView()
        api_view.set_bot(bot)
        api_view.register(app)
        self.port = port

	# Setting the Flask app's log level
	log = logging.getLogger('werkzeug')

	if config.debug:
	    log.setLevel(logging.DEBUG)
	else:
	    log.setLevel(logging.ERROR)

    def start(self):
        app.run(host='127.0.0.1', port=self.port)

class ApiView(FlaskView):
    def set_bot(self, bot):
        global global_bot
        global_bot = bot

    @route("/player_info")
    def get_player_info(self):
        return global_bot.get_player_info(False)
