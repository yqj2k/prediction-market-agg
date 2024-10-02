from mongo_db_clients.mongodb_client import MongoDBClient

class MongoDBKVStore:
    def __init__(self, uri, db_name, collection_name="kv_store"):
        self.client = MongoDBClient(uri, db_name)
        self.collection_name = collection_name

    def set(self, key, value):
        # Create or update the key-value pair where "key" is the document's "_id"
        query = {"_id": key}
        document = {"_id": key, "value": value}
        existing_doc = self.client.read(self.collection_name, query)
        
        if existing_doc:
            return self.client.update(self.collection_name, query, {"value": value})
        else:
            return self.client.create(self.collection_name, document)

    def get(self, key):
        query = {"_id": key}
        document = self.client.read(self.collection_name, query)
        return document.get("value") if document else None

    def delete(self, key):
        query = {"_id": key}
        return self.client.delete(self.collection_name, query)

    def get_all(self):
        documents = self.client.read_all(self.collection_name)
        return {doc['key']: doc['value'] for doc in documents}

    def close(self):
        self.client.close()
