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

DEFAULT_DRIVER = 'sqlite'
DEFAULT_CONN_STR = ':memory:'

class Datastore(object):

    def __init__(self, *args, **kwargs):
        super(Datastore, self).__init__()

        driver = DEFAULT_DRIVER if 'driver' not in kwargs else kwargs['driver']
        conn_str = DEFAULT_CONN_STR if 'conn_str' not in kwargs else kwargs['conn_str']

        self.backend = get_backend('{driver}://{conn}'.format(driver=driver, conn=conn_str))

    def migrate(self, path=None):
        if path is None:
            # `migrations` should be a sub directory of the calling package, unless a path is specified
            filename = inspect.stack()[1][1]
            path = os.path.join(os.path.dirname(filename), 'migrations')
        elif not os.path.isdir(str(path)):
            raise RuntimeError('The migrations directory does not exist')

        try:
            migrations = read_migrations(path)
            self.backend.apply_migrations(self.backend.to_apply(migrations))
        except (IOError, OSError):
            """
            If `migrations` directory is not present, then whatever is subclassing
            us will not have any DB schemas to load.
            """

    def get_connection(self):
        return self.backend.connection
