from flask import Flask
from dotenv import dotenv_values
from flask_cors import CORS
from api_resources.drift_events import create_drift_events_bp
from api_resources.poly_events import create_poly_events_bp
from api_resources.limitless_events import create_limitless_events_bp
from api_resources.matched_events import create_matched_events_bp
from mongo_db_clients.mongodb_client import MongoDBClient

# Load configuration from .env
config = dotenv_values(".env")

# Initialize the MongoDB client
mongo_client = MongoDBClient(config["ATLAS_URI"], config["DB_NAME"])

app = Flask(__name__)

CORS(app)

# Register blueprints for each resource
app.register_blueprint(create_drift_events_bp(mongo_client), url_prefix='/drift_events')
app.register_blueprint(create_poly_events_bp(mongo_client), url_prefix='/poly_events')
app.register_blueprint(create_limitless_events_bp(mongo_client), url_prefix='/limitless_events')
app.register_blueprint(create_matched_events_bp(mongo_client), url_prefix='/matched-events')

if __name__ == '__main__':
    app.run(debug=True)
