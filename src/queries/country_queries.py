from src.utils import get_mongo_client


def get_country_collection():
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    return database["countries"]


def country_exists(country):
    collection = get_country_collection()

    result = collection.find_one({"country": country})

    return result is not None


def find_country_with_flag_code(flag_code):
    collection = get_country_collection()

    result = collection.find_one({"flag_code": flag_code})

    return None if result is None else result["country"]
