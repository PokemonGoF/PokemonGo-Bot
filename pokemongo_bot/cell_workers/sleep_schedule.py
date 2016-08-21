from datetime import datetime, timedelta
from time import sleep
from random import uniform
from pokemongo_bot.base_task import BaseTask


class SleepSchedule(BaseTask):
    """Pauses the execution of the bot every day for some time

    Simulates the user going to sleep every day for some time, the sleep time
    and the duration is changed every day by a random offset defined in the
    config file
    Example Config:
    {
        "type": "SleepSchedule",
        "config": {
          "time": "12:00",
          "duration":"5:30",
          "time_random_offset": "00:30",
          "duration_random_offset": "00:30"
          "wake_up_at_location": ""
        }
    }
    time: (HH:MM) local time that the bot should sleep
    duration: (HH:MM) the duration of sleep
    time_random_offset: (HH:MM) random offset of time that the sleep will start
                        for this example the possible start time is 11:30-12:30
    duration_random_offset: (HH:MM) random offset of duration of sleep
                        for this example the possible duration is 5:00-6:00
    wake_up_at_location: (lat, long | lat, long, alt | "") the location at which the bot wake up 
    *Note that an empty string ("") will not change the location*.    """
    SUPPORTED_TASK_API_VERSION = 1

    LOG_INTERVAL_SECONDS = 600
    SCHEDULING_MARGIN = timedelta(minutes=10)    # Skip if next sleep is RESCHEDULING_MARGIN from now

    def initialize(self):
        # self.bot.event_manager.register_event('sleeper_scheduled', parameters=('datetime',))
        self._process_config()
        self._schedule_next_sleep()
        self._calculate_current_sleep()

    def work(self):
        if self._should_sleep_now():
            self._sleep()
            self._schedule_next_sleep()
            wake_up_at_location = self.config.get("wake_up_at_location", "")
            if wake_up_at_location:
                self.bot.api.set_position(self.wake_up_at_location[0],self.wake_up_at_location[1],self.wake_up_at_location[2])
            self.bot.login()

    def _process_config(self):
        self.time = datetime.strptime(self.config.get('time', '01:00'), '%H:%M')

        # Using datetime for easier stripping of timedeltas
        duration = datetime.strptime(self.config.get('duration', '07:00'), '%H:%M')
        self.duration = int(timedelta(hours=duration.hour, minutes=duration.minute).total_seconds())

        time_random_offset = datetime.strptime(self.config.get('time_random_offset', '01:00'), '%H:%M')
        self.time_random_offset = int(
            timedelta(
                hours=time_random_offset.hour, minutes=time_random_offset.minute).total_seconds())

        duration_random_offset = datetime.strptime(self.config.get('duration_random_offset', '00:30'), '%H:%M')
        self.duration_random_offset = int(
            timedelta(
                hours=duration_random_offset.hour, minutes=duration_random_offset.minute).total_seconds())
        
        wake_up_at_location = self.config.get("wake_up_at_location", "")
        if wake_up_at_location:
            try:
                wake_up_at_location = wake_up_at_location.split(',',2)               
                lat=float(wake_up_at_location[0])
                lng=float(wake_up_at_location[1])
                if len(wake_up_at_location) == 3:
                    alt=float(wake_up_at_location[2])
                else:
                    alt = uniform(self.bot.config.alt_min, self.bot.config.alt_max)
            except ValueError:
                raise ValueError('SleepSchedule wake_up_at_location, parsing error in location') #TODO there must be a more elegant way to do it...

            self.wake_up_at_location = [lat, lng, alt]

    def _schedule_next_sleep(self):
        self._next_sleep = self._get_next_sleep_schedule()
        self._next_duration = self._get_next_duration()
        self.emit_event(
            'next_sleep',
            formatted="Next sleep at {time}",
            data={
                'time': str(self._next_sleep)
            }
        )

    def _calculate_current_sleep(self):
        self._current_sleep = self._next_sleep - timedelta(days=1)
        current_duration = self._get_next_duration()
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
        next_time = now.replace(hour=self.time.hour, minute=self.time.minute)

        next_time += timedelta(seconds=self._get_random_offset(self.time_random_offset))

        # If sleep time is passed add one day
        if next_time <= now:
            next_time += timedelta(days=1)

        return next_time

    def _get_next_duration(self):
        duration = self.duration + self._get_random_offset(self.duration_random_offset)
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

        self.emit_event(
            'bot_sleep',
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
