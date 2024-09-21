from websocket_processors.ws_processor import WSProcessor
import logging
import json

logging.basicConfig(level=logging.INFO)

# SubscriptionMessage defines the structure of the subscription request
class PolySubscriptionMessage:
    def __init__(self, auth, markets, assets_ids, message_type):
        self.auth = auth
        self.markets = markets
        self.assets_ids = assets_ids
        self.type = message_type

# PriceChangeEvent defines the structure for a price change event message
class PriceChangeEvent:
    def __init__(self, event_type, asset_id, market, price, size, side, timestamp):
        self.event_type = event_type
        self.asset_id = asset_id
        self.market = market
        self.price = price
        self.size = size
        self.side = side
        self.timestamp = timestamp

def handle_price_change(event):
    logging.info(event)
    price_change_event = PriceChangeEvent(
        event['event_type'],
        event['asset_id'],
        event['market'],
        event['price'],
        event['size'],
        event['side'],
        event['timestamp']
    )
    logging.info("Price change detected: assetID: %s, New Price: %s, Time: %s",
                 price_change_event.asset_id, price_change_event.price, price_change_event.timestamp)

class PolyWSProcessor(WSProcessor):
    def __init__(self, subscriptionMessage):
        self.subscriptionMessage = subscriptionMessage

    def createSubcriptionMessage(self):
        return self.subscriptionMessage
    
    async def processMessage(self, message):
        event = json.loads(message)
        event_type = event.get("event_type")
        
        if event_type == "price_change":
            handle_price_change(event)
        else:
            logging.warning(f"Unhandled event type: {event_type}")