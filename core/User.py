import re
from core.Logger import Logger
from init import log


class User:
    register_cls = None
    cursor = None
    connect = None

    def __init__(self, chat_id, username='', city_id=2, state_number='', blocked=False, permission_level=1):
        self.chat_id = str(chat_id)
        self.username = username
        self.blocked = bool(blocked)
        self.permission_level = int(permission_level)
        self.state_number = str(state_number)
        self.city = self.register_cls.get_city(int(city_id))
        if not self.city:
            raise Exception('Something wrong with getting city with id ' + str(city_id))

    def getchatid(self):
        return self.chat_id

    def isblocked(self):
        return self.blocked

    def getcity(self):
        return self.city

    def change_city(self, new_city_id):
        new_city = self.register_cls.get_city(new_city_id)
        if new_city:
            sql = "update users set city_id=? where chat_id=?"
            val = (new_city.id, self.chat_id)
            self.cursor.execute(sql, val)
            self.connect.commit()
            self.city = new_city
            return True
        else:
            log('Can`t find city by id ' + str(new_city_id))
            return False

    def getstatenumber(self):
        return self.state_number

    def change_permission(self, permission_level: int):
        if 0 < permission_level < 5 and permission_level != self.permission_level:
            sql = "update users set permission_id=? where chat_id=?"
            val = (permission_level, self.chat_id)
            self.cursor.execute(sql, val)
            self.connect.commit()
            self.permission_level = permission_level
            return True
        else:
            log('Wrong permission level')
            return False

    def change_state_number(self, new_state_number):
        state_number = self.validate_state_number(new_state_number)
        if state_number:
            sql = "update users set state_number=? where chat_id=?"
            val = (state_number, self.chat_id)
            self.cursor.execute(sql, val)
            self.connect.commit()
            self.state_number = new_state_number
            return True
        else:
            log(new_state_number + ' not valid')
            return False

    def change_block(self, blocked: bool):
        sql = "update users set blocked=? where chat_id=?"
        val = (int(blocked), self.chat_id)
        self.cursor.execute(sql, val)
        self.connect.commit()
        self.blocked = blocked
        return True

    def user_exists(self):
        sql = "select * from users where chat_id=?"
        val = (self.chat_id,)
        self.cursor.execute(sql, val)
        return bool(self.cursor.fetchone())

    def adduser(self):
        if not self.user_exists():
            if self.state_number:
                sql = "insert into users (chat_id, username, city_id, permission_id, blocked, state_number) values (?, ?, ?, ?, ?, ?)"
                val = (
                    self.chat_id, self.username, self.city.id, self.permission_level, int(self.blocked),
                    self.state_number)
            else:
                sql = "insert into users (chat_id, username, city_id, permission_id, blocked) values (?, ?, ?, ?, ?)"
                val = (self.chat_id, self.username, self.city.id, self.permission_level, int(self.blocked))
            self.cursor.execute(sql, val)
            self.connect.commit()
            return True
        else:
            log('User with chat_id ' + self.chat_id + ' already exists')
            return False

    def isdriver(self):
        if self.permission_level == 1:
            return True
        else:
            return False

    def isregionuser(self):
        if self.permission_level == 2:
            return True
        else:
            return False

    def isadmin(self):
        if self.permission_level >= 3:
            return True
        else:
            return False

    def issuperadmin(self):
        if self.permission_level == 4:
            return True
        else:
            return False

    def get_blocked_users(self):
        """
        1 - chat_id
        2 - username without '@'
        3 - state_number
        """

        sql = "select chat_id, username, state_number from users where city_id=? and blocked=1"
        val = (self.city.id,)
        self.cursor.execute(sql, val)
        response = self.cursor.fetchall()
        return response

    def select_regional_users(self):
        """
        0 - id
        1 - chat_id
        2 - username without '@'
        3 - city_id
        4 - permission_id
        5 - blocked(bool)
        6 - state_number

        :param permission:
        :return:  list
        """

        sql = "select * from users where city_id=? and permission_id=2"
        val = (self.city.id,)
        self.cursor.execute(sql, val)
        result = self.cursor.fetchall()
        if result:
            return result
        else:
            return None

    @classmethod
    def select_all_users(cls, permission=0):
        """
        0 - id
        1 - chat_id
        2 - username without '@'
        3 - city_id
        4 - permission_id
        5 - blocked(bool)
        6 - state_number

        :param permission:
        :return:  list
        """
        if permission == 0:
            sql = "select * from users"
            cls.cursor.execute(sql)
            result = cls.cursor.fetchall()
        else:
            sql = "select * from users where permission_id=?"
            val = (permission,)
            cls.cursor.execute(sql, val)
            result = cls.cursor.fetchall()

        return result

    @classmethod
    def select_user_by_chatid(cls, chat_id):
        """
        0 - id
        1 - chat_id
        2 - username without '@'
        3 - city_id
        4 - permission_id
        5 - blocked(bool)
        6 - state_number

        :param cursor:
        :return: User
        """
        sql = "select * from users where chat_id=?"
        val = (chat_id,)
        cls.cursor.execute(sql, val)
        result = cls.cursor.fetchone()
        if result:
            username = result[2]
            state_number = result[6]
            city_id = result[3]
            blocked = result[5]
            permission_level = result[4]
            return User(chat_id, username, city_id, state_number, blocked, permission_level)
        else:
            return None

    @staticmethod
    def validate_state_number(state_number: str):
        regexp = r'(^[A-Z|А-Я][A-Z|А-Я]\d\d\d\d[A-Z|А-Я][A-Z|А-Я]$)|(^[A-ZА-Я]+$)'
        state_number = state_number.replace(' ', '').upper()
        try:
            result = re.findall(regexp, state_number)[0][0]
            return result
        except IndexError:
            return False

    @staticmethod
    def validate_driver(chat_id):
        chat_id = str(chat_id)
        user = User.register_cls.get_user(chat_id)
        if user:
            if user.isdriver():
                if not user.isblocked():
                    return True
        return False
