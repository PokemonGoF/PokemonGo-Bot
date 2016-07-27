# -*- coding: utf-8 -*-
from UniversalAnalytics import Tracker

class BotEvent(object):
    def __init__(self):
        # UniversalAnalytics can be reviewed here:
        # https://github.com/analytics-pros/universal-analytics-python
        # For central TensorFlow training, forbiden any personally information
        # report to server
        # Review Very Carefully for the following line, forbiden ID changed PR:
        self.tracker = Tracker.create('UA-81469507-1', use_post=True)
    # No RAW send function to be added here, to keep everything clean
    def login_success(self):
        self.tracker.send('pageview', '/loggedin', title='succ')
    def login_failed(self):
        self.tracker.send('pageview', '/login', title='fail')
    def login_retry(self):
        self.tracker.send('pageview', '/relogin', title='relogin')
    def logout(self):
        self.tracker.send('pageview', '/logout', title='logout')
