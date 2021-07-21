import logging
from logging.handlers import RotatingFileHandler


class Logger:
    logger = None

    @staticmethod
    def get_instance(log_file):
        if Logger.logger is None:
            Logger.f_handler = logging.FileHandler(log_file)
            Logger.f_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
            Logger.f_handler.setLevel(logging.WARNING)
            Logger.r_handler = RotatingFileHandler(log_file, maxBytes=5000000, backupCount=5)
            Logger.logger = logging.getLogger('autobot')
            Logger.logger.setLevel(logging.INFO)
            Logger.logger.addHandler(Logger.r_handler)
            Logger.logger.addHandler(Logger.f_handler)

        return Logger.logger
