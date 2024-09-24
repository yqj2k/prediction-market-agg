import requests
import asyncio
from mongo_db_clients import mongodb_client
from dotenv import load_dotenv, dotenv_values

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



def process_feed(event):
    event = FeedEvent(event)
    # find event in db, then update the prices of that event
    query = {"address": event.address}
    existing_market = mongodb_client.read(COLLECTION_NAME, query)
    if not (existing_market is None):
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
        print("We shouldn't be updating a market we haven't processed yet")

def store_last_timestamp(timestamp):
    query = {"_id": "last_feed_call"}
    document = {"_id": "last_feed_call", "value": timestamp} 
    last_called_feed = mongodb_client.read(last_feed_collection, query)
    if last_called_feed == None:
        mongodb_client.create(last_feed_collection, document)
    else:
        mongodb_client.update(last_feed_collection, query, document)
    
    mongodb_client.close()


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
        
        most_recent_timestamp = feed[0]["timestamp"]
        for idx in range(len(feed)):
            curr_event = feed[idx]
            if curr_event["eventType"] != "NEW_TRADE":
                continue
            event = FeedEvent(curr_event)
            process_feed(event)

        store_last_timestamp(most_recent_timestamp)
        print("Done scraping limitless feed")

        # Wait for 1 min (60 seconds) before running again
        await asyncio.sleep(60)
