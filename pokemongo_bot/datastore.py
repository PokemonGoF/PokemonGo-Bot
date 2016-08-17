"""
Use the built-in sqlite3 library as a datastore,

To handle database migrations, use the `yoyo-migrations` package.
For further details on this, see:
https://pypi.python.org/pypi/yoyo-migrations
"""

import inspect
import os
import sys
import warnings

try:
    from yoyo import read_migrations, get_backend
except ImportError:
    warnings.warn('Please run `pip install -r requirements.txt` to ensure you have the latest required packages')
    sys.exit(-1)


_DEFAULT = object()

class DatabaseManager(object):
    def __init__(self, bot):
        self.bot = bot

    @property
    def backend(self):
        return get_backend('sqlite:///data/{}.db'.format(self.bot.config.username))


class Datastore(object):
    MIGRATIONS_PATH = _DEFAULT

    def __init__(self):
        """
        When a subclass is initiated, the migrations should automatically be run.
        """
        path = self.MIGRATIONS_PATH

        if path is _DEFAULT:
            # `migrations` should be a sub directory of the calling package, unless a path is specified
            filename = inspect.stack()[1][1]
            path = os.path.join(os.path.dirname(filename), 'migrations')
        elif not os.path.isdir(str(path)):
            raise RuntimeError('The migrations directory does not exist')

        backend = self.database.backend
        with backend.connection as conn:
            migrations = read_migrations(path)
            backend.apply_migrations(backend.to_apply(migrations))
