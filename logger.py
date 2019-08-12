import logging
import sys


class Logging:
    logging = None

    def __init__(self):
        self.loggers = {}

    @staticmethod
    def get_logging():
        if not Logging.logging:
            Logging.logging = Logging()
            return Logging.logging

    def create_logger(self, name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        self.loggers[name] = logger
        return logger


    def get_logger(self, name):
        return self.loggers[name]
