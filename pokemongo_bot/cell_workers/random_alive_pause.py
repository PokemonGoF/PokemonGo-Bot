from datetime import datetime as dt, timedelta
from time import sleep
from random import uniform
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult

class RandomAlivePause(BaseTask):
    """Drops the execution of following bot tasks
    This task MUST be placed on the top of task list

    Simulates the user doing "something random" for some time leaving app launched
    Example Config:
    {
      "type": "RandomAlivePause",
      "config": {
        "min_duration": "00:00:10",
        "max_duration": "00:10:00",
        "min_interval": "00:05:00",
        "max_interval": "01:30:00"
      }
    }

    Based on RandomPause.
    """
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self._sleep_to_go = 0
        self._last_call = None
        self._process_config()
        self._schedule_next_pause()

    def work(self):
        if self._should_pause_now():
            if not self._sleep():
              sleep(1)
              return WorkerResult.RUNNING
            self._schedule_next_pause()


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

    def _process_config(self):
        self.minDuration = self.getSeconds(self.config.get('min_duration', '00:00:10'))
        self.maxDuration = self.getSeconds(self.config.get('max_duration', '00:10:00'))
        self.minInterval = self.getSeconds(self.config.get('min_interval', '00:10:00'))
        self.maxInterval = self.getSeconds(self.config.get('max_interval', '01:10:00'))

        if self.minDuration > self.maxDuration:
            raise ValueError('random pause min_duration is bigger than random pause max_duration') #TODO there must be a more elegant way to do it...
        if self.minInterval > self.maxInterval:
            raise ValueError('random pause min_interval is bigger than random pause max_interval') #TODO there must be a more elegant way to do it...

    def _schedule_next_pause(self):
        '''
        Schedule the time and the duration of the next pause.
        '''
        self._next_pause = self._get_next_pause_schedule()
        self._next_duration = self._get_next_duration()
        self.emit_event(
            'next_random_alive_pause',
            formatted="Next random alive pause at {time}, for a duration of {duration}",
            data={
                'time': str(self._next_pause.strftime("%H:%M:%S")),
                'duration': str(timedelta(seconds=self._next_duration))
            }
        )

    def _should_pause_now(self):
        if self._sleep_to_go > 0: return True

        now = dt.now()
        end = self._next_pause + timedelta(seconds=self._next_duration)
        if now >= self._next_pause and now < end:
            diff = (now - self._next_pause).total_seconds()
            if (self._next_duration - diff) <= 0:
                self._schedule_next_pause()
                return False
            else:
                self._next_duration -= diff
                return True

        return False

    def _get_next_pause_schedule(self):
        now = dt.now()
        next_time = now + timedelta(seconds=int(uniform(self.minInterval, self.maxInterval)))

        # If pause time is passed add one day
        if next_time <= now:
            next_time += timedelta(days=1)

        return next_time

    def _get_next_duration(self):
        duration = int(uniform(self.minDuration, self.maxDuration))
        return duration

    def _sleep(self):
        if self._next_duration <= 0: return True

        now = dt.now()

        if self._sleep_to_go <= 0:
            self._sleep_to_go = self._next_duration

            sleep_m, sleep_s = divmod(self._sleep_to_go, 60)
            sleep_h, sleep_m = divmod(sleep_m, 60)
            sleep_hms = '%02d:%02d:%02d' % (sleep_h, sleep_m, sleep_s)

            resume = now + timedelta(seconds=self._sleep_to_go)

            self.emit_event(
                'bot_random_alive_pause',
                formatted="Taking a random break keeping bot alive for {time_hms}, will resume at {resume}",
                data={
                    'time_hms': sleep_hms,
                    'resume': resume.strftime("%H:%M:%S")
                }
            )

            self._last_call = now
            return False

        self.bot.heartbeat()
        if self.bot.config.replicate_gps_xy_noise or self.bot.config.replicate_gps_z_noise: # Adding some noise
            lat, lng, alt = self.bot.api.get_position()
            self.bot.api.set_position(lat, lng, alt) # Just set the same _actual_ values. set_position will add noise itself

        diff = (now - self._last_call).total_seconds()
        self._last_call = now
        self._sleep_to_go -= diff
        return True if self._sleep_to_go <= 0 else False
