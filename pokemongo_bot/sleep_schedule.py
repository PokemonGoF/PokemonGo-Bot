from datetime import datetime, timedelta
from time import sleep
from random import uniform


class SleepSchedule(object):
    """Pauses the execution of the bot every day for some time

    Simulates the user going to sleep every day for some time, the sleep time
    and the duration is changed every day by a random offset defined in the
    config file
    Example Config:
    "sleep_schedule": [
      {
        "time": "12:00",
        "duration": "5:30",
        "time_random_offset": "00:30",
        "duration_random_offset": "00:30",
        "wake_up_at_location": ""
      },
      {
        "time": "17:45",
        "duration": "3:00",
        "time_random_offset": "01:00",
        "duration_random_offset": "00:30",
        "wake_up_at_location": ""
      }
    ]
    time: (HH:MM) local time that the bot should sleep
    duration: (HH:MM) the duration of sleep
    time_random_offset: (HH:MM) random offset of time that the sleep will start
                        for this example the possible start time is 11:30-12:30
    duration_random_offset: (HH:MM) random offset of duration of sleep
                        for this example the possible duration is 5:00-6:00
    wake_up_at_location: (lat, long | lat, long, alt | "") the location at which the bot wake up 
    *Note that an empty string ("") will not change the location*.    """

    LOG_INTERVAL_SECONDS = 600
    SCHEDULING_MARGIN = timedelta(minutes=10)    # Skip if next sleep is RESCHEDULING_MARGIN from now

    def __init__(self, bot, config):
        self.bot = bot
        self._process_config(config)
        self._schedule_next_sleep()
        self._calculate_current_sleep()

    def work(self):
        if self._should_sleep_now():
            self._sleep()
            wake_up_at_location = self._wake_up_at_location
            self._schedule_next_sleep()
            if wake_up_at_location:
                if hasattr(self.bot, 'api'): # Check if api is already initialized
                    self.bot.api.set_position(wake_up_at_location[0],wake_up_at_location[1],wake_up_at_location[2])
                else:
                    self.bot.wake_location = wake_up_at_location
            if hasattr(self.bot, 'api'): self.bot.login() # Same here


    def _process_config(self, config):
        self.entries = []
        for entry in config:
            prepared = {}
            prepared['time'] = datetime.strptime(entry['time'] if 'time' in entry else '01:00', '%H:%M')

            # Using datetime for easier stripping of timedeltas
            raw_duration = datetime.strptime(entry['duration'] if 'duration' in entry else '07:00', '%H:%M')
            duration = int(timedelta(hours=raw_duration.hour, minutes=raw_duration.minute).total_seconds())

            raw_time_random_offset = datetime.strptime(entry['time_random_offset'] if 'time_random_offset' in entry else '01:00', '%H:%M')
            time_random_offset = int(
                timedelta(
                    hours=raw_time_random_offset.hour, minutes=raw_time_random_offset.minute).total_seconds())

            raw_duration_random_offset = datetime.strptime(entry['duration_random_offset'] if 'duration_random_offset' in entry else '00:30', '%H:%M')
            duration_random_offset = int(
                timedelta(
                    hours=raw_duration_random_offset.hour, minutes=raw_duration_random_offset.minute).total_seconds())

            raw_wake_up_at_location = entry['wake_up_at_location'] if 'wake_up_at_location' in entry else ''
            if raw_wake_up_at_location:
                try:
                    wake_up_at_location = raw_wake_up_at_location.split(',',2)
                    lat=float(wake_up_at_location[0])
                    lng=float(wake_up_at_location[1])
                    if len(wake_up_at_location) == 3:
                        alt=float(wake_up_at_location[2])
                    else:
                        alt = uniform(self.bot.config.alt_min, self.bot.config.alt_max)
                except ValueError:
                    raise ValueError('SleepSchedule wake_up_at_location, parsing error in location') #TODO there must be a more elegant way to do it...

                prepared['wake_up_at_location'] = [lat, lng, alt]
            prepared['duration'] = duration
            prepared['time_random_offset'] = time_random_offset
            prepared['duration_random_offset'] = duration_random_offset
            self.entries.append(prepared)

    def _schedule_next_sleep(self):
        self._next_sleep, self._next_duration, self._wake_up_at_location = self._get_next_sleep_schedule()
        self.bot.event_manager.emit(
            'next_sleep',
            sender=self,
            formatted="Next sleep at {time}",
            data={
                'time': str(self._next_sleep)
            }
        )

    def _calculate_current_sleep(self):
        self._current_sleep = self._next_sleep - timedelta(days=1)
        current_duration = self._next_duration
        self._current_end = self._current_sleep + timedelta(seconds = current_duration)

    def _should_sleep_now(self):
        if datetime.now() >= self._next_sleep:
            return True
        if datetime.now() >= self._current_sleep and datetime.now() < self._current_end:
            self._next_duration = (self._current_end - datetime.now()).total_seconds()
            return True

        return False

    def _get_next_sleep_schedule(self):
        now = datetime.now() + self.SCHEDULING_MARGIN

        times = []
        for index in range(len(self.entries)):
            next_time = now.replace(hour=self.entries[index]['time'].hour, minute=self.entries[index]['time'].minute)
            next_time += timedelta(seconds=self._get_random_offset(self.entries[index]['time_random_offset']))

            # If sleep time is passed add one day
            if next_time <= now:
                next_time += timedelta(days=1)

            times.append(next_time)

        diffs = {}
        for index in range(len(self.entries)):
          diff = (times[index]-now).total_seconds()
          if diff >= 0: diffs[index] = diff

        closest = min(diffs.iterkeys(), key=lambda x: diffs[x])

        next_time = times[closest]
        next_duration = self._get_next_duration(self.entries[closest])
        location = self.entries[closest]['wake_up_at_location'] if 'wake_up_at_location' in self.entries[closest] else ''

        return next_time, next_duration, location

    def _get_next_duration(self, entry):
        duration = entry['duration'] + self._get_random_offset(entry['duration_random_offset'])
        return duration

    def _get_random_offset(self, max_offset):
        offset = uniform(-max_offset, max_offset)
        return int(offset)

    def _sleep(self):
        sleep_to_go = self._next_duration

        sleep_m, sleep_s = divmod(sleep_to_go, 60)
        sleep_h, sleep_m = divmod(sleep_m, 60)
        sleep_hms = '%02d:%02d:%02d' % (sleep_h, sleep_m, sleep_s)

        now = datetime.now()
        wake = str(now + timedelta(seconds=sleep_to_go))

        self.bot.event_manager.emit(
            'bot_sleep',
            sender=self,
            formatted="Sleeping for {time_hms}, wake at {wake}",
            data={
                'time_hms': sleep_hms,
                'wake': wake
            }
        )
        while sleep_to_go > 0:
            if sleep_to_go < self.LOG_INTERVAL_SECONDS:
                sleep(sleep_to_go)
                sleep_to_go = 0
            else:
                sleep(self.LOG_INTERVAL_SECONDS)
                sleep_to_go -= self.LOG_INTERVAL_SECONDS
