"""
Tools for interacting with MySQL databases.
"""

import logging
import MySQLdb
import MySQLdb.cursors
import _mysql_exceptions


class Connection(object):
    """
    A MySQL database connection class. Useful for interacting with a
    MySQL database. Provides no hand-holding (assumes you know SQL).
    """

    def __init__(self, config):
        """
        Save the config and initialize a few member variables.
        """
        self.config = config
        self.last_query = None
        self.connection = None

    def prepare(self, query, args):
        """
        Escape arguments, replace them in the query string. Also
        pre-process arguments to properly handle None/True/False values.
        This function sets the last_query property on the object,
        which is useful when debugging.
        """
        self.connect()
        bind_args = []

        for arg in args:
            if arg is None:
                bind_args.append('NULL')
            elif arg is False:
                bind_args.append('0')
            elif arg is True:
                bind_args.append('1')
            else:
                bind_args.append(self.connection.escape(
                    arg, self.connection.encoders))

        self.last_query = query % tuple(bind_args)
        logging.getLogger('moar').debug(self.last_query)

        return self.last_query

    def connect(self):
        """
        Connect to MySQL only if a connection does not already exist.
        """
        if not self.connection:
            self.connection = MySQLdb.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['username'],
                passwd=self.config['password'],
                db=self.config['schema'],
                cursorclass=MySQLdb.cursors.SSDictCursor)
        return self.connection

    def query(self, query, *args):
        """
        Run a query with the given arguments. Uses a generator to stream
        results back (keeps memory usage low).
        """
        run_query = self.prepare(query, args)
        cursor = self.connection.cursor()
        cursor.execute(run_query)
        row = cursor.fetchone()
        while row:
            yield row
            row = cursor.fetchone()
        cursor.close()

    def execute(self, query, *args):
        """
        Execute a query. Do the right thing--if there is a resultset,
        return it.  If there is something else (like number of rows
        changed), return that instead.
        """
        run_query = self.prepare(query, args)
        try:
            cursor = self.connection.cursor()
            cursor.execute(run_query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except _mysql_exceptions.OperationalError, ex:
            code, _message = ex
            if code == 2006:
                logging.getLogger('moar').info(
                    'Connection lost, reconnecting...')
                cursor.close()
                self.close()
                self.connect()
                return self.execute(query, *args)

    def close(self):
        """
        Close the connection. Can be re-opened later.
        """
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def __del__(self):
        """
        Close the connection.
        """
        self.close()
