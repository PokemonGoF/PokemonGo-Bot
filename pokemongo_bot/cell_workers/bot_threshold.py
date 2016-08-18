from datetime import datetime, timedelta
from time import sleep
from random import uniform, randint
from pokemongo_bot.base_task import BaseTask

class BotThreshold(BaseTask):
    """Pauses the execution of the bot after some configured threshold for anti-detection purposes

    Example Config:
    {
        "type": "BotThreshold",
        "config": {
          "enabled": true,
          "duration":"18:30",
          "duration_random_offset": "00:30"
          "min_pokemon_caught": 500,
          "max_pokemon_caught": 900,
          "min_pokestop_spun": 1000,
          "max_pokestop_spun": 1900
        }
    }
    duration: (HH:MM) the duration of rest time
    duration_random_offset: (HH:MM) random offset of duration of rest
                        for this example the possible duration is 18 hours to 19 hours
    min_pokemon_caught: (0-inf) minimum number of pokemon to capture before going to rest
    max_pokemon_caught: (0-inf) maximum number of pokemon to capture before going to rest
    min_pokestop_spun: (0-inf) minimum number of pokestops to spin before going to rest
    max_pokestop_spun: (0-inf) minimum number of pokestops to spin before going to rest
    """
    SUPPORTED_TASK_API_VERSION = 1
    LOG_INTERVAL_SECONDS = 600

    def initialize(self):
        self._process_config()
        self._calculate_threshold()

    def work(self):
        if self._should_rest_now():
            self._rest()
            raise Exception("Resetting metrics for next run of BotThreshold")

    def _process_config(self):
        # Using datetime for easier stripping of timedeltas
        duration = datetime.strptime(self.config.get('duration', '18:30'), '%H:%M')
        self.duration = int(timedelta(hours=duration.hour, minutes=duration.minute).total_seconds())

        duration_random_offset = datetime.strptime(self.config.get('duration_random_offset', '00:30'), '%H:%M')
        self.duration_random_offset = int(
            timedelta(
                hours=duration_random_offset.hour, minutes=duration_random_offset.minute).total_seconds())

        self.min_pokemon_caught = self.config.get('min_pokemon_caught', 500)
        self.max_pokemon_caught = self.config.get('max_pokemon_caught', 900)
        self.min_pokestop_spun = self.config.get('min_pokestop_spun', 1000)
        self.max_pokestop_spun = self.config.get('max_pokestop_spun', 1900)

    def _calculate_threshold(self):
        self._rest_duration = self._get_rest_duration()
        self._pokemon_threshold = self._calculate_pokemon_threshold()
        self._pokestop_threshold = self._calculate_pokestop_threshold()
        self.emit_event(
            'next_rest',
            formatted="Bot will rest after catching {pokemon_threshold} Pokemon or spinning {pokestop_threshold} Pokestops, whichever is earlier",
            data={
                'pokemon_threshold': str(self._pokemon_threshold),
                'pokestop_threshold': str(self._pokestop_threshold)
            }
        )

    def _calculate_pokemon_threshold(self):
        if self.min_pokemon_caught > self.max_pokemon_caught:
            self.min_pokemon_caught, self.max_pokemon_caught = self.max_pokemon_caught, self.min_pokemon_caught
        return randint(self.min_pokemon_caught, self.max_pokemon_caught)

    def _calculate_pokestop_threshold(self):
        if self.min_pokestop_spun > self.max_pokestop_spun:
            self.min_pokestop_spun, self.max_pokestop_spun = self.max_pokestop_spun, self.min_pokestop_spun
        return randint(self.min_pokestop_spun, self.max_pokestop_spun)

    def _should_rest_now(self):
        metrics = self.bot.metrics
        metrics.capture_stats()
        self._captured_pokemon = metrics.num_captures()
        self._visited_pokestop = metrics.num_visits()

        if self._captured_pokemon >= self._pokemon_threshold or self._visited_pokestop >= self._pokestop_threshold:
            return True

        return False

    def _get_rest_duration(self):
        duration = self.duration + self._get_random_offset(self.duration_random_offset)
        return duration

    def _get_random_offset(self, max_offset):
        offset = uniform(-max_offset, max_offset)
        return int(offset)

    def _rest(self):
        rest_to_go = self._rest_duration

        rest_m, rest_s = divmod(rest_to_go, 60)
        rest_h, rest_m = divmod(rest_m, 60)
        rest_hms = '%02d:%02d:%02d' % (rest_h, rest_m, rest_s)

        now = datetime.now()
        resume = str(now + timedelta(seconds=rest_to_go))

        self.emit_event(
            'bot_rest',
            formatted="Captured {captured_pokemon} Pokemon and spun {visited_pokestop} Pokestop(s)! Resting for {time_hms}, resume at {resume}",
            data={
                'captured_pokemon': self._captured_pokemon,
                'visited_pokestop': self._visited_pokestop,
                'time_hms': rest_hms,
                'resume': resume
            }
        )
        while rest_to_go > 0:
            if rest_to_go < self.LOG_INTERVAL_SECONDS:
                sleep(rest_to_go)
                rest_to_go = 0
            else:
                sleep(self.LOG_INTERVAL_SECONDS)
                rest_to_go -= self.LOG_INTERVAL_SECONDS
