"""
Keeps track of things that can be changed.
"""

from christine import database


class Settings():
    """
    This tracks various setting vars that must be shared by all the other modules.
    On startup, loads vars from the sqlite db.
    """

    name = "Settings"

    def __init__(self):

        # initialize all the known vars to document better and avoid race conditions
        self.broca_eq_frequencies = [275, 285, 296, 318, 329, 438, 454, 488, 5734, 6382, 6614, 6855, 11300]
        self.broca_eq_width = 100
        self.broca_eq_gain = -3
        self.broca_volume = 35.0

        # Load the vars from the sqlite db
        self.load()

    def update(self, name, value):
        """Update one setting var and save to the sqlite db."""

        # Update the setting var
        setattr(self, name, value)

        # Save to the sqlite db
        database.conn.do_query(
            f"UPDATE settings SET value = '{value}' WHERE name = '{name}'"
        )
        database.conn.do_commit()

    def load(self):
        """Grabs the setting variables from db on startup."""

        rows = database.conn.do_query("SELECT name,value,type FROM settings")
        if rows is not None:

            for row in rows:

                if row[2] == "f":
                    print(f'row[0] {row[0]} row[1] {row[1]} row[2] {row[2]} ')
                    setattr(self, row[0], float(row[1]))

                elif row[2] == "b":
                    if row[1] == "True":
                        setattr(self, row[0], True)
                    else:
                        setattr(self, row[0], False)

                elif row[2] == "i":
                    setattr(self, row[0], int(row[1]))

                elif row[2] == "s":
                    setattr(self, row[0], str(row[1]))

                else:
                    setattr(self, row[0], eval(row[1])) # pylint: disable=eval-used


# Instantiate
SETTINGS = Settings()
