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
        self.enabled = True
        self.today = date.today()
        self._schedule = []
        self._last_reminder = None
        self._process_config(config)
        if not self.enabled: return
        self._mkschedule()

    def work(self):
        if not self.enabled: return
        if not self._schedule: self._mkschedule()
        if self._should_sleep_now():
            location = self._schedule[0]['location'] if 'location' in self._schedule[0] else None
            cfg_type = self._schedule[0]['type']
            self._sleep()
            if cfg_type != 'random_alive_pause':
                if location:
                    if hasattr(self.bot, 'api'): # Check if api is already initialized
                        msg = "Wake up location found: {location} {position}"
                        self.bot.event_manager.emit(
                            'location_found',
                            sender=self,
                            level='info',
                            formatted=msg,
                            data={
                                'location': location['raw'],
                                'position': location['coord']
                            }
                        )

                        self.bot.api.set_position(*location['coord'])

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
                        self.bot.wake_location = location
                if hasattr(self.bot, 'api'): self.bot.login() # Same here

    def getSeconds(self, strTime):
        '''
        Return the duration in seconds of a time string
        :param strTime: string time of format %H:%M:%S
        '''
        try:
            x = datetime.strptime(strTime, '%H:%M:%S')
            seconds = int(timedelta(hours=x.hour, minutes=x.minute, seconds=x.second).total_seconds())
        except ValueError:
            seconds = 0

        if seconds < 0:
            seconds = 0

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

        def getkey(key, cfg, cfg_type="", entry=None, defval=""):
            if entry: # Sleep entry processing
                if key in entry:
                    ret = entry[key]
                else:
                    index = cfg.index(entry) + 1
                    if defval:
                        ret = defval
                        self.bot.logger.warning('SleepSchedule: sleep: No "%s" key found in %s entry, using default value (%s)' % (key, cfg_type, defval))
                    else:
                        raise ValueError('SleepSchedule: No "%s" key found in sleep entry %d' % (key, index))
            else: # RandomPause or RandomAlivePause
                if key in cfg:
                    ret = cfg[key]
                else:
                    ret = defval
                    self.bot.logger.warning('SleepSchedule: %s: No "%s" key found, using default value (%s)' % (cfg_type, key, defval))
            return ret

        self.sleep = []
        self.pause = {}
        self.pause['random_pause'] = {}
        self.pause['random_alive_pause'] = {}


        if 'enabled' in config and config['enabled'] == False:
            self.enabled = False
            return

        if 'enable_reminder' in config and config['enable_reminder'] == True:
            self._enable_reminder = True
            self._reminder_interval = config['reminder_interval'] if 'reminder_interval' in config else 600
            self._last_reminder = None
        else:
            self._enable_reminder = False

        if 'entries' in config:
            self.bot.logger.warning('SleepSchedule is disabled. Config structure has been changed, see docs/configuration_files.md for more information')
            self.enabled = False
            return

        if 'sleep' in config:
            cfg = config['sleep']
            for entry in cfg:
                if 'enabled' in entry and entry['enabled'] == False: continue

                prepared = {}

                prepared['time'] = datetime.strptime(getkey('time', cfg, entry=entry), '%H:%M')

                raw_duration = datetime.strptime(getkey('duration', cfg, entry=entry), '%H:%M')
                duration = int(timedelta(hours=raw_duration.hour, minutes=raw_duration.minute).total_seconds())

                raw_time_random_offset = datetime.strptime(getkey('time_random_offset', cfg, entry=entry, defval='01:00'), '%H:%M')
                time_random_offset = int(timedelta(hours=raw_time_random_offset.hour, minutes=raw_time_random_offset.minute).total_seconds())

                raw_duration_random_offset = datetime.strptime(getkey('duration_random_offset', cfg, entry=entry, defval='00:30'), '%H:%M')
                duration_random_offset = int(timedelta(hours=raw_duration_random_offset.hour, minutes=raw_duration_random_offset.minute).total_seconds())

                raw_wake_up_at_location = entry['wake_up_at_location'] if 'wake_up_at_location' in entry else None
                if raw_wake_up_at_location:
                    try:
                        wake_up_at_location = self.bot.get_pos_by_name(raw_wake_up_at_location)
                        lat = float(wake_up_at_location[0])
                        lng = float(wake_up_at_location[1])
                        alt = float(wake_up_at_location[2]) if wake_up_at_location[2] else uniform(self.bot.config.alt_min, self.bot.config.alt_max)
                        prepared['wake_up_at_location'] = {'raw': raw_wake_up_at_location, 'coord': (lat, lng, alt)}
                    except:
                        index = config.index(entry)
                        self.bot.warning('SleepSchedule: sleep: error parsing wake_up_at_location in entry %d' % index)

                prepared['duration'] = duration
                prepared['time_random_offset'] = time_random_offset
                prepared['duration_random_offset'] = duration_random_offset
                self.sleep.append(prepared)

        for cfg_type in ["random_pause", "random_alive_pause"]:
            if cfg_type in config:
                cfg = config[cfg_type]
                if 'enabled' in cfg and cfg['enabled']:
                    raw_min_duration = getkey('min_duration', cfg, cfg_type=cfg_type, defval='00:00:10')
                    self.pause[cfg_type]['min_duration'] = self.getSeconds(raw_min_duration)

                    raw_max_duration = getkey('max_duration', cfg, cfg_type=cfg_type, defval='00:10:00')
                    self.pause[cfg_type]['max_duration'] = self.getSeconds(raw_max_duration)

                    raw_min_interval = getkey('min_interval', cfg, cfg_type=cfg_type, defval='00:05:00')
                    self.pause[cfg_type]['min_interval'] = self.getSeconds(raw_min_interval)

                    raw_max_interval = getkey('max_interval', cfg, cfg_type=cfg_type, defval='01:30:00')
                    self.pause[cfg_type]['max_interval'] = self.getSeconds(raw_max_interval)

                    if self.pause[cfg_type]['min_duration'] > self.pause[cfg_type]['max_duration']:
                        self.bot.logger.warning('SleepSchedule: %s: min_duration is greater than max_duration. %s is disabled' % (cfg_type, cfg_type))
                        self.pause[cfg_type] = {}
                    elif self.pause[cfg_type]['min_interval'] > self.pause[cfg_type]['max_interval']:
                        self.bot.logger.warning('SleepSchedule: %s: min_interval is greater than max_interval, %s is disabled' % (cfg_type, cfg_type))
                        self.pause[cfg_type] = {}

        if (not len(self.sleep)) and (not self.pause['random_pause']) and (not self.pause['random_alive_pause']):
            self.enabled = False
            self.bot.logger.warning('SleepSchedule is disabled')

    def _mkschedule(self, mk_next=False): # Calculating all of sleep/pause triggering this day
        if not mk_next:
            now = datetime.now()
        else:
            now = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)

        times = []
        for index in range(len(self.sleep)):
            sch_time = now.replace(hour=self.sleep[index]['time'].hour, minute=self.sleep[index]['time'].minute)
            sch_time += timedelta(seconds=self._get_random_offset(self.sleep[index]['time_random_offset']))
            sch_duration = self._get_sleep_duration(self.sleep[index])
            sch_end = sch_time + timedelta(seconds=sch_duration)
            prev_day_time = sch_time - timedelta(days=1)
            prev_day_end = sch_end - timedelta(days=1)
            location = self.sleep[index]['wake_up_at_location'] if 'wake_up_at_location' in self.sleep[index] else None

            diff = sch_time - now

            # Edge case if sleep time has started previous day
            if prev_day_time <= now and now < prev_day_end:
                times.append({'type': 'sleep',
                              'start': prev_day_time,
                              'end': prev_day_end,
                              'duration': sch_duration,
                              'location': location})
            elif (sch_time <= now and sch_end > now) or (sch_time > now and diff > self.SCHEDULING_MARGIN):
                times.append({'type': 'sleep',
                              'start': sch_time,
                              'end': sch_end,
                              'duration': sch_duration,
                              'location': location})

        now += self.SCHEDULING_MARGIN
        next_day = self.today + timedelta(days=1)
        for cfg_type in ["random_pause", "random_alive_pause"]:
            if not self.pause[cfg_type]: continue
            sch_time = now + timedelta(seconds=self._get_random_offset(self.pause[cfg_type]['max_interval'], min_offset=self.pause[cfg_type]['min_interval']))
            while sch_time.date() < next_day:
                sch_duration = self._get_random_offset(self.pause[cfg_type]['max_duration'], min_offset=self.pause[cfg_type]['min_duration'])
                sch_end = sch_time + timedelta(seconds=sch_duration)
                times.append({'type': cfg_type,
                              'start': sch_time,
                              'end': sch_end,
                              'duration': sch_duration,
                              'min_duration': self.pause[cfg_type]['min_duration']})
                sch_time = sch_end + timedelta(seconds=self._get_random_offset(self.pause[cfg_type]['max_interval'], min_offset=self.pause[cfg_type]['min_interval']))

        if (self.sleep or self.pause['random_pause'] or self.pause['random_alive_pause']) and not mk_next and not times:
            self._mkschedule(mk_next=True)
            return

        sorted_times = sorted(times, key=lambda k: k['start'])
        new_times = []

        for index in range(len(sorted_times)):
            self.overlay(sorted_times[index], new_times)

        self._schedule = new_times


    def overlay(self, entry, target):
        if entry['duration'] <= 0: return
        if target:
            latest = target[len(target)-1]
            if latest['duration'] <= 0:
                target.remove(latest)
                self.overlay(entry, target)
            elif latest['end'] == entry['start'] and ((latest['type'] == 'random_pause' and entry['type'] == 'random_alive_pause') or (latest['type'] == 'random_alive_pause' and entry['type'] == 'random_pause')):
                target.append(entry)
            elif (latest['end'] + self.SCHEDULING_MARGIN) > entry['start']:
                if latest['type'] == 'sleep' and entry['type'] == 'sleep':
                    latest['end'] = entry['start'] - self.SCHEDULING_MARGIN
                    latest['duration'] = int((latest['end'] - latest['start']).total_seconds())
                    self.overlay(entry, target)
                elif latest['type'] == 'sleep' and (entry['type'] == 'random_pause' or entry['type'] == 'random_alive_pause'):
                    entry['start'] = latest['end'] + self.SCHEDULING_MARGIN
                    entry['duration'] = int((entry['end'] - entry['start']).total_seconds())
                    if entry['duration'] < entry['min_duration']: return
                    self.overlay(entry, target)
                elif (latest['type'] == 'random_pause' or latest['type'] == 'random_alive_pause') and entry['type'] == 'sleep':
                    latest['end'] = entry['start'] - self.SCHEDULING_MARGIN
                    latest['duration'] = int((latest['end'] - latest['start']).total_seconds())
                    if latest['duration'] < latest['min_duration']:
                        target.remove(latest)
                        self.overlay(entry, target)
                elif (latest['type'] == 'random_pause') and (entry['type'] == 'random_alive_pause'):
                    entry['start'] = latest['end']
                    entry['duration'] = int((entry['end'] - entry['start']).total_seconds())
                    if entry['duration'] <= 0: return
                elif (latest['type'] == 'random_alive_pause') and (entry['type'] == 'random_pause'):
                    latest['end'] = entry['start']
                    latest['duration'] = int((latest['end'] - latest['start']).total_seconds())
                    if latest['duration'] <= 0:
                        target.remove(latest)
                        self.overlay(entry, target)
            else:
                target.append(entry)
        else:
            target.append(entry)

    def _should_sleep_now(self):
        entry = self._schedule[0]
        now = datetime.now()

        if now >= entry['end']:
            self._schedule.remove(entry)
            if self._schedule:
                return self._should_sleep_now()
            else:
                return False

        if now >= entry['start'] and now < entry['end']:
            entry['duration'] = (entry['end'] - now).total_seconds()
            return True

        if self._enable_reminder:
            if not self._last_reminder:
                self._last_reminder = now
            diff = now - self._last_reminder
            if (diff.total_seconds() >= self._reminder_interval) or (self._last_reminder == now):
                self.bot.event_manager.emit(
                    'next_sleep',
                    sender=self,
                    formatted="Next %s at {time}, for a duration of {duration}" % entry['type'],
                    data={
                        'time': self._time_fmt(entry['start']),
                        'duration': self._time_fmt(entry['duration'])
                    }
                )
                self._last_reminder = now

        return False

    def _get_sleep_duration(self, entry):
        duration = entry['duration'] + self._get_random_offset(entry['duration_random_offset'])
        return duration

    def _get_random_offset(self, max_offset, min_offset=-1):
        if min_offset < 0:
            offset = uniform(-max_offset, max_offset)
        else:
            offset = uniform(min_offset, max_offset)
        return int(offset)

    def _sleep(self):
        entry = self._schedule[0]
        sleep_to_go = entry['duration']

        sleep_hms = self._time_fmt(entry['duration'])

        now = datetime.now()
        wake = self._time_fmt(now + timedelta(seconds=sleep_to_go))

        if entry['type'] == 'sleep':
            self.bot.event_manager.emit(
                'bot_sleep',
                sender=self,
                formatted="Sleeping for {time_hms}, wake at {wake}",
                data={
                    'time_hms': sleep_hms,
                    'wake': wake
                }
            )
            self.bot.hb_locked = True
            sleep(sleep_to_go)
        elif entry['type'] == 'random_pause':
            self.bot.event_manager.emit(
                'bot_random_pause',
                sender=self,
                formatted="Taking a random break for {time_hms}, will resume at {resume}",
                data={
                    'time_hms': sleep_hms,
                    'resume': wake
                }
            )
            self.bot.hb_locked = True
            sleep(sleep_to_go)
        elif entry['type'] == 'random_alive_pause':
            raw_wake = now + timedelta(seconds=sleep_to_go)
            self.bot.event_manager.emit(
                'bot_random_alive_pause',
                sender=self,
                formatted="Taking a random break keeping bot alive for {time_hms}, will resume at {resume}",
                data={
                    'time_hms': sleep_hms,
                    'resume': wake
                }
            )
            while datetime.now() <= raw_wake:
                sleep(uniform(1, 3))
                if self.bot.config.replicate_gps_xy_noise or self.bot.config.replicate_gps_z_noise: # Adding some noise
                    lat, lng, alt = self.bot.api.get_position()
                    self.bot.api.set_position(lat, lng, alt) # Just set the same _actual_ values. set_position will add noise itself


        end = entry['end']
        self._schedule.remove(entry)
        if self._schedule and self._schedule[0]['end'] == end: self._sleep()
