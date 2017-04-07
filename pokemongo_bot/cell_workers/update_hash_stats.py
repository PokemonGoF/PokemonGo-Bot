from datetime import datetime, timedelta
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.tree_config_builder import ConfigException
from pokemongo_bot.worker_result import WorkerResult

from pgoapi.hash_server import HashServer

class UpdateHashStats(BaseTask):
    """
    Periodically displays the hash stats in the terminal.
    Time return is UTC format.
    
    Example config :
    {
        "type": "UpdateHashStats",
        "config": {
            "enabled": true,
            "min_interval": 60,
            "stats": ["period", "remaining", "maximum", "expiration"]
        }
    }

    min_interval : The minimum interval at which the stats are displayed,
                   in seconds (defaults to 60 seconds).
                   The update interval cannot be accurate as workers run synchronously.
    stats : An array of stats to display and their display order (implicitly),
            see available stats below (defaults to ["period", "remaining", "maximum", "expiration"]).
    """
    SUPPORTED_TASK_API_VERSION = 1
    
    def initialize(self):
        self.next_update = None
        self.enabled = self.config.get("enabled",False)
        self.min_interval = self.config.get("min_interval", 60)
        self.displayed_stats = self.config.get('stats', ["period", "remaining", "maximum", "expiration"])
        
        self.bot.event_manager.register_event('log_hash_stats', parameters=('stats'))
    
    def work(self):
        if not self._should_display() and self.enabled:
            return WorkerResult.SUCCESS
            
        line = self._get_stats_line()
        
        if not line:
            return WorkerResult.SUCCESS
        
        self._log_on_terminal(line)
        return WorkerResult.SUCCESS
    
    def _log_on_terminal(self, stats):
        """
        Logs the stats into the terminal using an event.
        :param stats: The stats to display.
        :type stats: string
        :return: Nothing.
        :rtype: None
        """
        self.emit_event(
            'log_hash_stats',
            formatted="{stats}",
            data={
                'stats': stats
            }
        )
        self._compute_next_update()
    
    def _get_stats_line(self):
        """
        Generates a stats string with the given player stats according to the configuration.
        :return: A string containing human-readable stats, ready to be displayed.
        :rtype: string
        """
        
        # self.logger.info(format(HashServer.status.get('period', 0)))
        # self.logger.info(format(HashServer.status.get('remaining', 0)))
        # self.logger.info(format(HashServer.status.get('maximum', 0)))
        # self.logger.info(format(HashServer.status.get('expiration', 0)))
        
        # Create stats strings.
        available_stats = {
            'period': 'Period: {}'.format(datetime.utcfromtimestamp(HashServer.status.get('period', 0))),
            'remaining': 'Remaining: {}'.format(HashServer.status.get('remaining', 0)),
            'maximum': 'Maximum: {}'.format(HashServer.status.get('maximum', 0)),
            'expiration': 'Expiration: {}'.format(datetime.utcfromtimestamp(HashServer.status.get('expiration', 0)))
        }
        def get_stat(stat):
            """
            Fetches a stat string from the available stats dictionary.
            :param stat: The stat name.
            :type stat: string
            :return: The generated stat string.
            :rtype: string
            :raise: ConfigException: When the provided stat string isn't in the available stats
            dictionary.
            """
            if stat not in available_stats:
                raise ConfigException("Stat '{}' isn't available for displaying".format(stat))
            return available_stats[stat]
            
        line = ' | '.join(map(get_stat, self.displayed_stats))
        
        return line
    
    def _should_display(self):
        """
        Returns a value indicating whether the stats should be displayed.
        :return: True if the stats should be displayed; otherwise, False.
        :rtype: bool
        """
        return self.next_update is None or datetime.now() >= self.next_update

    def _compute_next_update(self):
        """
        Computes the next update datetime based on the minimum update interval.
        :return: Nothing.
        :rtype: None
        """
        self.next_update = datetime.now() + timedelta(seconds=self.min_interval)