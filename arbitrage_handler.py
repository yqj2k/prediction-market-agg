import logging

logging.basicConfig(level=logging.INFO)


class ArbitrageHandler:
    def __init__(self, db_client):
        self.db_client = db_client

    def handle(self, source, price_change_event):
        
        if source == "polymarket":
            mapping_to_drift = self.db_client.read("poly-drift-map", {"_id": price_change_event["_id"]})
            if mapping_to_drift is not None:
                drift_market = self.db_client.read("drift_events", {"_id": mapping_to_drift["drift_id"]})
                logging.info("Poly Event - %s, Drift Event - %s, Poly Yes - %s, Drift No - %s, Arb: %s", price_change_event["question"], drift_market["name"], price_change_event["prices"][0], drift_market["prices"][1], float(price_change_event["prices"][0]) + float(drift_market["prices"][1]))
                logging.info("Poly Event - %s, Drift Event - %s, Poly No - %s, Drift Yes - %s, Arb: %s", price_change_event["question"], drift_market["name"], price_change_event["prices"][1], drift_market["prices"][0], float(price_change_event["prices"][1]) + float(drift_market["prices"][0]))
  
            
        
