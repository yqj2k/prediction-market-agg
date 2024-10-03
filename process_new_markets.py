from mongo_db_clients.mongodb_client import MongoDBClient
from mongo_db_clients.mongodb_kv_store_client import MongoDBKVStore
from scrapers.drift_scraper import init_drift
from scrapers.limitless_scraper import init_limitless
from scrapers.poly_scraper import init_poly
from dotenv import load_dotenv, dotenv_values
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import logging

config = dotenv_values(".env")

load_dotenv()

model = SentenceTransformer("all-MiniLM-L6-v2")

logging.basicConfig(level=logging.INFO)


def match_markets(new_markets, unmatched_markets, unmatched_markets_id_to_idx, mongodb_client, threshold=0.80):
    all_markets = list(map(vars, new_markets)) + unmatched_markets

    # Convert event names to a list
    market_questions = [market["question"] for market in all_markets]

    # Generate embeddings for event names
    embeddings = model.encode(market_questions, convert_to_tensor=True)

    # Compute cosine similarities between embeddings
    cosine_similarities = cosine_similarity(embeddings)

    matched_indices = set()

    # Finding pairs above the threshold
    for i in range(len(all_markets)):
        for j in range(i + 1, len(all_markets)):
            # Only consider matching events from different sites
            if (
                all_markets[i]["platform"] != all_markets[j]["platform"]
                and cosine_similarities[i, j] >= threshold
            ):
                platforms = [all_markets[i]["platform"], all_markets[j]["platform"]]
                platforms.sort()
                
                if all_markets[i]["_id"] in unmatched_markets_id_to_idx:
                    unmatched_markets.pop(unmatched_markets_id_to_idx.get(all_markets[i]["_id"]))
                    unmatched_markets_id_to_idx.pop(all_markets[i]["_id"])
                if all_markets[j]["_id"] in unmatched_markets_id_to_idx:
                    unmatched_markets.pop(unmatched_markets_id_to_idx.get(all_markets[j]["_id"]))
                    unmatched_markets_id_to_idx.pop(all_markets[j]["_id"])

                mongodb_client.create(
                    f"{platforms[0]}_{platforms[1]}_map",
                    {
                        f"{all_markets[i]['platform']}_id": all_markets[i]["_id"],
                        f"{all_markets[j]['platform']}_id": all_markets[j]["_id"],
                    },
                )
                logging.info(
                    "matched: %s and %s",
                    all_markets[i]["question"],
                    all_markets[j]["question"],
                )
                matched_indices.update([i, j])

    for idx, market in enumerate(all_markets):
        if idx not in matched_indices and market["_id"] not in unmatched_markets_id_to_idx:
            unmatched_markets.append(market)
            unmatched_markets_id_to_idx[market["_id"]] = len(unmatched_markets) - 1
            
if __name__ == "__main__":
    mongodb_client = MongoDBClient(config["ATLAS_URI"], config["DB_NAME"])
    mongodb_poly_kv_store_client = MongoDBKVStore(
        config["ATLAS_URI"], config["DB_NAME"], "polymarket_kv_store"
    )

    unmatched_markets = mongodb_client.read_all("unmatched_markets")
    unmatched_markets_id_to_idx = {getattr(obj, "_id"): idx for idx, obj in enumerate(unmatched_markets)}

    offset = 0
    while True:
        new_poly_markets = init_poly(
            offset, mongodb_client, mongodb_poly_kv_store_client
        )
        new_drift_markets = init_drift(mongodb_client)
        new_limitless_markets = init_limitless(mongodb_client)

        new_markets = new_poly_markets + new_drift_markets + new_limitless_markets

        offset += 50
        if len(new_markets) == 0:
            break
        else:
            match_markets(new_markets, unmatched_markets, unmatched_markets_id_to_idx, mongodb_client)
            continue
    
    for market in unmatched_markets:
        mongodb_client.create("unmatched_markets", market)
    
