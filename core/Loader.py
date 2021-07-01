from core.Register import Registry
from core.User import User
from core.City import City
from core.Db import Db

User.register_cls = Registry


class Loader:

    db = None

    def __init__(self):
        # Экземпляр БД
        self.db = Db()
        City.cursor = self.db.cursor
        City.connect = self.db.conn
        User.cursor = self.db.cursor
        User.connect = self.db.conn

        # Загрузка городов
        cities_from_db = City.select_all_cities()
        for city in cities_from_db:
            try:
                Registry.load_city(city[0], City(city[1], city[2], city[3], db_id=city[0]))
            except AssertionError:
                print('City id ' + city[3] + ' does not exist on gdrive. (City name: ' + city[1] + ')')

        # Загрузка пользователей
        users_from_db = User.select_all_users()
        for user in users_from_db:
            Registry.load_user(User(user[1], user[2], user[3], permission_level=user[4], blocked=user[5], state_number=user[6]))

    @staticmethod
    def get_blocked_users(chat_id, city_id):
        src_user = Registry.get_user(chat_id)
        if not src_user.isdriver():
            users = []
            for user in Registry.users:
                if user.city.id == int(city_id) and user.isblocked():
                    users.append(user)
            return users
        else:
            print('Operation not allowed')
            return False

    @staticmethod
    def delete_city(city_id):
        city = Registry.get_city(city_id)
        Registry.unload_city(city_id)
        if city.delete_city():
            del city
            return True
        else:
            return False

    @staticmethod
    def add_city(name, ukr_name, dir_id):
        try:
            city = City(name, ukr_name, dir_id)
        except AssertionError:
            print('City id ' + dir_id + ' does not exist on gdrive. (City name: ' + name + ')')
            return False

        if city.addcity():
            del city
            city = City.selectcitybyid(dir_id)
            Registry.load_city(city.id, city)
            return city
        else:
            return False

    @staticmethod
    def add_user(chat_id, username, city_id=2, permission_level=1, blocked=False, state_number=''):
        user = User(chat_id, username, city_id, permission_level=permission_level, blocked=blocked, state_number=state_number)

        if user.adduser():
            Registry.load_user(user)
            return user
        else:
            return False
