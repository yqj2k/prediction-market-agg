from constants.drift_constants import MAX_PRICE
from websocket_processors.ws_processor import WSProcessor
import logging
import json

logging.basicConfig(level=logging.INFO)


# SubscriptionMessage defines the structure of the subscription request
class DriftSubscriptionMessage:
    def __init__(self, type, marketType, channel, market):
        self.type = type
        self.marketType = marketType
        self.channel = channel
        self.market = market

class DriftWSProcessor(WSProcessor):
    def __init__(
        self,
        subscription_message,
        collection_name,
        db_client,
        arbitrage_handler,
    ):
        self.subscription_message = subscription_message
        self.db_client = db_client
        self.collection_name = collection_name
        self.arbitrage_handler = arbitrage_handler

    def createSubcriptionMessages(self):
        return self.subscription_message

    async def processMessage(self, message):
        res = json.loads(message)
        
        if str(res.get("channel")) != "heartbeat":
            cleaned_json_string = str(res.get("data")).replace('\\"', '"')

            if cleaned_json_string != "None":
                data = json.loads(cleaned_json_string)
                marked_id = data.get("marketName")
                market = self.db_client.read(self.collection_name, {"_id": marked_id})
                if market is not None:
                    yes_price = format(int(data.get("asks")[0].get("price")) / MAX_PRICE, ".2f")
                    no_price = format(1 - (int(data.get("bids")[0].get("price")) / MAX_PRICE),".2f")
                    
                    if not (market["prices"][0] == yes_price and market["prices"][1] == no_price):
                        self.db_client.update(
                            self.collection_name, {"_id": marked_id}, {"prices": [yes_price, no_price]}
                        )
                        self.arbitrage_handler.handle("drift", [yes_price, no_price])  
