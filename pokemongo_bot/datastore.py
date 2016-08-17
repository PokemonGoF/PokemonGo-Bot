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

BACKEND = _DEFAULT
DATABASE = _DEFAULT

def _init_database(connection_string=':memory:', driver='sqlite'):
    global BACKEND, DATABASE

    if DATABASE is _DEFAULT:
        BACKEND = get_backend('{driver}://{conn}'.format(driver=driver, conn=connection_string))
        DATABASE = BACKEND.connection

    return DATABASE

class Datastore(object):
    MIGRATIONS_PATH = _DEFAULT

    def __init__(self, *args, **kwargs):
        """
        When a subclass is initiated, the migrations should automatically be run.
        """
        if _DEFAULT in (BACKEND, DATABASE):
            raise RuntimeError('Migration database connection not setup. Need to run `_init_database`')

        # Init parents with additional params we may have received
        super(Datastore, self).__init__(*args, **kwargs)

        path = self.MIGRATIONS_PATH

        if path is _DEFAULT:
            # `migrations` should be a sub directory of the calling package, unless a path is specified
            filename = inspect.stack()[1][1]
            path = os.path.join(os.path.dirname(filename), 'migrations')
        elif not os.path.isdir(str(path)):
            raise RuntimeError('The migrations directory does not exist')

        try:
            migrations = read_migrations(path)
            BACKEND.apply_migrations(BACKEND.to_apply(migrations))
        except (IOError, OSError):
            """
            If `migrations` directory is not present, then whatever is subclassing
            us will not have any DB schemas to load.
            """
            pass
