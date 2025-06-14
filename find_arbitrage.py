import asyncio
from arbitrage_handler import ArbitrageHandler
from mongo_db_clients.mongodb_client import MongoDBClient
from mongo_db_clients.mongodb_kv_store_client import MongoDBKVStore
from scrapers.drift_scraper import init_drift, init_drift_ws
from scrapers.poly_scraper import init_poly, init_poly_ws
from scrapers.limitless_scraper import init_limitless
from websocket_processors.limitless_ws_processor import scrape_limitless_feed
import signal
import logging
import sys
from dotenv import load_dotenv, dotenv_values

config = dotenv_values(".env")

load_dotenv()


def signal_handler(sig, frame):
    logging.info("Interrupt received, closing connection")
    sys.exit(0)

async def run_ws(mongodb_client, mongodb_poly_kv_store_client, arbitrage_handler):
    # Schedule three calls *concurrently*:
    await asyncio.gather(
        init_poly_ws(mongodb_client, mongodb_poly_kv_store_client, arbitrage_handler),
        init_drift_ws(mongodb_client, arbitrage_handler),
        # scrape_limitless_feed()
    )

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    mongodb_client = MongoDBClient(config["ATLAS_URI"], config["DB_NAME"])
    mongodb_poly_kv_store_client = MongoDBKVStore(
        config["ATLAS_URI"], config["DB_NAME"], "polymarket_kv_store"
    )
    arbitrage_handler = ArbitrageHandler(mongodb_client)
    
    asyncio.run(
        run_ws(mongodb_client, mongodb_poly_kv_store_client, arbitrage_handler),
    )
