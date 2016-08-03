# -*- coding: utf-8 -*-
from time import sleep

from UniversalAnalytics import Tracker

from pokemongo_bot import logger
from raven import Client
import raven
import os

class BotEvent(object):
    def __init__(self, config):
        self.config = config
        # UniversalAnalytics can be reviewed here:
        # https://github.com/analytics-pros/universal-analytics-python
        if self.config.health_record:
            logger.log('Health check is enabled. For more information:', 'yellow')
            logger.log('https://github.com/PokemonGoF/PokemonGo-Bot/tree/dev#analytics', 'yellow')
            self.tracker = Tracker.create('UA-81469507-1', use_post=True)
            self.client = Client(
                dsn='https://8abac56480f34b998813d831de262514:196ae1d8dced41099f8253ea2c8fe8e6@app.getsentry.com/90254',
                name='PokemonGof-Bot',
                processors = (
                    'raven.processors.SanitizePasswordsProcessor',
                    'raven.processors.RemoveStackLocalsProcessor'
                ),
                install_logging_hook = False,
                hook_libraries = (),
                enable_breadcrumbs = False,
                logging = False,
                context = {}
            )

    def capture_error(self):
        if self.config.health_record:
            self.client.captureException()

    # No RAW send function to be added here, to keep everything clean
    def login_success(self):
        if self.config.health_record:
            self.tracker.send('pageview', '/loggedin', title='succ')

    def login_failed(self):
        if self.config.health_record:
            self.tracker.send('pageview', '/login', title='fail')

    def login_retry(self):
        if self.config.health_record:
            self.tracker.send('pageview', '/relogin', title='relogin')

    def logout(self):
        if self.config.health_record:
            self.tracker.send('pageview', '/logout', title='logout')
