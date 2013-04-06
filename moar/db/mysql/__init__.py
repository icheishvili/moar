"""
MySQL connection object for Python that makes it easy to write fault-tolerant
data access and introspect queries.
"""

import _mysql_exceptions
import MySQLdb
import MySQLdb.cursors

class Connection(object):
    """
    Simple MySQL connection object that does everything needed without
    introducing extra bloat.
    """

    def __init__(self, config):
        """
        Save the config and connect.
        """
        self.config = config
        self.mysql = None
        self.last_query = None
        self.connect()

    def prepare(self, query, args):
        """
        Prepare the query for execution query by converting booleans to
        integers, Nones to NULLs, and escaping all parameters.
        """
        bind_args = []
        for arg in args:
            if arg is None:
                bind_args.append('NULL')
            elif arg is False:
                bind_args.append('0')
            elif arg is True:
                bind_args.append('1')
            else:
                bind_args.append(self.mysql.escape(arg, self.mysql.encoders))
        run_query = query % tuple(bind_args)
        self.last_query = run_query
        return run_query

    def connect(self):
        """
        Connect to the MySQL database.
        """
        self.mysql = MySQLdb.connect(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['username'],
            passwd=self.config['password'],
            db=self.config['database'],
            cursorclass=MySQLdb.cursors.SSDictCursor,
            use_unicode=True,
            charset='utf8')
        self.execute('''
            SET NAMES utf8mb4;
            SET CHARACTER SET utf8mb4;
        ''')

    def query(self, query, *args, **kwargs):
        """
        Query MySQL, stream rows back one by one. Handles re-connects.
        """
        run_query = self.prepare(query, args)
        retries = kwargs.get('retries', 1)

        try:
            cursor = self.mysql.cursor()
            cursor.execute(run_query)
            row = cursor.fetchone()
            while row:
                yield row
                row = cursor.fetchone()
            cursor.close()
        except _mysql_exceptions.OperationalError, ex:
            code, _message = ex
            if code in (2006, 2013) and retries:
                self.close()
                self.connect()
                for row in self.query(query, *args, retries=retries - 1):
                    yield row
            else:
                raise

    def execute(self, query, *args):
        """
        Buffered version of query().
        """
        return list(self.query(query, *args))

    def close(self):
        """
        Close the MySQL connection.
        """
        if self.mysql is not None:
            self.mysql.close()
            self.mysql = None

    def __del__(self):
        """
        Alias for close().
        """
        self.close()
