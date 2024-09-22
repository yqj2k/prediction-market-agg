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
    # logging.info(event)
    price_change_event = PriceChangeEvent(
        event["event_type"],
        event["asset_id"],
        event["market"],
        event["price"],
        event["size"],
        event["side"],
        event["timestamp"],
    )
    # logging.info("Price change detected: assetID: %s, New Price: %s, Time: %s",
    #              price_change_event.asset_id, price_change_event.price, price_change_event.timestamp)
    return price_change_event


class PolyWSProcessor(WSProcessor):
    def __init__(
        self,
        subscription_message,
        collection_name,
        db_client,
        kv_client,
        arbitrage_handler,
    ):
        self.subscription_message = subscription_message
        self.db_client = db_client
        self.kv_client = kv_client
        self.collection_name = collection_name
        self.arbitrage_handler = arbitrage_handler

    def createSubcriptionMessages(self):
        return self.subscription_message

    async def processMessage(self, message):
        event = json.loads(message)
        event_type = event.get("event_type")

        if event_type == "price_change":
            price_change_event = handle_price_change(event)
            asset_id = price_change_event.asset_id

            market_id = self.kv_client.get(asset_id)
            market = self.db_client.read(self.collection_name, {"_id": market_id})
            if not (market_id is None and market is None):
                index = 0 if market["tokenIds"][0] == asset_id else 1

                if not market["prices"][index] == price_change_event.price:
                    market["prices"][index] = price_change_event.price
                    new_prices = market["prices"]
                    self.db_client.update(
                        self.collection_name, {"_id": market_id}, {"prices": new_prices}
                    )
                    self.arbitrage_handler.handle("polymarket", market)
                    # logging.info("Price change detected: assetID: %s, New Price: %s, Time: %s", price_change_event.asset_id, price_change_event.price, price_change_event.timestamp)
