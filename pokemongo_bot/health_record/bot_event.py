# -*- coding: utf-8 -*-
from UniversalAnalytics import Tracker
from pokemongo_bot import logger
from time import sleep

class BotEvent(object):
    def __init__(self,bot):
        self.bot = bot
        # UniversalAnalytics can be reviewed here:
        # https://github.com/analytics-pros/universal-analytics-python
        # For central TensorFlow training, forbiden any personally information
        # report to server
        # Review Very Carefully for the following line, forbiden ID changed PR:
        if bot.config.health_record:
            logger.log('Send anonymous bot health report to server, it can be disabled by config \"health_record\":false in config file', 'red')
            logger.log('Wait for 2 seconds ', 'red')
            sleep(3)
            self.tracker = Tracker.create('UA-81469507-1', use_post=True)
    # No RAW send function to be added here, to keep everything clean
    def login_success(self):
        if self.bot.config.health_record:
            self.tracker.send('pageview', '/loggedin', title='succ')
    def login_failed(self):
        if self.bot.config.health_record:
            self.tracker.send('pageview', '/login', title='fail')
    def login_retry(self):
        if self.bot.config.health_record:
            self.tracker.send('pageview', '/relogin', title='relogin')
    def logout(self):
        if self.bot.config.health_record:
            self.tracker.send('pageview', '/logout', title='logout')
