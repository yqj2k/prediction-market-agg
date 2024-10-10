import logging

from constants.global_constants import PLATFORMS

logging.basicConfig(level=logging.INFO)

class ArbitrageHandler:
    def __init__(self, db_client):
        self.db_client = db_client
            
        # generate platforms to platform mappings map
        self.platform_mappings = dict.fromkeys(PLATFORMS, set())
        
        for idx_outer, platform_outer in enumerate(PLATFORMS):
            for idx_inner, platform_inner in enumerate(PLATFORMS):
                platforms = [platform_outer, platform_inner]
                platforms.sort()
                mapping_tuple = (platforms[0], platforms[1])

                if idx_outer == idx_inner:
                    continue
                
                self.platform_mappings[platform_outer].add(mapping_tuple)
                self.platform_mappings[platform_inner].add(mapping_tuple)

    def handle(self, source, price_change_event):
        
        mappings_tuples = self.platform_mappings[source]
        
        for mapping_tuple in mappings_tuples:
            mapping = self.db_client.read(f"{mapping_tuple[0]}_{mapping_tuple[1]}_map", {f"{source}_id": price_change_event["_id"]})
            if mapping is not None:
                other_market_platform = mapping_tuple[0] if mapping_tuple[1] == source else mapping_tuple[1]
                source_market = self.db_client.read(f"{source}_events", {"_id": mapping[f"{source}_id"]})
                other_market = self.db_client.read(f"{other_market_platform}_events", {"_id": mapping[f"{other_market_platform}_id"]})
                
                if (source_market["prices"] is None or other_market["prices"] is None):
                    continue
                
                logging.info(f"{source} Event - {source_market["question"]}, {other_market_platform} Event - {other_market["question"]}, {source} Yes - {price_change_event["prices"][0]}, {other_market_platform} No - {other_market["prices"][1]}, Arb: {float(price_change_event["prices"][0]) + float(other_market["prices"][1])}")
                logging.info(f"{source} Event - {source_market["question"]}, {other_market_platform} Event - {other_market["question"]}, {source} No - {price_change_event["prices"][1]}, {other_market_platform} Yes - {other_market["prices"][0]}, Arb: {float(price_change_event["prices"][1]) + float(other_market["prices"][0])}")            
            