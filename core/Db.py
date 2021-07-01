import sqlite3
from init import database_file as path_db


class Db:

    conn = None
    cursor = None

    def __init__(self):
        self.conn = sqlite3.connect(path_db)
        self.cursor = self.conn.cursor()

    def get_cursor(self):
        return self.cursor

    def del_cursor(self):
        self.cursor = None

    def __del__(self):
        self.del_cursor()
        self.conn.close()
