import requests

from constants.drift_constants import MAX_PRICE
import websocket_handler
from websocket_processors.drift_ws_processor import DriftSubscriptionMessage, DriftWSProcessor

HARDCODED_MARKETS_MAP = {
    "TRUMP-WIN-2024-BET": "Will Donald Trump win the 2024 Presidential Election?",
    "KAMALA-POPULAR-VOTE-2024-BET": "Will Kamala Harris win the popular vote in 2024?",
    "REPUBLICAN-POPULAR-AND-WIN-BET": "Will the Republican Party win the election and popular vote?",
    "BREAKPOINT-IGGYERIC-BET": "Will Iggy Azalea win the celebcoin debate at Solana Breakpoint 2024?",
    "DEMOCRATS-WIN-MICHIGAN-BET": "Will the Democrats win in Michigan?",
}
HARDCODED_MARKETS_NAMES = [
    "TRUMP-WIN-2024-BET",
    "KAMALA-POPULAR-VOTE-2024-BET",
    "REPUBLICAN-POPULAR-AND-WIN-BET",
    "BREAKPOINT-IGGYERIC-BET",
    "DEMOCRATS-WIN-MICHIGAN-BET",
]

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

def init_drift(mongodb_client):
    for market_name in HARDCODED_MARKETS_NAMES:
        resp = requests.request(GET, HOST + market_name)
        if resp.status_code != 200:
            print("Request to dlob drift API erroring out, stopping execution")
            return

        data = resp.json()

        query = {"_id": market_name}
        existing_market = mongodb_client.read(COLLECTION_NAME, query)
        if existing_market is None:
            yes_price = int(data["asks"][0]["price"]) / MAX_PRICE
            no_price = 1 - (int(data["bids"][0]["price"]) / MAX_PRICE)
            mongodb_client.create(
                COLLECTION_NAME,
                {
                    "_id": market_name,
                    "name": HARDCODED_MARKETS_MAP[market_name],
                    "prices": [format(yes_price, ".2f"), format(no_price, ".2f")],
                },
            )

async def init_drift_ws(mongodb_client, arbitrage_handler):
    subscription_msgs = []
    for market_name in HARDCODED_MARKETS_NAMES:
        subscription_msgs.append(DriftSubscriptionMessage("subscribe", "perp", "orderbook", market_name))
        
    drift_ws_processor = DriftWSProcessor(
        subscription_msgs,
        COLLECTION_NAME,
        mongodb_client,
        arbitrage_handler,
    )
    
    await websocket_handler.open_ws_connection(WS_HOST, drift_ws_processor)