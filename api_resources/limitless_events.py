from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId

def create_limitless_events_bp(mongo_client):
    limitless_events_bp = Blueprint('limitless_events', __name__)

    @limitless_events_bp.route('/', methods=['POST'])
    def create_limitless_event():
        data = request.json
        event_id = mongo_client.create("limitless_events", data)
        return jsonify({'message': 'Limitless event created', 'id': event_id}), 201

    @limitless_events_bp.route('/', methods=['GET'])
    def read_limitless_events():
        events = mongo_client.read_all("limitless_events")
        events = [{**event, '_id': str(event['_id'])} for event in events]
        return jsonify(events), 200

    @limitless_events_bp.route('/<id>', methods=['GET'])
    def read_single_limitless_event(id):
        event = mongo_client.read("limitless_events", {"_id": ObjectId(id)})
        if event:
            event['_id'] = str(event['_id'])
            return jsonify(event), 200
        else:
            return jsonify({'error': 'Event not found'}), 404

    @limitless_events_bp.route('/<id>', methods=['PUT'])
    def update_limitless_event(id):
        data = request.json
        updated_count = mongo_client.update("limitless_events", {"_id": ObjectId(id)}, data)
        if updated_count:
            return jsonify({'message': 'Limitless event updated'}), 200
        else:
            return jsonify({'error': 'Event not found'}), 404

    @limitless_events_bp.route('/<id>', methods=['DELETE'])
    def delete_limitless_event(id):
        deleted_count = mongo_client.delete("limitless_events", {"_id": ObjectId(id)})
        if deleted_count:
            return jsonify({'message': 'Limitless event deleted'}), 200
        else:
            return jsonify({'error': 'Event not found'}), 404
        
    return limitless_events_bp
