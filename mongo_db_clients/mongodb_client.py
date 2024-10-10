from pymongo import MongoClient
from dotenv import dotenv_values
config = dotenv_values(".env")
from bson.objectid import ObjectId

class MongoDBClient:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def create(self, collection_name, document):
        collection = self.db[collection_name]
        result = collection.insert_one(document)
        return str(result.inserted_id)

    def read(self, collection_name, query):
        collection = self.db[collection_name]
        document = collection.find_one(query)
        return document

    def read_all(self, collection_name):
        collection = self.db[collection_name]
        documents = collection.find()
        return list(documents)
    
    def read_all_with_query(self, collection_name, query):
        collection = self.db[collection_name]
        documents = collection.find(query)
        return list(documents)

    def update(self, collection_name, query, new_values):
        collection = self.db[collection_name]
        result = collection.update_one(query, {"$set": new_values})
        return result.modified_count

    def delete(self, collection_name, query):
        collection = self.db[collection_name]
        result = collection.delete_one(query)
        return result.deleted_count

    def close(self):
        self.client.close()

# Example usage
if __name__ == "__main__":
    # Connect to the MongoDB server
    mongo_client = MongoDBClient(config["ATLAS_URI"], config["DB_NAME"])

    # Create a new document
    doc_id = mongo_client.create("test_collection", {"name": "Alice", "age": 30})
    print(f"Document inserted with ID: {doc_id}")

    # Read a document
    document = mongo_client.read("test_collection", {"_id": ObjectId(doc_id)})
    print(f"Document read: {document}")

    # Update the document
    updated_count = mongo_client.update("test_collection", {"_id": ObjectId(doc_id)}, {"age": 31})
    print(f"Documents updated: {updated_count}")

    # Read all documents
    all_documents = mongo_client.read_all("test_collection")
    print(f"All documents: {all_documents}")

    # Delete the document
    deleted_count = mongo_client.delete("test_collection", {"_id": ObjectId(doc_id)})
    print(f"Documents deleted: {deleted_count}")

    # Close the connection
    mongo_client.close()
