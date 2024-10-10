import requests
from datetime import datetime
from constants.drift_constants import HARDCODED_MARKETS_MAP, HARDCODED_MARKETS_NAMES, MAX_PRICE
from constants.global_constants import PLATFORMS
import websocket_handler
from websocket_processors.drift_ws_processor import DriftSubscriptionMessage, DriftWSProcessor

GET = "GET"
POST = "POST"
DELETE = "DELETE"
PUT = "PUT"

HOST = "https://dlob.drift.trade/l2?marketName="
WS_HOST = "wss://dlob.drift.trade/ws"
COLLECTION_NAME = "drift_events"

# drift events
# YES price = first ask price /  1000000
# NO price = 1 - (first bid price /  1000000)
class Market:
    def __init__(self, _id, question, prices):
        self._id = _id
        self.question = question
        self.prices = prices
        self.platform = "drift"
        self.end_date = datetime.strptime("2024-10-05T12:00:00Z", "%Y-%m-%dT%H:%M:%SZ")

def init_drift(mongodb_client):
    new_market_list = []
    for market_name in HARDCODED_MARKETS_NAMES:
        resp = requests.request(GET, HOST + market_name)
        if resp.status_code != 200:
            print("Request to dlob drift API erroring out, stopping execution")
            return

        data = resp.json()

        query = {"_id": market_name}
        existing_market = mongodb_client.read(COLLECTION_NAME, query)
        if existing_market is None and len(data["asks"]) > 0 and len(data["bids"]) > 0 :
            yes_price = int(data["asks"][0]["price"]) / MAX_PRICE
            no_price = 1 - (int(data["bids"][0]["price"]) / MAX_PRICE)
            new_market_entry = Market(market_name, HARDCODED_MARKETS_MAP[market_name], [format(yes_price, ".2f"), format(no_price, ".2f")])
            mongodb_client.create(
                COLLECTION_NAME,
                new_market_entry.__dict__,
            )
            new_market_list.append(new_market_entry)
    return new_market_list

async def init_drift_ws(mongodb_client, arbitrage_handler):
    list_markets = []
    processed_mappings = set()

    for idx_outer, platform_outer in enumerate(PLATFORMS):
        for idx_inner, platform_inner in enumerate(PLATFORMS):
            platforms = [platform_outer, platform_inner]
            platforms.sort()
            mapping_name = f"{platforms[0]}_{platforms[1]}_map"
            
            if idx_outer == idx_inner or (platform_outer != "drift" and platform_inner != "drift") or mapping_name in processed_mappings:
                continue
            
            mapped_drift_markets = mongodb_client.read_all(mapping_name)
            list_markets.extend([mapping["drift_id"] for mapping in mapped_drift_markets])
            processed_mappings.add(mapping_name)
            
    subscription_msgs = list(map(lambda market_name: DriftSubscriptionMessage("subscribe", "perp", "orderbook", market_name), list_markets))
        
    drift_ws_processor = DriftWSProcessor(
        subscription_msgs,
        COLLECTION_NAME,
        mongodb_client,
        arbitrage_handler,
    )
    
    await websocket_handler.open_ws_connection(WS_HOST, drift_ws_processor)