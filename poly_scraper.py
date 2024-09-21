import os
from dotenv import load_dotenv, dotenv_values
import requests
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
        self.id = market['id']
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
        self.outcomes = market['outcomes']
        self.prices = market['outcomePrices']
        self.volume = market['volume']
        self.tokenIds = market['clobTokenIds']

    def __repr__(self):
        return f"Market id:{self.id}, event id: {self.event_id}, description: {self.description}, slug: {self.slug}, createdAt: {self.created_date}, endDate: {self.end_date}, liquidity: {self.liquidity}, outcomes: {self.outcomes}, prices: {self.prices}, volume: {self.volume} \n" 
    


def main():
    host = "https://gamma-api.polymarket.com/markets?active=true&limit=25&liquidity_num_min=1&volume_num_min=1"

    mongodb_client = MongoClient(config["ATLAS_URI"])
    database = mongodb_client[config["DB_NAME"]]
    collection = database["polymarket_events"]
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
        # new_market = Market(market['id'], market['question'], market['createdAt'], market['endDate'], market['liquidity'], market['outcomes'], market['outcomePrices'], market['volume'])
        list_markets.append(new_market)

        # find if document exists in collection, otherwise push it
        query = { 'id': new_market.id }
        if collection.find_one(query) == None:
            res = collection.insert_one(new_market.__dict__)
            print("Inserted document id: "+ str(res.inserted_id))
        else:
            print("Market exists already, updates only happen during WS connection")
    mongodb_client.close()

main()