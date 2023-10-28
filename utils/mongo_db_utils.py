import os
from pymongo import MongoClient

db_user = os.environ.get('DB_USER')
db_pwd = os.environ.get('DB_PWD')
db_host = os.environ.get('DB_HOST')

def get_chunked_transcriptions_coll(db_name, coll_name):

    mongodb_uri = f"mongodb+srv://{db_user}:{db_pwd}@{db_host}/?retryWrites=true&w=majority"
    client = MongoClient(mongodb_uri)
    ct_coll = client[db_name][coll_name]

    return ct_coll