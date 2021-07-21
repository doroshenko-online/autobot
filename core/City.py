from misc import *
from core.Logger import Logger
from init import log


class City:

    cursor = None
    connect = None

    def __init__(self, name, ukr_name, dir_id, db_id=0):
        self.validate_dirid(dir_id)
        self.id = int(db_id)
        self.name = name
        self.ukr_name = ukr_name
        self.dir_id = str(dir_id)

    def getname(self):
        return self.name

    def getukrname(self):
        return self.ukr_name

    def getdirid(self):
        return self.dir_id

    def delete_city(self):
        if self.city_exists():
            sql = "delete from cities where directory_id=?"
            val = self.dir_id
            self.cursor.execute(sql, val)
            self.connect.commit()
            return True
        else:
            log('City with directory_id ' + self.dir_id + 'does not exist')
            return False

    def city_exists(self):
        sql = "select * from cities where directory_id=?"
        val = (self.dir_id,)
        self.cursor.execute(sql, val)
        return bool(self.cursor.fetchone())

    def addcity(self):
        if not self.city_exists():
            sql = "insert into cities (name, ukr_name, directory_id) values (?, ?, ?)"
            val = (self.name, self.ukr_name, self.dir_id,)
            self.cursor.execute(sql, val)
            self.connect.commit()
            return True
        else:
            log("city with directory_id " + self.dir_id + " already exists")
            return False

    def change_name(self, name):
        if self.city_exists():
            sql = "update cities set name=? where directory_id=?"
            val = (name, self.dir_id,)
            try:
                self.cursor.execute(sql, val)
            except Exception as e:
                log('Can`t update name on city ' + self.name)
                return False
            self.connect.commit()
            self.name = name
            return True

    def change_ukrname(self, ukr_name):
        if self.city_exists():
            sql = "update cities set ukr_name=? where directory_id=?"
            val = (ukr_name, self.dir_id,)
            try:
                self.cursor.execute(sql, val)
            except Exception as e:
                log('Can`t update ukr_name on city ' + self.name)
                return False
            self.connect.commit()
            self.ukr_name = ukr_name
            return True

    def change_dir_id(self, dir_id):
        try:
            self.validate_dirid(dir_id)
        except AssertionError as e:
            log(e)
            return False
        sql = "update cities set directory_id=? where directory_id=?"
        val = (dir_id, self.dir_id,)
        self.cursor.execute(sql, val)
        self.connect.commit()
        self.dir_id = dir_id
        return True

    @staticmethod
    def validate_dirid(dir_id):
        assert find_file_by_id(dir_id), 'Directory id does not exist'

    @classmethod
    def selectcitybyid(cls, dir_id):
        """
        0 - id
        1 - name
        2 - ukr_name
        3 - dir_id
        :param dir_id:
        :return: City
        """
        try:
            cls.validate_dirid(dir_id)
        except AssertionError as e:
            log(str(e) + ": " + dir_id)
            return None
        sql = "select * from cities where directory_id=?"
        val = (dir_id,)
        try:
            cls.cursor.execute(sql, val)
        except Exception:
            log('Something wrong with getting city from database')
            return None

        result = cls.cursor.fetchone()
        if result:
            name = result[1]
            ukr_name = result[2]
            return City(name, ukr_name, result[3], db_id=result[0])
        else:
            return None

    @classmethod
    def select_all_cities(cls):
        """
        0 - id
        1 - name
        2 - ukr_name
        3 - dir_id
        :return: list
        """
        sql = "select * from cities"
        cls.cursor.execute(sql)
        result = cls.cursor.fetchall()
        return result
