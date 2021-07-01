from core.City import City
from core.User import User


class Registry:
    users = {}
    cities = {}

    @classmethod
    def get_user(cls, chat_id):
        try:
            return cls.users[str(chat_id)]
        except KeyError:
            print('No load user with chat id ' + str(chat_id))
            return None

    @classmethod
    def get_city(cls, city_id):
        try:
            return cls.cities[int(city_id)]
        except KeyError:
            print('No load city with id ' + str(city_id))
            return None

    @classmethod
    def load_user(cls, user: User):
        if user.chat_id not in cls.users:
            cls.users[user.chat_id] = user
            return True
        else:
            print('User already exists')
            return False

    @classmethod
    def load_city(cls, city_id, city: City):
        city_id = int(city_id)
        if city_id not in cls.cities:
            cls.cities[city_id] = city
            return True
        else:
            print('City already exists')
            return False

    @classmethod
    def unload_user(cls, chat_id):
        try:
            del cls.users[str(chat_id)]
        except KeyError:
            print('No load user with chat id ' + str(chat_id))
            return False
        else:
            return True

    @classmethod
    def unload_city(cls, city_id):
        try:
            del cls.cities[int(city_id)]
        except KeyError:
            print('No load city with id ' + str(city_id))
            return False
        else:
            return True
