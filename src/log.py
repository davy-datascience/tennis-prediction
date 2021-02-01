from datetime import datetime

from src.utils import get_mongo_client


def log(label, msg, exception_type=None):
    print("'{0}': {1}".format(label, msg))
    myclient = get_mongo_client()
    mydb = myclient["tennis"]
    mycol = mydb["logs"]

    log_dict = {"label": label, "message": msg, "datetime": datetime.utcnow()}
    if exception_type:
        log_dict["exception_type"] = exception_type

    mycol.insert_one(log_dict)
