"""Conexión de Python con MongoDB usando PyMongo.

Instalar el driver:   pip install pymongo
"""
from pymongo import MongoClient

URI = "mongodb://localhost:27017"   # servidor local (cámbialo si usan Atlas u otro puerto)
BD = "BDAutos"


def get_db(uri, db_name):
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")    # revisa que el servidor responda; si no, marca error
    return client[db_name]


if __name__ == "__main__":
    db = get_db(URI, BD)
    print("Conectado a:", db.name)
    print("Colecciones:", db.list_collection_names())
    print("makers:", db.makers.count_documents({}), "| cars:", db.cars.count_documents({}))
    print(db.cars.find_one({}, {"_id": 0, "descr": 1, "maker.name": 1, "specs.mpg": 1}))
