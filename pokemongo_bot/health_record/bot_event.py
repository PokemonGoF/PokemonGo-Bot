# -*- coding: utf-8 -*-
from time import sleep

import logging
from raven import Client
import raven
import os
import uuid
import requests

class BotEvent(object):
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # UniversalAnalytics can be reviewed here:
        # https://github.com/analytics-pros/universal-analytics-python
        if self.config.health_record:
            self.logger.info('Health check is enabled. For more logrmation:')
            self.logger.info('https://github.com/PokemonGoF/PokemonGo-Bot/tree/dev#analytics')
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

    def login_success(self):
        if self.config.health_record:
            track_url('/loggedin')

    def login_failed(self):
        if self.config.health_record:
            track_url('/login')

    def login_retry(self):
        if self.config.health_record:
            track_url('/relogin')

    def logout(self):
        if self.config.health_record:
            track_url('/logout')


def track_url(path):
    data = {
        'v': '1',
        'tid': 'UA-81469507-1',
        'aip': '1', # Anonymize IPs
        'cid': uuid.uuid4(),
        't': 'pageview',
        'dp': path
    }

    response = requests.post(
        'http://www.google-analytics.com/collect', data=data)

    response.raise_for_status()
