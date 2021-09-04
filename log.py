import configparser
import logging

from datetime import datetime
from utils import get_mongo_client


config = configparser.ConfigParser()
config.read("config.ini")


def get_log_collection():
    myclient = get_mongo_client()
    mydb = myclient["tennis"]
    return mydb["logs"]


def log(label, msg, exception_type=None):
    mycol = get_log_collection()

    log_dict = {"label": label, "message": msg, "datetime": datetime.utcnow()}
    if exception_type:
        log_dict["exception_type"] = exception_type

    mycol.insert_one(log_dict)


def delete_log_by_label(label):
    mycol = get_log_collection()

    mycol.delete_many({"label": label})


def log_to_file(msg, file_path, level=logging.INFO):
    # Log
    logging.basicConfig(filename=file_path, level=logging.INFO,
                        format='%(asctime)s  %(name)s:%(levelname)s: %(message)s')
    logging.log(level, "{0}".format(msg))
    # Print to console
    print(msg)


def get_file_log(name):
    return '{0}logs/{1}'.format(config['project']['folder'], config['logs'][name])
