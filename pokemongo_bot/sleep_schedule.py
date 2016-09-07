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

    SCHEDULING_MARGIN = timedelta(minutes=10)    # Skip if next sleep is SCHEDULING_MARGIN from now

    def __init__(self, bot, config):
        self.bot = bot
        self._last_reminder = datetime.now()
        self._reminder_interval = self.bot.config.sleep_reminder_interval
        self._last_index = -1
        self._next_index = -1
        self._process_config(config)
        self._schedule_next_sleep()

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

    def _time_fmt(self, value):
       ret = ""
       if isinstance(value, datetime):
           ret = value.strftime("%H:%M:%S")
       elif isinstance(value, (int, float)):
           h, m = divmod(value, 3600)
           m, s = divmod(m, 60)
           ret = "%02d:%02d:%02d" % (h, m, s)
       return ret


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
        self._next_sleep, self._next_duration, self._next_end, self._wake_up_at_location, sleep_now = self._get_next_sleep_schedule()

        if not sleep_now:
            self.bot.event_manager.emit(
                'next_sleep',
                sender=self,
                formatted="Next sleep at {time}, for a duration of {duration}",
                data={
                    'time': self._time_fmt(self._next_sleep),
                    'duration': self._time_fmt(self._next_duration)
                }
            )
            self._last_reminder = datetime.now()

    def _should_sleep_now(self):
        now = datetime.now()

        if now >= self._next_sleep and now < self._next_end:
            self._next_duration = (self._next_end - now).total_seconds()
            return True

        diff = now - self._last_reminder
        if (diff.total_seconds() >= self._reminder_interval):
            self.bot.event_manager.emit(
                'next_sleep',
                sender=self,
                formatted="Next sleep at {time}, for a duration of {duration}",
                data={
                    'time': self._time_fmt(self._next_sleep),
                    'duration': self._time_fmt(self._next_duration)
                }
            )
            self._last_reminder = now

        return False

    def _get_next_sleep_schedule(self):
        now = datetime.now()

        times = []
        for index in range(len(self.entries)):
            next_time = now.replace(hour=self.entries[index]['time'].hour, minute=self.entries[index]['time'].minute)
            next_time += timedelta(seconds=self._get_random_offset(self.entries[index]['time_random_offset']))

            next_duration = self._get_next_duration(self.entries[index])

            next_end = next_time + timedelta(seconds=next_duration)

            prev_day_time = next_time - timedelta(days=1)
            prev_day_end = next_end - timedelta(days=1)

            location = self.entries[index]['wake_up_at_location'] if 'wake_up_at_location' in self.entries[index] else ''

            diff = next_time - now

            # Edge case if sleep time has started previous day
            if (prev_day_time <= now and now < prev_day_end):
                self._next_index = index
                return prev_day_time, next_duration, prev_day_end, location, True
            # If sleep time is passed or time to sleep less than SCHEDULING_MARGIN then add one day
            elif (next_time <= now and now > next_end) or (diff > timedelta(0) and diff < self.SCHEDULING_MARGIN):
                next_time += timedelta(days=1)
                next_end += timedelta(days=1)
                diff = next_time - now
            # If now is sleeping time
            elif next_time <= now and now < next_end:
                if index == self._last_index: # If it is still the same sleep entry, but now < next_end because of random offset
                    next_time += timedelta(days=1)
                    next_end += timedelta(days=1)
                    diff = next_time - now
                else:
                    self._next_index = index
                    return next_time, next_duration, next_end, location, True

            prepared = {'index': index, 'time': next_time, 'duration': next_duration, 'end': next_end, 'location': location, 'diff': diff}
            times.append(prepared)

        closest = min(times, key=lambda x: x['diff'])
        self._next_index = closest['index']

        return closest['time'], closest['duration'], closest['end'], closest['location'], False

    def _get_next_duration(self, entry):
        duration = entry['duration'] + self._get_random_offset(entry['duration_random_offset'])
        return duration

    def _get_random_offset(self, max_offset):
        offset = uniform(-max_offset, max_offset)
        return int(offset)

    def _sleep(self):
        sleep_to_go = self._next_duration

        sleep_hms = self._time_fmt(self._next_duration)

        now = datetime.now()
        wake = self._time_fmt(now + timedelta(seconds=sleep_to_go))

        self.bot.event_manager.emit(
            'bot_sleep',
            sender=self,
            formatted="Sleeping for {time_hms}, wake at {wake}",
            data={
                'time_hms': sleep_hms,
                'wake': wake
            }
        )

        sleep(sleep_to_go)
        self._last_index = self._next_index
