"""
Handles talking to the sqlite database
"""
import os.path
import sqlite3
import argparse

from christine import log


class ChristineDB:
    """
    There is a SQLite db that contains all sounds
    And now it also contains status and probably settings later on
    The db has all of the sounds in it. There is a preprocess.py script that will take the master sounds and process them into directories to be played
    Eventually I need to give some thought to security, since you might be able to inject commands into this pretty easily

    After reading https://www.sqlite.org/atomiccommit.html I'm really not that concerned with running sync commands, etc to prevent db corruption, seems taken care of
    """

    def __init__(self):

        # Connect to the SQLite database
        self.sqlite_path = "christine.sqlite"

        # if the database file doesn't exist, start fresh
        existing_database_file = os.path.isfile(self.sqlite_path)

        # connect to db. I guess it can create it if it's not there
        self.sqlite_connection = sqlite3.connect(
            database=self.sqlite_path, check_same_thread=False
        )

        # import the initial content of db if necessary
        if existing_database_file is False:
            with open(file='christine.sql', mode='r', encoding='utf-8') as sql_file:
                sql = sql_file.read()
            sqlite_cursor = self.sqlite_connection.cursor()
            sqlite_cursor.executescript(sql)

    def do_query(self, query):
        """
        Do a database query, return raw rows
        """

        try:
            sqlite_cursor = self.sqlite_connection.cursor()
            sqlite_cursor.execute(query)

            rows = sqlite_cursor.fetchall()
            log.db.debug("%s (%s)", query, len(rows))
            if len(rows) == 0:
                return None
            else:
                return rows

        # log exception in the db.log
        except Exception as ex:
            log.db.error("Database error. %s %s %s  Query: %s", ex.__class__, ex, log.format_tb(ex.__traceback__), query)
            return None

    def field_names_for_table(self, table):
        """
        Return a dict of sound table field names to ids for later use for selecting fields by name
        Best solution I could find. Otherwise if I make any changes to field names it won't propagate into the objects
        """

        try:
            query = f"select * from {table}"

            sqlite_cursor = self.sqlite_connection.cursor()
            sqlite_cursor.execute(query)
            sqlite_field_names = {}
            index = 0
            for field_name in sqlite_cursor.description:
                sqlite_field_names[field_name[0]] = index
                index += 1
            del sqlite_cursor
            return sqlite_field_names

        # log exception in the db.log
        except Exception as ex:
            log.db.error("Database error. %s %s %s  Query: %s", ex.__class__, ex, log.format_tb(ex.__traceback__), query)
            return None

    def do_commit(self):
        """
        Do a database commit.
        """

        try:
            self.sqlite_connection.commit()

        # log exception in the db.log
        except Exception as ex:
            log.db.error("Database error (commit). %s %s %s", ex.__class__, ex, log.format_tb(ex.__traceback__))

    def disconnect(self):
        """Called when script is supposed to be shutting down."""

        try:
            self.sqlite_connection.commit()
            self.sqlite_connection.close()

        # log exception in the db.log
        except Exception as ex:
            log.db.error("Database error (close). %s %s %s", ex.__class__, ex, log.format_tb(ex.__traceback__))


# Instantiate
database = ChristineDB()

# This provides a way to run sql from cli
# This was super helpful: https://docs.python.org/3/howto/argparse.html#id1
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="The database query to run.")
    args = parser.parse_args()

    print(args.query)
    print(database.do_query(args.query))
    database.do_commit()
