from websocket_processors.ws_processor import WSProcessor
import json

class PriceChangeEvent:
    def __init__(self, event_type, market, timestamp, address, outcome, contracts, amount, amountUSD, symbol, strategy):
        self.event_type = event_type
        self.market = market
        self.timestamp = timestamp
        self.address = address
        self.outcome = outcome
        self.contracts = contracts
        self.amount = amount
        self.amountUSD = amountUSD
        self.symbol = symbol
        self.strategy = strategy

def handle_price_change(event):
    # logging.info(event)
    price_change_event = PriceChangeEvent(
        event["eventType"],
        event["title"],
        event["data"]["timestamp"],
        event["data"]["address"],
        event["data"]["outcome"],
        event["data"]["contracts"],
        event["data"]["tradeAmount"],
        event["data"]["tradeAmountUSD"],
        event["data"]["symbol"],
        event["data"]["strategy"]
    )
    # logging.info("Price change detected: assetID: %s, New Price: %s, Time: %s",
    #              price_change_event.asset_id, price_change_event.price, price_change_event.timestamp)
    return price_change_event

class LimitlessWSProcessor(WSProcessor):
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

        if event_type == "NEW_TRADE":
            price_change_event = handle_price_change(event)
            address = price_change_event.address

            # market_id = self.kv_client.get(address)
            market = self.db_client.read(self.collection_name, {"_address": address})
            
            if not (address is None and market is None):
                index = 0 if market["outcome"] == "YES" else 1

                if not market["prices"][index] == price_change_event.price:
                    market["prices"][index] = price_change_event.price
                    new_prices = market["prices"]
                    self.db_client.update(
                        self.collection_name, {"_address": address}, {"prices": new_prices}
                    )
                    self.arbitrage_handler.handle("limitless", market)
                    # logging.info("Price change detected: assetID: %s, New Price: %s, Time: %s", price_change_event.asset_id, price_change_event.price, price_change_event.timestamp)
