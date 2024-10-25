from flask import Blueprint, jsonify
from constants.global_constants import PLATFORMS  # Import the MongoDB client instance

def create_matched_events_bp(mongo_client):
    matched_events_bp = Blueprint("matched-events", __name__)

    @matched_events_bp.route("/", methods=["GET"])
    def read_matched_events():
        processed_mappings = set()
        
        for idx_outer, platform_outer in enumerate(PLATFORMS):
            for idx_inner, platform_inner in enumerate(PLATFORMS):
                if idx_outer == idx_inner:
                    continue
                
                platforms = [platform_outer, platform_inner]
                platforms.sort()
                
                processed_mappings.add((platforms[0], platforms[1]))
        
        all_event_pairs = []
                
        for mapping_name in processed_mappings:
            mappings = mongo_client.read_all(f"{mapping_name[0]}_{mapping_name[1]}_map")
            
            for mapping in mappings:
                first_id = mapping[f"{mapping_name[0]}_id"]
                second_id = mapping[f"{mapping_name[1]}_id"]
                first_event = mongo_client.read(f"{mapping_name[0]}_events", {"_id": first_id})
                second_event = mongo_client.read(f"{mapping_name[1]}_events", {"_id": second_id})
                
                all_event_pairs.append([first_event, second_event])
                
        return jsonify(all_event_pairs), 200
    
    return matched_events_bp
