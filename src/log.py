import configparser
import pymongo
from datetime import datetime
from dateutil.tz import UTC

config = configparser.ConfigParser()
config.read("src/config.ini")
MONGO_CLIENT = config['mongo']['client']


def log(label, msg):
    myclient = pymongo.MongoClient(MONGO_CLIENT)
    mydb = myclient["tennis"]
    mycol = mydb["logs"]
    mycol.insert_one({"label": label, "message": msg, "datetime": datetime.now(tz=UTC)})
