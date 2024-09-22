import os
from dotenv import load_dotenv, dotenv_values
import requests
import signal
import logging
import sys
import asyncio
import json

from mongodb_kv_store_client import MongoDBKVStore
import websocket_handler
from websocket_processors.poly_ws_processor import PolySubscriptionMessage, PolyWSProcessor
from mongodb_client import MongoDBClient

config = dotenv_values(".env")

load_dotenv()

GET = "GET"
POST = "POST"
DELETE = "DELETE"
PUT = "PUT"

from pymongo import MongoClient

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
    # def __init__(self, id, question, created_date, end_date, liquidity, outcomes, prices, volume):
        # check_correct_values(id, question, created_date, end_date, liquidity, outcomes, prices, volume)
        # print("individual market: " + str(market))
        self._id = market['id']
        self.question = market['question']
        self.event_id = market['events'][0]['id']
        self.description = events[0]['title']
        self.slug = events[0]['slug']
        self.created_date = market['createdAt']
        if 'endDate' in market:
            self.end_date = market['endDate']
        else:
            print("This market is missing an end date: " + market['id'])
            self.end_date = '2025-12-31T12:00:00Z'
        if 'liquidity' in market:
            self.liquidity = market['liquidity']
        else:
            self.liquidity = '0'
        self.outcomes = json.loads(market['outcomes'])
        self.prices = json.loads(market['outcomePrices'])
        self.volume = market['volume']
        self.tokenIds = json.loads(market['clobTokenIds'])

    def __repr__(self):
        return f"Market id:{self.id}, event id: {self.event_id}, description: {self.description}, slug: {self.slug}, createdAt: {self.created_date}, endDate: {self.end_date}, liquidity: {self.liquidity}, outcomes: {self.outcomes}, prices: {self.prices}, volume: {self.volume} \n" 
    


async def main():
    host = "https://gamma-api.polymarket.com/markets?active=true&limit=25&liquidity_num_min=1&volume_num_min=1"

    mongodb_client = MongoDBClient(config["ATLAS_URI"], config["DB_NAME"])
    mongodb_poly_kv_store_client = MongoDBKVStore(config["ATLAS_URI"], config["DB_NAME"], "polymarket_kv_store")
    
    collection_name = "polymarket_events"
    print("Connected to Polymarket MongoDB database!")

    resp = requests.request(GET, host)
    if resp.status_code != 200:
        print("Request to gamma API erroring out, stopping execution")
        return
    
    print("num of markets: " + str( len( resp.json() ) ) )
    markets = resp.json()
    
    list_markets = []
    for market in markets:
        m_event = market['events']
        
        if len(m_event) > 1:
            print("This market has multiple events: {} + id: {}", market['description'], market['id'])
            continue
        
        new_market = Market(market, m_event)
        list_markets.append(new_market)

        # find if document exists in collection, otherwise push it
        query = {'_id': new_market._id}
        existing_market = mongodb_client.read(collection_name, query)
        
        if existing_market == None:
            res = mongodb_client.create(collection_name, new_market.__dict__)
            
            # Store each TokenID as K-V (Token - Market Id)
            mongodb_poly_kv_store_client.set(new_market.tokenIds[0], new_market._id)
            mongodb_poly_kv_store_client.set(new_market.tokenIds[1], new_market._id)
            
            print("Inserted document id: "+ str(res))
        else:
            print("Market exists already, updates only happen during WS connection")
            
    all_token_ids = [market.tokenIds for market in list_markets]
    flattened_token_ids = [token_id for sublist in all_token_ids for token_id in sublist]
    
    poly_ws_processor = PolyWSProcessor(PolySubscriptionMessage(
        {},
        [], 
        flattened_token_ids,
        "Market"  
    ), collection_name, mongodb_client, mongodb_poly_kv_store_client)
    
    await websocket_handler.open_ws_connection("wss://ws-subscriptions-clob.polymarket.com/ws/market", poly_ws_processor)

def signal_handler(sig, frame):
    logging.info("Interrupt received, closing connection")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())