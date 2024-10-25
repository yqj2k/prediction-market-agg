from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId

def create_poly_events_bp(mongo_client):
    poly_events_bp = Blueprint('poly_events', __name__)

    @poly_events_bp.route('/', methods=['POST'])
    def create_poly_event():
        data = request.json
        event_id = mongo_client.create("poly_events", data)
        return jsonify({'message': 'Poly event created', 'id': event_id}), 201

    @poly_events_bp.route('/', methods=['GET'])
    def read_poly_events():
        events = mongo_client.read_all("poly_events")
        events = [{**event, '_id': str(event['_id'])} for event in events]
        return jsonify(events), 200

    @poly_events_bp.route('/<id>', methods=['GET'])
    def read_single_poly_event(id):
        event = mongo_client.read("poly_events", {"_id": ObjectId(id)})
        if event:
            event['_id'] = str(event['_id'])
            return jsonify(event), 200
        else:
            return jsonify({'error': 'Event not found'}), 404

    @poly_events_bp.route('/<id>', methods=['PUT'])
    def update_poly_event(id):
        data = request.json
        updated_count = mongo_client.update("poly_events", {"_id": ObjectId(id)}, data)
        if updated_count:
            return jsonify({'message': 'Poly event updated'}), 200
        else:
            return jsonify({'error': 'Event not found'}), 404

    @poly_events_bp.route('/<id>', methods=['DELETE'])
    def delete_poly_event(id):
        deleted_count = mongo_client.delete("poly_events", {"_id": ObjectId(id)})
        if deleted_count:
            return jsonify({'message': 'Poly event deleted'}), 200
        else:
            return jsonify({'error': 'Event not found'}), 404
        
    return poly_events_bp
