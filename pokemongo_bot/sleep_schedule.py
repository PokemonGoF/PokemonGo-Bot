from datetime import datetime, date, timedelta
from time import sleep
from random import uniform


class SleepSchedule(object):
    """The main class of sleep/pause tasks

    Pauses the execution of the bot for some time using schedule
      and/or at a random time for a random duration
      and/or at a random time for a random duration keeping bot alive

    Example Config:
    "sleep_schedule": {
      "enabled": true,
      "enable_reminder": false,
      "reminder_interval": 600,
      "sleep": [
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
      ],
      "random_pause": {
        "enabled": true,
        "min_duration": "00:00:10",
        "max_duration": "00:10:00",
        "min_interval": "00:05:00",
        "max_interval": "01:30:00"
      },
      "random_alive_pause": {
        "enabled": true,
        "min_duration": "00:00:10",
        "max_duration": "00:10:00",
        "min_interval": "00:05:00",
        "max_interval": "01:30:00"
      }
    }

    enabled: (true | false) enables/disables SleepSchedule. Default: true
    enable_reminder: (true | false) enables/disables sleep/pause reminder. Default: false
    reminder_interval: (interval) reminder interval in seconds. Default: 600

    sleep: bot sleep rules. Default: []
      enabled: (true | false) enables/disables single sleep entry, doesn't override global value. Default: true
      time: (HH:MM) local time that the bot should sleep
      duration: (HH:MM) the duration of sleep
      time_random_offset: (HH:MM) random offset of time that the sleep will start
                          for this example the possible start times are 11:30-12:30 and 16:45-18:45
                          default: 01:00
      duration_random_offset: (HH:MM) random offset of duration of sleep
                          for this example the possible durations are 5:00-6:00 and 2:30-3:30
                          default: 00:30
      wake_up_at_location: (lat, long | lat, long, alt | "") the location at which the bot wake up
      *Note that an empty string ("") will not change the location*.

    random_pause: rules to pause the execution of the bot at a random time for a random duration. Default: {}
      enabled: (true | false) enables/disables random pause feature. Default: true
      min_duration: (HH:MM:SS) minumum duration of the pause. Default: 00:00:10
      max_duration: (HH:MM:SS) maximum duration of the pause. Default: 00:10:00
      min_interval: (HH:MM:SS) minimum interval between pauses. Default: 00:05:00
      max_interval: (HH:MM:SS) maximum interval between pauses. Default: 01:30:00

    random_alive_pause: rules to pause the execution of the bot keeping it alive at a random time for a random duration. Default: {}
      Configuration including default values is the same as random_pause configuration

    """

    SCHEDULING_MARGIN = timedelta(minutes=10)

    def __init__(self, bot, config):
        self.bot = bot
        self._last_index = -1
        self._next_index = -1
        self.today = date.today()
        self._process_config(config)
        self._schedule()

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

    def getSeconds(self, strTime):
        '''
        Return the duration in seconds of a time string
        :param strTime: string time of format %H:%M:%S
        '''
        try:
            x = dt.strptime(strTime, '%H:%M:%S')
            seconds = int(timedelta(hours=x.hour,minutes=x.minute,seconds=x.second).total_seconds())
        except ValueError:
            seconds = 0;

        if seconds < 0:
            seconds = 0;

        return seconds


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

        def testkey(cfg, cfg_type, key, entry=None, warn=False, defval=''):
            if cfg_type == 'sleep':
                if not key in entry:
                    index = cfg.index(entry) + 1
                    if not warn:
                        raise ValueError('SleepSchedule: No "%s" key found in sleep entry %d' % (key, index))
                    else:
                        self.bot.logger.warning('SleepSchedule: No "%s" key found in sleep entry %d, using default value (%s)' % (key, index, defval))
            elif cfg_type == 'random_pause' or cfg_type == 'random_alive_pause':
                if not key in cfg:
                    self.bot.logger.warning('SleepSchedule: No "%s" key found in %s entry, using default value (%s)' % (key, cfg_type, defval))

        self.sleep = []
        self.random_pause = {}
        self.random_alive_pause = {}


        if 'enabled' in config and config['enabled'] == False: return

        if 'enable_reminder' in config and config['enable_reminder'] == True:
            self._enable_reminder = True
            self._reminder_interval = config['reminder_interval'] if 'reminder_interval' in config else 600
        else:
            self._enable_reminder = False

        if 'entries' in config:
            self.bot.logger.warning('SleepSchedule is disabled. Config structure has been changed, see docs/configuration_files.md for more information')
            return

        if 'sleep' in config:
            cfg = config['sleep']
            for entry in cfg:
                if 'enabled' in entry and entry['enabled'] == False: continue

                prepared = {}

                testkey(cfg, 'sleep', 'time', entry=entry)
                prepared['time'] = datetime.strptime(entry['time'], '%H:%M')

                testkey(cfg, 'sleep', 'duration', entry=entry)
                raw_duration = datetime.strptime(entry['duration'], '%H:%M')
                duration = int(timedelta(hours=raw_duration.hour, minutes=raw_duration.minute).total_seconds())

                testkey(cfg, 'sleep', 'time_random_offset', entry=entry, warn=True, defval='01:00')
                raw_time_random_offset = datetime.strptime(entry['time_random_offset'] if 'time_random_offset' in entry else '01:00', '%H:%M')
                time_random_offset = int(timedelta(hours=raw_time_random_offset.hour, minutes=raw_time_random_offset.minute).total_seconds())

                testkey(cfg, 'sleep', 'duration_random_offset', entry=entry, warn=True, defval='00:30')
                raw_duration_random_offset = datetime.strptime(entry['duration_random_offset'] if 'duration_random_offset' in entry else '00:30', '%H:%M')
                duration_random_offset = int(timedelta(hours=raw_duration_random_offset.hour, minutes=raw_duration_random_offset.minute).total_seconds())

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
                self.sleep.append(prepared)

        if "random_pause" in config:
            cfg = config['random_pause']
            if 'enabled' in cfg and cfg['enabled']:
                testkey(cfg, 'random_pause', 'min_duration', defval='00:00:10')
                raw_min_duration = cfg['min_duration'] if 'min_duration' in cfg else '00:00:10'
                self.random_pause['min_duration'] = self.getSeconds(raw_min_duration)

                testkey(cfg, 'random_pause', 'max_duration', defval='00:00:10')
                raw_max_duration = cfg['max_duration'] if 'max_duration' in cfg else '00:10:00'
                self.random_pause['max_duration'] = self.getSeconds(raw_max_duration)

                testkey(cfg, 'random_pause', 'min_interval', defval='00:05:00')
                raw_min_interval = cfg['min_interval'] if 'min_interval' in cfg else '00:05:00'
                self.random_pause['min_interval'] = self.getSeconds(raw_min_interval)

                testkey(cfg, 'random_pause', 'max_interval', defval='01:30:00')
                raw_max_interval = cfg['max_interval'] if 'max_interval' in cfg else '01:30:00'
                self.random_pause['max_interval'] = self.getSeconds(raw_max_interval)

                if self.random_pause['min_duration'] > self.random_pause['max_duration']:
                    self.bot.logger.warning('SleepSchedule: random_pause: min_duration is greater than max_duration. random_pause is disabled')
                    self.random_pause = {}
                elif self.random_pause['min_interval'] > self.random_pause['max_interval']:
                    self.bot.logger.warning('SleepSchedule: random_pause: min_interval is greater than max_interval, random_pause is disabled')
                    self.random_pause = {}

        if "random_alive_pause" in config:
            cfg = config['random_alive_pause']
            if 'enabled' in cfg and cfg['enabled']:
                testkey(cfg, 'random_alive_pause', 'min_duration', defval='00:00:10')
                raw_min_duration = cfg['min_duration'] if 'min_duration' in cfg else '00:00:10'
                self.random_alive_pause['min_duration'] = self.getSeconds(raw_min_duration)

                testkey(cfg, 'random_alive_pause', 'max_duration', defval='00:00:10')
                raw_max_duration = cfg['max_duration'] if 'max_duration' in cfg else '00:10:00'
                self.random_alive_pause['max_duration'] = self.getSeconds(raw_max_duration)

                testkey(cfg, 'random_alive_pause', 'min_interval', defval='00:05:00')
                raw_min_interval = cfg['min_interval'] if 'min_interval' in cfg else '00:05:00'
                self.random_alive_pause['min_interval'] = self.getSeconds(raw_min_interval)

                testkey(cfg, 'random_alive_pause', 'max_interval', defval='01:30:00')
                raw_max_interval = cfg['max_interval'] if 'max_interval' in cfg else '01:30:00'
                self.random_alive_pause['max_interval'] = self.getSeconds(raw_max_interval)

                if self.random_alive_pause['min_duration'] > self.random_alive_pause['max_duration']:
                    self.bot.logger.warning('SleepSchedule: random_alive_pause: min_duration is greater than max_duration. random_alive_pause is disabled')
                    self.random_alive_pause = {}
                elif self.random_alive_pause['min_interval'] > self.random_alive_pause['max_interval']:
                    self.bot.logger.warning('SleepSchedule: random_alive_pause: min_interval is greater than max_interval, random_alive_pause is disabled')
                    self.random_alive_pause = {}


        if (not len(self.sleep)) and (not self.random_pause) and (not self.random_alive_pause): self.bot.logger.warning('SleepSchedule is disabled')

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
