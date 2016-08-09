import time

class GymCache(object):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.cache_length_seconds = 60 * 10

    def get(self, gym_id, player_latitude, player_longitude, gym_latitude, gym_longitude):
        if gym_id not in self.cache:
            response_gym_details = self.bot.api.get_gym_details(
                gym_id=gym_id,
                player_latitude=player_latitude,
                player_longitude=player_longitude,
                gym_latitude=gym_latitude,
                gym_longitude=gym_longitude
            )

            self.cache[gym_id] = response_gym_details

        gym_info = self.cache[gym_id]
        gym_info['last_accessed'] = time.time()

        self._remove_stale_gyms()
        return gym_info

    def _remove_stale_gyms(self):
        for gym_id, gym_details in self.cache.items():
            if gym_details['last_accessed'] < time.time() - self.cache_length_seconds:
                del self.cache[gym_id]


