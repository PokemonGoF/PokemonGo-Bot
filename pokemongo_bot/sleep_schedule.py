from datetime import datetime, timedelta
from time import sleep
from random import uniform


class SleepSchedule(object):
    """Pauses the execution of the bot every day for some time

    Simulates the user going to sleep every day for some time, the sleep time
    and the duration is changed every day by a random offset defined in the
    config file
    Example Config:
    "sleep_schedule": {
      "enabled": true,
      "enable_reminder": false,
      "reminder_interval": 600,
      "entries": [
        {
          "enabled": true,
          "time": "12:00",
          "duration": "5:30",
          "time_random_offset": "00:30",
          "duration_random_offset": "00:30",
          "wake_up_at_location": ""
        },
        {
          "enabled": true,
          "time": "17:45",
          "duration": "3:00",
          "time_random_offset": "01:00",
          "duration_random_offset": "00:30",
          "wake_up_at_location": ""
        }
      ]
    }
    enabled: (true | false) enables/disables SleepSchedule. Inside of entry will enable/disable single entry, but will not override global value. Default: true
    enable_reminder: (true | false) enables/disables sleep reminder. Default: false
    reminder_interval: (interval) reminder interval in seconds. Default: 600

    enabled: (true | false) see above
    time: (HH:MM) local time that the bot should sleep
    duration: (HH:MM) the duration of sleep
    time_random_offset: (HH:MM) random offset of time that the sleep will start
                        for this example the possible start times are 11:30-12:30 and 16:45-18:45
                        default: 01:00
    duration_random_offset: (HH:MM) random offset of duration of sleep
                        for this example the possible durations are 5:00-6:00 and 2:30-3:30
                        default: 00:30
    wake_up_at_location: (lat, long | lat, long, alt | "") the location at which the bot wake up
    *Note that an empty string ("") will not change the location*.    """

    SCHEDULING_MARGIN = timedelta(minutes=10)    # Skip if next sleep is SCHEDULING_MARGIN from now

    def __init__(self, bot, config):
        self.bot = bot
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
                    msg = "Wake up location found: {location} {position}"
                    self.bot.event_manager.emit(
                        'location_found',
                        sender=self,
                        level='info',
                        formatted=msg,
                        data={
                            'location': wake_up_at_location['raw'],
                            'position': wake_up_at_location['coord']
                        }
                    )

                    self.bot.api.set_position(*wake_up_at_location['coord'])

                    self.bot.event_manager.emit(
                        'position_update',
                        sender=self,
                        level='info',
                        formatted="Now at {current_position}",
                        data={
                            'current_position': self.bot.position,
                            'last_position': '',
                            'distance': '',
                            'distance_unit': ''
                        }
                    )
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

        def testkey(entry, key, offset=False, defval=''):
            if not key in entry:
                index = config.index(entry) + 1
                if not offset:
                    raise ValueError('SleepSchedule: No "%s" key found in entry %d' % (key, index))
                else:
                    self.bot.logger.warning('SleepSchedule: No "%s" key found in entry %d, using default value (%s)' % (key, index, defval))

        self.entries = []

        if 'enabled' in config and config['enabled'] == False: return

        if 'enable_reminder' in config and config['enable_reminder'] == True:
            self._enable_reminder = True
            self._reminder_interval = config['reminder_interval'] if 'reminder_interval' in config else 600
        else:
            self._enable_reminder = False

        if not 'entries' in config:
            self.bot.logger.warning('SleepSchedule is disabled. Config structure has been changed, see docs/configuration_files.md for more information')
            return

        for entry in config['entries']:
            if 'enabled' in entry and entry['enabled'] == False: continue

            prepared = {}

            testkey(entry, 'time')
            prepared['time'] = datetime.strptime(entry['time'], '%H:%M')

            testkey(entry, 'duration')
            raw_duration = datetime.strptime(entry['duration'], '%H:%M')
            duration = int(timedelta(hours=raw_duration.hour, minutes=raw_duration.minute).total_seconds())

            testkey(entry, 'time_random_offset', offset=True, defval='01:00')
            raw_time_random_offset = datetime.strptime(entry['time_random_offset'] if 'time_random_offset' in entry else '01:00', '%H:%M')
            time_random_offset = int(
                timedelta(
                    hours=raw_time_random_offset.hour, minutes=raw_time_random_offset.minute).total_seconds())

            testkey(entry, 'duration_random_offset', offset=True, defval='00:30')
            raw_duration_random_offset = datetime.strptime(entry['duration_random_offset'] if 'duration_random_offset' in entry else '00:30', '%H:%M')
            duration_random_offset = int(
                timedelta(
                    hours=raw_duration_random_offset.hour, minutes=raw_duration_random_offset.minute).total_seconds())

            raw_wake_up_at_location = entry['wake_up_at_location'] if 'wake_up_at_location' in entry else None
            if raw_wake_up_at_location:
                try:
                    wake_up_at_location = self.bot.get_pos_by_name(raw_wake_up_at_location)
                    lat = float(wake_up_at_location[0])
                    lng = float(wake_up_at_location[1])
                    alt = float(wake_up_at_location[2]) if wake_up_at_location[2] else uniform(self.bot.config.alt_min, self.bot.config.alt_max)
                    prepared['wake_up_at_location'] = { 'raw': raw_wake_up_at_location, 'coord': (lat, lng, alt) }
                except:
                    index = config.index(entry)
                    self.bot.warning('SleepSchedule: error parsing wake_up_at_location in entry %d' % index)

            prepared['duration'] = duration
            prepared['time_random_offset'] = time_random_offset
            prepared['duration_random_offset'] = duration_random_offset
            self.entries.append(prepared)

        if not len(self.entries): self.bot.logger.warning('SleepSchedule is disabled')

    def _schedule_next_sleep(self):
        if not len(self.entries): return

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
            if self._enable_reminder: self._last_reminder = datetime.now()

    def _should_sleep_now(self):
        if not len(self.entries): return False

        now = datetime.now()

        if now >= self._next_sleep and now < self._next_end:
            self._next_duration = (self._next_end - now).total_seconds()
            return True

        if self._enable_reminder:
            diff = now - self._last_reminder
            if (diff.total_seconds() >= self._reminder_interval):
                self.bot.event_manager.emit(
                    'next_sleep',
                    sender=self,
                    formatted="Next sleep at {time}, for a duration of {duration}",
                    data={
                        'time': str(self._next_sleep.strftime("%H:%M:%S")),
                        'duration': str(timedelta(seconds=self._next_duration))
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

            location = self.entries[index]['wake_up_at_location'] if 'wake_up_at_location' in self.entries[index] else None

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
