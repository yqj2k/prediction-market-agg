import requests
import json
from datetime import datetime
from constants.global_constants import PLATFORMS
import websocket_handler
from websocket_processors.poly_ws_processor import (
    PolySubscriptionMessage,
    PolyWSProcessor,
)


GET = "GET"
POST = "POST"
DELETE = "DELETE"
PUT = "PUT"

HOST = "https://gamma-api.polymarket.com/markets?active=true&limit=50&order=slug"
WS_HOST = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
COLLECTION_NAME = "poly_events"


# task
# query + store gamma api responses to db
# unique market events
# can't use clob client wrapper, it only queries clob endpoints

# endpoint optional params
# active: if it's an active event or nah
# limit: number of events to pick up
# min liquidity + volume: needed for cleaning data + access to good events


class Market:
    def __init__(self, market, events):
        self._id = market["id"]
        self.question = market["question"]
        self.event_id = market["events"][0]["id"]
        self.description = events[0]["title"]
        self.slug = events[0]["slug"]
        self.created_date = datetime.strptime(
            market["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        if "endDate" in market:
            self.end_date = datetime.strptime(market["endDate"], "%Y-%m-%dT%H:%M:%SZ")
        else:
            print("This market is missing an end date: " + market["id"])
            self.end_date = datetime.strptime(
                "2024-10-05T12:00:00Z", "%Y-%m-%dT%H:%M:%SZ"
            )
        if "liquidity" in market:
            self.liquidity = market["liquidity"]
        else:
            self.liquidity = "0"
        self.outcomes = json.loads(market["outcomes"])
        self.prices = json.loads(market["outcomePrices"])
        if "volume" in market:
            self.volume = market["volume"]
        else:
            print("This market is missing volume: " + market["id"])
            self.volume = "0"
        if "clobTokenIds" in market:
            self.tokenIds = json.loads(market["clobTokenIds"])
        else:
            print("This market is missing clobTokenIds: " + market["clobTokenIds"])
            self.tokenIds = []
        self.platform = "poly"

    def __repr__(self):
        return f"Market id:{self.id}, event id: {self.event_id}, description: {self.description}, slug: {self.slug}, createdAt: {self.created_date}, endDate: {self.end_date}, liquidity: {self.liquidity}, outcomes: {self.outcomes}, prices: {self.prices}, volume: {self.volume} \n"


def init_poly(
    offset, mongodb_client, mongodb_poly_kv_store_client, start_date_min=None
):
    base_url = f"{HOST}&offset={offset}"

    if start_date_min:
        base_url += f"&start_date_min={start_date_min.strftime("%Y-%m-%dT%H:%M:%S")}"

    resp = requests.request(GET, base_url)
    if resp.status_code != 200:
        print("Request to gamma API erroring out, stopping execution")
        return

    markets = resp.json()

    new_market_list = []
    for market in markets:
        m_event = market["events"]

        if len(m_event) > 1:
            print(
                "This market has multiple events: {} + id: {}",
                market["description"],
                market["id"],
            )
            continue

        new_market = Market(market, m_event)

        # find if document exists in collection, otherwise push it
        query = {"_id": new_market._id}
        existing_market = mongodb_client.read(COLLECTION_NAME, query)

        if existing_market is None:
            mongodb_client.create(COLLECTION_NAME, new_market.__dict__)

            # Store each TokenID as K-V (Token - Market Id)
            mongodb_poly_kv_store_client.set(new_market.tokenIds[0], new_market._id)
            mongodb_poly_kv_store_client.set(new_market.tokenIds[1], new_market._id)

            new_market_list.append(new_market)
    return new_market_list


async def init_poly_ws(mongodb_client, mongodb_poly_kv_store_client, arbitrage_handler):
    list_markets = []
    processed_mappings = set()
    
    for idx_outer, platform_outer in enumerate(PLATFORMS):
        for idx_inner, platform_inner in enumerate(PLATFORMS):
            platforms = [platform_outer, platform_inner]
            platforms.sort()
            mapping_name = f"{platforms[0]}_{platforms[1]}_map"
            
            if idx_outer == idx_inner or (
                platform_outer != "poly" and platform_inner != "poly"
            ) or mapping_name in processed_mappings:
                continue
            
            mapped_poly_markets = mongodb_client.read_all(
                mapping_name
            )

            query = {
                "_id": {"$in": [mapping["poly_id"] for mapping in mapped_poly_markets]}
            }
            
            list_markets = list_markets + mongodb_client.read_all_with_query(COLLECTION_NAME, query)
            processed_mappings.add(mapping_name)

    all_token_ids = [market["tokenIds"] for market in list_markets]
    flattened_token_ids = [
        token_id for sublist in all_token_ids for token_id in sublist
    ]

    poly_ws_processor = PolyWSProcessor(
        [PolySubscriptionMessage({}, [], flattened_token_ids, "Market")],
        COLLECTION_NAME,
        mongodb_client,
        mongodb_poly_kv_store_client,
        arbitrage_handler,
    )

    await websocket_handler.open_ws_connection(WS_HOST, poly_ws_processor)
