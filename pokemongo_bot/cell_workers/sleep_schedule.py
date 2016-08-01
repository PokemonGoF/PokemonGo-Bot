from datetime import datetime, timedelta
from time import sleep
from random import uniform
from pokemongo_bot import logger
from pokemongo_bot.cell_workers.base_task import BaseTask


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
        }
    }
    time: (HH:MM) local time that the bot should sleep
    duration: (HH:MM) the duration of sleep
    time_random_offset: (HH:MM) random offset of time that the sleep will start
                        for this example the possible start time is 11:30-12:30
    duration_random_offset: (HH:MM) random offset of duration of sleep
                        for this example the possible duration is 5:00-6:00
    """

    LOG_INTERVAL_SECONDS = 600
    SCHEDULING_MARGIN = timedelta(minutes=10)    # Skip if next sleep is RESCHEDULING_MARGIN from now

    def initialize(self):
        # self.bot.event_manager.register_event('sleeper_scheduled', parameters=('datetime',))
        self._process_config()
        self._schedule_next_sleep()

    def work(self):
        if datetime.now() >= self._next_sleep:
            self._sleep()
            self._schedule_next_sleep()
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

    def _schedule_next_sleep(self):
        self._next_sleep = self._get_next_sleep_schedule()
        self._next_duration = self._get_next_duration()
        logger.log('SleepSchedule: next sleep at {}'.format(str(self._next_sleep)), color='green')

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
        logger.log('It\'s time for sleep.')
        while sleep_to_go > 0:
            logger.log('Sleeping for {} more seconds'.format(sleep_to_go), 'yellow')
            if sleep_to_go < self.LOG_INTERVAL_SECONDS:
                sleep(sleep_to_go)
                sleep_to_go = 0
            else:
                sleep(self.LOG_INTERVAL_SECONDS)
                sleep_to_go -= self.LOG_INTERVAL_SECONDS
