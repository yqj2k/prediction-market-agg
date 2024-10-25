from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId

def create_drift_events_bp(mongo_client):
    drift_events_bp = Blueprint('drift_events', __name__)

    @drift_events_bp.route('/', methods=['POST'])
    def create_drift_event():
        data = request.json
        event_id = mongo_client.create("drift_events", data)
        return jsonify({'message': 'Drift event created', 'id': event_id}), 201

    @drift_events_bp.route('/', methods=['GET'])
    def read_drift_events():
        events = mongo_client.read_all("drift_events")
        events = [{**event, '_id': str(event['_id'])} for event in events]
        return jsonify(events), 200

    @drift_events_bp.route('/<id>', methods=['GET'])
    def read_single_drift_event(id):
        event = mongo_client.read("drift_events", {"_id": ObjectId(id)})
        if event:
            event['_id'] = str(event['_id'])
            return jsonify(event), 200
        else:
            return jsonify({'error': 'Event not found'}), 404

    @drift_events_bp.route('/<id>', methods=['PUT'])
    def update_drift_event(id):
        data = request.json
        updated_count = mongo_client.update("drift_events", {"_id": ObjectId(id)}, data)
        if updated_count:
            return jsonify({'message': 'Drift event updated'}), 200
        else:
            return jsonify({'error': 'Event not found'}), 404

    @drift_events_bp.route('/<id>', methods=['DELETE'])
    def delete_drift_event(id):
        deleted_count = mongo_client.delete("drift_events", {"_id": ObjectId(id)})
        if deleted_count:
            return jsonify({'message': 'Drift event deleted'}), 200
        else:
            return jsonify({'error': 'Event not found'}), 404
        
    return drift_events_bp
