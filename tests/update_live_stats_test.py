import unittest
from sys import platform as _platform
from datetime import datetime, timedelta
from mock import call, patch, MagicMock
from pokemongo_bot.cell_workers.update_live_stats import UpdateLiveStats
from tests import FakeBot


class UpdateLiveStatsTestCase(unittest.TestCase):
    config = {
        'min_interval': 20,
        'stats': ['login', 'username', 'pokemon_evolved', 'pokemon_encountered', 'uptime',
                  'pokemon_caught', 'stops_visited', 'km_walked', 'level', 'stardust_earned',
                  'level_completion', 'xp_per_hour', 'pokeballs_thrown', 'highest_cp_pokemon',
                  'level_stats', 'xp_earned', 'pokemon_unseen', 'most_perfect_pokemon',
                  'pokemon_stats', 'pokemon_released', 'captures_per_hour'],
        'terminal_log': True,
        'terminal_title': False
    }
    player_stats = {
        'level': 25,
        'prev_level_xp': 1250000,
        'next_level_xp': 1400000,
        'experience': 1337500
    }

    def setUp(self):
        self.bot = FakeBot()
        self.bot._player = {'username': 'Username'}
        self.bot.config.username = 'Login'
        self.worker = UpdateLiveStats(self.bot, self.config)

    def mock_metrics(self):
        self.bot.metrics = MagicMock()
        self.bot.metrics.runtime.return_value = timedelta(hours=15, minutes=42, seconds=13)
        self.bot.metrics.distance_travelled.return_value = 42.05
        self.bot.metrics.xp_per_hour.return_value = 1337.42
        self.bot.metrics.xp_earned.return_value = 424242
        self.bot.metrics.visits = {'latest': 250, 'start': 30}
        self.bot.metrics.num_encounters.return_value = 130
        self.bot.metrics.num_captures.return_value = 120
        self.bot.metrics.captures_per_hour.return_value = 75
        self.bot.metrics.releases = 30
        self.bot.metrics.num_evolutions.return_value = 12
        self.bot.metrics.num_new_mons.return_value = 3
        self.bot.metrics.num_throws.return_value = 145
        self.bot.metrics.earned_dust.return_value = 24069
        self.bot.metrics.highest_cp = {'desc': 'highest_cp'}
        self.bot.metrics.most_perfect = {'desc': 'most_perfect'}

    def test_config(self):
        self.assertEqual(self.worker.min_interval, self.config['min_interval'])
        self.assertEqual(self.worker.displayed_stats, self.config['stats'])
        self.assertEqual(self.worker.terminal_title, self.config['terminal_title'])
        self.assertEqual(self.worker.terminal_log, self.config['terminal_log'])

    def test_should_display_no_next_update(self):
        self.worker.next_update = None

        self.assertTrue(self.worker._should_display())

    @patch('pokemongo_bot.cell_workers.update_live_stats.datetime')
    def test_should_display_no_terminal_log_title(self, mock_datetime):
        # _should_display should return False if both terminal_title and terminal_log are false
        # in configuration, even if we're past next_update.
        now = datetime.now()
        mock_datetime.now.return_value = now + timedelta(seconds=20)
        self.worker.next_update = now
        self.worker.terminal_log = False
        self.worker.terminal_title = False

        self.assertFalse(self.worker._should_display())

    @patch('pokemongo_bot.cell_workers.update_live_stats.datetime')
    def test_should_display_before_next_update(self, mock_datetime):
        now = datetime.now()
        mock_datetime.now.return_value = now - timedelta(seconds=20)
        self.worker.next_update = now

        self.assertFalse(self.worker._should_display())

    @patch('pokemongo_bot.cell_workers.update_live_stats.datetime')
    def test_should_display_after_next_update(self, mock_datetime):
        now = datetime.now()
        mock_datetime.now.return_value = now + timedelta(seconds=20)
        self.worker.next_update = now

        self.assertTrue(self.worker._should_display())

    @patch('pokemongo_bot.cell_workers.update_live_stats.datetime')
    def test_should_display_exactly_next_update(self, mock_datetime):
        now = datetime.now()
        mock_datetime.now.return_value = now
        self.worker.next_update = now

        self.assertTrue(self.worker._should_display())

    @patch('pokemongo_bot.cell_workers.update_live_stats.datetime')
    def test_compute_next_update(self, mock_datetime):
        now = datetime.now()
        mock_datetime.now.return_value = now
        old_next_display_value = self.worker.next_update
        self.worker._compute_next_update()

        self.assertNotEqual(self.worker.next_update, old_next_display_value)
        self.assertEqual(self.worker.next_update,
                         now + timedelta(seconds=self.config['min_interval']))

    @patch('pokemongo_bot.cell_workers.update_live_stats.stdout')
    @patch('pokemongo_bot.cell_workers.UpdateLiveStats._compute_next_update')
    def test_update_title_linux_cygwin(self, mock_compute_next_update, mock_stdout):
        self.worker._update_title('new title linux', 'linux')

        self.assertEqual(mock_stdout.write.call_count, 1)
        self.assertEqual(mock_stdout.write.call_args, call('\x1b]2;new title linux\x07'))
        self.assertEqual(mock_compute_next_update.call_count, 1)

        self.worker._update_title('new title linux2', 'linux2')

        self.assertEqual(mock_stdout.write.call_count, 2)
        self.assertEqual(mock_stdout.write.call_args, call('\x1b]2;new title linux2\x07'))
        self.assertEqual(mock_compute_next_update.call_count, 2)

        self.worker._update_title('new title cygwin', 'cygwin')

        self.assertEqual(mock_stdout.write.call_count, 3)
        self.assertEqual(mock_stdout.write.call_args, call('\x1b]2;new title cygwin\x07'))
        self.assertEqual(mock_compute_next_update.call_count, 3)

    @patch('pokemongo_bot.cell_workers.update_live_stats.stdout')
    @patch('pokemongo_bot.cell_workers.UpdateLiveStats._compute_next_update')
    def test_update_title_darwin(self, mock_compute_next_update, mock_stdout):
        self.worker._update_title('new title darwin', 'darwin')

        self.assertEqual(mock_stdout.write.call_count, 1)
        self.assertEqual(mock_stdout.write.call_args, call('\033]0;new title darwin\007'))
        self.assertEqual(mock_compute_next_update.call_count, 1)

    @unittest.skipUnless(_platform.startswith("win"), "requires Windows")
    @patch('pokemongo_bot.cell_workers.update_live_stats.ctypes')
    @patch('pokemongo_bot.cell_workers.UpdateLiveStats._compute_next_update')
    def test_update_title_win32(self, mock_compute_next_update, mock_ctypes):
        self.worker._update_title('new title win32', 'win32')

        self.assertEqual(mock_ctypes.windll.kernel32.SetConsoleTitleA.call_count, 1)
        self.assertEqual(mock_ctypes.windll.kernel32.SetConsoleTitleA.call_args,
                         call('new title win32'))
        self.assertEqual(mock_compute_next_update.call_count, 1)

    @patch('pokemongo_bot.cell_workers.update_live_stats.BaseTask.emit_event')
    @patch('pokemongo_bot.cell_workers.UpdateLiveStats._compute_next_update')
    def test_log_on_terminal(self, mock_compute_next_update, mock_emit_event):
        self.worker._log_on_terminal('stats')

        self.assertEqual(mock_emit_event.call_count, 1)
        self.assertEqual(mock_emit_event.call_args,
                         call('log_stats', data={'stats': 'stats'}, formatted='{stats}'))
        self.assertEqual(mock_compute_next_update.call_count, 1)

    def test_get_stats_line_player_stats_none(self):
        line = self.worker._get_stats_line(None)

        self.assertEqual(line, '')

    def test_get_stats_line_no_displayed_stats(self):
        self.worker.displayed_stats = []
        line = self.worker._get_stats_line(self.player_stats)

        self.assertEqual(line, '')

    def test_get_stats_line(self):
        self.mock_metrics()

        line = self.worker._get_stats_line(self.player_stats)
        expected = 'Login | Username | Evolved 12 pokemon | Encountered 130 pokemon | ' \
                   'Uptime : 15:42:13 | Caught 120 pokemon | Visited 220 stops | ' \
                   '42.05km walked | Level 25 | Earned 24,069 Stardust | ' \
                   '87,500 / 150,000 XP (58%) | 1,337 XP/h | Threw 145 pokeballs | ' \
                   'Highest CP pokemon : highest_cp | Level 25 (87,500 / 150,000, 58%) | ' \
                   '+424,242 XP | Encountered 3 new pokemon | ' \
                   'Most perfect pokemon : most_perfect | ' \
                   'Encountered 130 pokemon, 120 caught, 30 released, 12 evolved, ' \
                   '3 never seen before | Released 30 pokemon | 75 pokemon/h'

        self.assertEqual(line, expected)
