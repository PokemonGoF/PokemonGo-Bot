from datetime import datetime as dt, timedelta
from time import sleep
from random import uniform
from pokemongo_bot.base_task import BaseTask


class RandomPause(BaseTask):
    """Pauses the execution of the bot at a random time for a random duration
    
    Simulates the user doing "something random" for some time.
    Example Config:
    {
        "type": "RandomPause",
        "config": {
          "min_duration": "00:00:10",
          "max_duration": "00:10:00",
          "min_interval": "00:05:00",
          "max_interval": "01:30:00"
        }
    }
    
    Inspired from sleep_schedule. 
    ... In retrospect, we could have used a generic class for both.
    """
    SUPPORTED_TASK_API_VERSION = 1

    LOG_INTERVAL_SECONDS = 600
    # At least 15 second of margin, because of login
    SCHEDULING_MARGIN = timedelta(seconds=15)    # Skip if next pause is RESCHEDULING_MARGIN from now

    def initialize(self):
        # self.bot.event_manager.register_event('sleeper_scheduled', parameters=('datetime',))
        self._process_config()
        self._schedule_next_pause()
        #self._calculate_current_pause() #I didn't get it...

    def work(self):
        if self._should_pause_now():
            self._sleep()
            self._schedule_next_pause()
            self.bot.login()


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
            'next_random_pause',
            formatted="Next random pause at {time}, for a duration of {duration}",
            data={
                'time': str(self._next_pause.strftime("%H:%M:%S")),
                'duration': str(timedelta(seconds=self._next_duration))
            }
        )

    def _should_pause_now(self):
        if dt.now() >= (self._next_pause + timedelta(seconds=self._next_duration) + timedelta(seconds=1)):
            self._schedule_next_pause()
            return False
        if dt.now() >= self._next_pause:
            return True

        return False

    def _get_next_pause_schedule(self):
        now = dt.now() + self.SCHEDULING_MARGIN
        next_time = now + timedelta(seconds=int(uniform(self.minInterval, self.maxInterval)))

        # If pause time is passed add one day
        if next_time <= now:
            next_time += timedelta(days=1)

        return next_time

    def _get_next_duration(self):
        duration = int(uniform(self.minDuration, self.maxDuration))
        return duration

    def _sleep(self):
        sleep_to_go = self._next_duration

        sleep_m, sleep_s = divmod(sleep_to_go, 60)
        sleep_h, sleep_m = divmod(sleep_m, 60)
        sleep_hms = '%02d:%02d:%02d' % (sleep_h, sleep_m, sleep_s)

        now = dt.now()
        resume = now + timedelta(seconds=sleep_to_go)

        self.emit_event(
            'bot_random_pause',
            formatted="Taking a random break for {time_hms}, will resume at {resume}",
            data={
                'time_hms': sleep_hms,
                'resume': resume.strftime("%H:%M:%S")
            }
        )
        while sleep_to_go > 0:
            if sleep_to_go < self.LOG_INTERVAL_SECONDS:
                sleep(sleep_to_go)
                sleep_to_go = 0
            else:
                sleep(self.LOG_INTERVAL_SECONDS)
                sleep_to_go -= self.LOG_INTERVAL_SECONDS
