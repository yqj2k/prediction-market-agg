import requests
import json

import websocket_handler
from websocket_processors.limitless_ws_processor import (
    LimitlessWSProcessor
)


GET = "GET"
POST = "POST"
DELETE = "DELETE"
PUT = "PUT"

HOST = "https://api.limitless.exchange/markets/active"
WS_HOST = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
COLLECTION_NAME = "limitless_events"

# for betting URL, limitless.exchange/markets/{address} 

class Market:
    def __init__(self, market):
        # print("individual market: " + str(market))
        self._id = market["address"]
        self.question = market["title"]
        self.created_date = market["createdAt"]
        if "deadline" in market:
            self.end_date = market["deadline"]
        else:
            print("This market is missing a deadline: " + market["address"])
            self.end_date = "2025-12-31T12:00:00Z"
        self.liquidity = market["liquidityFormatted"]
        self.volume = market["volumeFormatted"]
        self.collateralAsset = market["collateralToken"]["symbol"]
        self.outcomes = ["Yes", "No"]
        self.prices = None


    def __repr__(self):
        return f"Market address:{self.address}, title: {self.title}, createdAt: {self.created_date}, endDate: {self.end_date}, liquidity: {self.liquidity}, volume: {self.volume} \n"


def init_limitless(mongodb_client):
    resp = requests.request(GET, HOST)
    if resp.status_code != 200:
        print("Request to limitless API erroring out, stopping execution")
        return

    markets = resp.json()

    list_markets = []
    for market in markets:
        print(market)
        m_event = market['markets'] if 'markets' in market else []

        if len(m_event) > 1:
            print(
                "This is an event with multiple outcomes, skipping for now: {} + id: {}",
                market["title"]
            )
            continue

        new_market = Market(market)
        list_markets.append(new_market)

        # find if document exists in collection, otherwise push it
        query = {"_id": new_market._id}
        existing_market = mongodb_client.read(COLLECTION_NAME, query)

        if existing_market is None:
            res = mongodb_client.create(COLLECTION_NAME, new_market.__dict__)

            # Store each TokenID as K-V (Token - Market Id)
            # mongodb_poly_kv_store_client.set(new_market.tokenIds[0], new_market._id)
            # mongodb_poly_kv_store_client.set(new_market.tokenIds[1], new_market._id)

            print("Inserted document id: " + str(res))
        else:
            print("Market exists already, updates only happen during WS/feed connection")


# async def init_limitless_ws(mongodb_client, arbitrage_handler):
#     list_markets = mongodb_client.read_all(COLLECTION_NAME)

#     all_addresses = [market["tokenIds"] for market in list_markets]
#     flattened_token_ids = [
#         token_id for sublist in all_token_ids for token_id in sublist
#     ]

#     poly_ws_processor = PolyWSProcessor(
#         [PolySubscriptionMessage({}, [], flattened_token_ids, "Market")],
#         COLLECTION_NAME,
#         mongodb_client,
#         mongodb_poly_kv_store_client,
#         arbitrage_handler,
#     )

#     await websocket_handler.open_ws_connection(WS_HOST, poly_ws_processor)
