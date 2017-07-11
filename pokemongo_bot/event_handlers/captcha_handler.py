# -*- coding: utf-8 -*-
from __future__ import print_function
import time

import requests
import os

from pokemongo_bot.event_manager import EventHandler
from pokemongo_bot.base_task import BaseTask
from sys import platform as _platform
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

SITE_KEY = '6LeeTScTAAAAADqvhqVMhPpr_vB9D364Ia-1dSgK'


class CaptchaHandler(EventHandler):
    def __init__(self, bot, captcha_solving):
        super(CaptchaHandler, self).__init__()
        self.bot = bot
        self.enabled = captcha_solving


    def get_token(self, url):
        token = ''
        path = os.getcwd()
        if _platform == "Windows" or _platform == "win32":
            # Check if we are on 32 or 64 bit
            file_name= 'chromedriver.exe'
        if _platform.lower() == "darwin":
            file_name= 'chromedriver'
        if _platform.lower() == "linux" or _platform.lower() == "linux2":
            file_name = 'chromedriver'
            
        full_path = ''
        if os.path.isfile(path + '/' + file_name): # check encrypt_location or local dir first
            full_path = path + '/' + file_name

        if full_path == '':
            self.bot.logger.error(file_name + ' is needed for manual captcha solving! Please place it in the bots root directory')
            sys.exit(1)
        
        try:
            driver = webdriver.Chrome(full_path)
            driver.set_window_size(600, 600)
        except Exception:
            self.bot.logger.error('Error with Chromedriver, please ensure it is the latest version.')
            sys.exit(1)
            
        driver.get(url)
        
        elem = driver.find_element_by_class_name("g-recaptcha")
        driver.execute_script("arguments[0].scrollIntoView(true);", elem)
        self.bot.logger.info('You have 1 min to solve the Captcha')
        try:
            WebDriverWait(driver, 60).until(EC.text_to_be_present_in_element_value((By.NAME, "g-recaptcha-response"), ""))
            token = driver.execute_script("return grecaptcha.getResponse()")
            driver.close()
        except TimeoutException, err:
            self.bot.logger.error('Timed out while trying to solve captcha')
        driver.quit()
        return token
    
    def handle_event(self, event, sender, level, formatted_msg, data):
        if event in ('pokestop_searching_too_often', 'login_successful'):
            self.bot.logger.info('Checking for captcha challenge.')

            # test manual 
            url = 'http://www.google.com/xhtml'
            
            request = self.bot.api.create_request()
            request.check_challenge()
            response_dict = request.call()
            
            challenge = response_dict['responses']['CHECK_CHALLENGE']
            if not challenge.get('show_challenge'):
                self.bot.event_manager.emit(
                    'captcha',
                    sender=self,
                    level='info',
                    formatted="Captcha Check Passed"
                )
                return
            url = challenge['challenge_url']
            
            if self.enabled == False:
                self.bot.event_manager.emit(
                    'captcha',
                    sender=self,
                    level='info',
                    formatted="Captcha encountered but solving diabled, exiting..."
                )
                sys.exit(1)
                return

            if not self.bot.config.twocaptcha_token:
                self.bot.logger.warn('No 2captcha token set, executing manual solving')
                token = self.get_token(url)
                if token !='':
                    self.bot.logger.info('Token: ' + token)
                    
                    request = self.bot.api.create_request()
                    request.verify_challenge(token=token)
                    request.call()
                    
                    self.bot.logger.info('Captcha solved')
                else:
                    self.bot.logger.error('Could not solve captcha')
                    sys.exit(1)
                return

            self.bot.logger.info('Creating 2captcha session for {}.'.format(url))
            response = requests.get('http://2captcha.com/in.php', params={
                'key': self.bot.config.twocaptcha_token,
                'method': 'userrecaptcha',
                'googlekey': SITE_KEY,
                'pageurl': url,
            })
            result = response.text.split('|', 1)
            if result[0] != 'OK':
                self.bot.logger.error('Failed to send captcha to 2captcha: {}'.format('|'.join(result)))
                return
            captcha_id = result[1]

            while True:
                time.sleep(10)
                response = requests.get('http://2captcha.com/res.php', params={
                    'key': self.bot.config.twocaptcha_token,
                    'action': 'get',
                    'id': captcha_id
                })
                result = response.text.split('|', 1)
                if result[0] == 'CAPCHA_NOT_READY':
                    self.bot.logger.info('2captcha reports captcha has not been solved yet.')
                    continue

                if result[0] == 'OK':
                    self.bot.logger.info('2captcha reports captcha has been solved.')
                    
                    request = self.bot.api.create_request()
                    request.verify_challenge(token=result[1])
                    request.call()
                else:
                    self.bot.logger.error('Could not solve captcha: {}'.format('|'.join(result)))

                break