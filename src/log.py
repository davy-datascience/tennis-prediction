from datetime import datetime
from dateutil.tz import UTC

from src.utils import get_mongo_client


def log(label, msg):
    print("'{0}': {1}".format(label, msg))
    myclient = get_mongo_client()
    mydb = myclient["tennis"]
    mycol = mydb["logs"]
    mycol.insert_one({"label": label, "message": msg, "datetime": datetime.now(tz=UTC)})
