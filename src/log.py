import logging
from datetime import datetime

from src.utils import get_mongo_client


def get_log_collection():
    myclient = get_mongo_client()
    mydb = myclient["tennis"]
    return mydb["logs"]


def log(label, msg, exception_type=None):
    print("'{0}': {1}".format(label, msg))

    mycol = get_log_collection()

    log_dict = {"label": label, "message": msg, "datetime": datetime.utcnow()}
    if exception_type:
        log_dict["exception_type"] = exception_type

    mycol.insert_one(log_dict)


def delete_log_by_label(label):
    mycol = get_log_collection()

    mycol.delete_many({"label": label})


def log_to_file(msg, file_path, level=logging.DEBUG):
    # Log
    logging.basicConfig(filename=file_path, level=logging.DEBUG)
    logging.log(level, "{0}\n".format(msg))
    # Print to console
    print(msg)
