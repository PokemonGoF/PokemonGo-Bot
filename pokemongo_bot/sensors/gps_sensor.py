# -*- coding: utf-8 -*-

class GpsSensor(object):

    def __init__(self, bot):
        self.bot = bot
        self.altitude = self.bot.config.gps['initial_altitude']

    @property
    def position(self):
        return self.bot.api._position_lat, self.bot.api._position_lng, self.bot.api._position_alt

    @position.setter
    def position(self, position_tuple):
        if len(position_tuple) > 2:
            # If not told to change altitude, leave it alone
            self.altitude = position_tuple[2]

        self.bot.event_manager.emit(
            'position_update',
            sender=self,
            level='debug',
            formatted='Setting location to {current_position}',
            data={
                'current_position': [position_tuple[0], position_tuple[1], self.altitude],
                'last_position': '',
                'distance': '',
                'distance_unit': ''
            }
        )

        self.bot.api.set_position(position_tuple[0], position_tuple[1], self.altitude)
