import requests
import asyncio
from mongo_db_clients import mongodb_client
from dotenv import load_dotenv, dotenv_values
from datetime import datetime

config = dotenv_values(".env")

load_dotenv()

GET = "GET"
HOST = "https://api.limitless.exchange/feed"
mongodb_client = mongodb_client.MongoDBClient(config["ATLAS_URI"], config["DB_NAME"])
COLLECTION_NAME = "limitless_events"
last_feed_collection = "limitless_last_scraped"

# limitless collection should only contain the last updated timestamp we've processed

# we only want NEW_TRADE event_Types
    # funded_market, resolved_market not necessary atm

class FeedEvent:
    def __init__(self, event):
        self.event_type = event["eventType"]
        self.timestamp = event["timestamp"]
        self.title = event["data"]["title"]
        self.address = event["data"]["address"]
        self.strategy = event["data"]["strategy"]
        self.outcome = event["data"]["outcome"]
        self.contracts = event["data"]["contracts"]
        self.symbol = event["data"]["symbol"]
        self.amount = event["data"]["tradeAmount"]
        self.tradeAmountUSD = event["data"]["tradeAmountUSD"]

    def __repr__(self):
        return f"""Event type: {self.event_type}, Timestamp: {self.timestamp}, 
        Title: {self.title}, Address: {self.address}, Strategy: {self.strategy}, 
        Outcome: {self.outcome}, Contracts: {self.contracts}, Symbol: {self.symbol},
        Amount: {self.amount}, AmountUSD: {self.tradeAmountUSD}"""


def process_feed(event):
    event = FeedEvent(event)
    # find event in db, then update the prices of that event
    query = {"address": event.address}
    existing_market = mongodb_client.read(COLLECTION_NAME, query)
    if existing_market is not None:
        new_price = event.amount / event.contracts
        if event.outcome == "YES":
            prices = [new_price, 1 - new_price]
            mongodb_client.update(COLLECTION_NAME, query, prices)
        elif event.outcome == "NO":
            prices = [1 - new_price, new_price]
            mongodb_client.update(COLLECTION_NAME, query, prices)
        else:
            print("outcome for this event is malformed, skipping event: " + event.title)
        pass
    else:
        print("Last feed processed: " + str(event))
        print("We shouldn't be updating a market we haven't processed yet")

def store_last_timestamp(timestamp):
    print("Storing last timestamp")
    query = {"_id": "last_feed_call"}
    document = {"_id": "last_feed_call", "value": timestamp} 
    last_called_feed = mongodb_client.read(last_feed_collection, query)
    if last_called_feed == None:
        mongodb_client.create(last_feed_collection, document)
    else:
        mongodb_client.update(last_feed_collection, query, document)

def get_last_timestamp():
    query = {"_id": "last_feed_call"}
    res = mongodb_client.read(last_feed_collection, query)
    if not res == None:
        return res["value"]
    else:
        return None
    
def compareFeedTimes(cachedFeed, currFeed):
    if cachedFeed == None:
        return False
    print("T1: " + str(cachedFeed[:-1]))
    print("T2: "+ str(currFeed[:-1]))
    formatted_t1 = datetime.fromisoformat(cachedFeed[:-1])
    formatted_t2 = datetime.fromisoformat(currFeed[:-1])
    return formatted_t1 > formatted_t2

async def scrape_limitless_feed():
    while True:
        print("Starting Limitless feed scraper...")
        # Simulate a task by sleeping for a moment
        resp = requests.request(GET, HOST)
        if resp.status_code != 200:
            print("Request to limitless API erroring out, stopping execution")
            return

        feed = resp.json()["data"]

        if len(feed) < 1:
            print("No data extracted, gonna skip this")
            return
        
        last_scraped_timestamp = get_last_timestamp()
        most_recent_timestamp = feed[0]["timestamp"]
        processedFeedAlready = compareFeedTimes(last_scraped_timestamp, most_recent_timestamp)
        if processedFeedAlready:
            print("No new feed to scrape, waiting then reset")
            asyncio.sleep(60)
            return
        
        for idx in range(len(feed) - 1, -1, -1):
            curr_event = feed[idx]
            if curr_event["eventType"] != "NEW_TRADE":
                continue
            process_feed(curr_event)

        store_last_timestamp(most_recent_timestamp)
        print("Done scraping limitless feed")

        # Wait for 1 min (60 seconds) before running again
        await asyncio.sleep(60)
