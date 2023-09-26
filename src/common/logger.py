import datetime
import logging
import os
import sys

DEFAULT_LOG_PATH = os.getcwd() + '/log'


def get_log_path():
    log_path = DEFAULT_LOG_PATH
    if not os.path.isdir(log_path):
        if os.access(log_path, os.W_OK):
            os.makedirs(log_path)
        else:
            log_path = os.getcwd()
        print('##### log path is %s #####' % log_path)
    return log_path + '/'


def get_logger(mod_name):
    logger = logging.getLogger(mod_name)

    # Add exception code if logger handler already exists
    if len(logger.handlers) > 0:
        return logger

    logger.setLevel(logging.INFO)

    # create a file handler
    now = datetime.datetime.now()
    # To print now without microsecond, space and semicolon
    now_str = str(now.replace(microsecond=0)).replace(" ", "-").replace(":", "-")

    file_handler = logging.FileHandler(get_log_path() + 'adart-' + now_str + '.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s')
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
