#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dispatcher import Signal, receiver

sign_in_signal = Signal(providing_args=['player', 'instance'])


class MyBot(object):
    def __init__(self, player=None):
        if not player:
            player = {}
        self.player = player

    def login(self):
        sign_in_signal.send(sender=self.__class__, instance=self, player=self.player)


def sign_in_handler(sender, instance, player, **kwargs):
    print 'sign_in_handler'
    print 'sender', sender
    print 'instance', instance
    print 'actor', player


@receiver([sign_in_signal], sender=MyBot)
def another_sign_in_hander(sender, **kwargs):
    print 'another_sign_in_hander', sender, kwargs


sign_in_signal.connect(sign_in_handler, sender=MyBot)

if __name__ == '__main__':
    bot = MyBot(player={'name': 'justAName'})
    bot.login()
