from constants.global_constants import PLATFORMS
from mongo_db_clients.mongodb_client import MongoDBClient
from mongo_db_clients.mongodb_kv_store_client import MongoDBKVStore
from scrapers.drift_scraper import init_drift
from scrapers.limitless_scraper import init_limitless
from scrapers.poly_scraper import init_poly
from dotenv import load_dotenv, dotenv_values
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from datetime import datetime
import logging
import argparse

config = dotenv_values(".env")

load_dotenv()

model = SentenceTransformer("all-MiniLM-L6-v2")

logging.basicConfig(level=logging.INFO)

embedding_cache = {}

def get_embedding(event_name):
    if event_name not in embedding_cache:
        # Compute embedding and store it in the cache
        embedding_cache[event_name] = model.encode(event_name, show_progress_bar=False)
    return embedding_cache[event_name]


# Algo is currently non-deterministic due to the following:
# - Since we are processing matches in batches, there could be a chance that there is a better match for an already matched pair
# - BUG: some matches are not generated on a new initial run for some reason
def match_markets(
    new_markets,
    unmatched_markets,
    unmatched_markets_id_to_idx,
    mongodb_client,
    threshold=0.80,
):
    all_markets = list(map(vars, new_markets)) + unmatched_markets

    # Convert market qeustions to a list
    market_questions = [market["question"] for market in all_markets]

    # Generate embeddings for market questions
    embeddings = [get_embedding(question) for question in market_questions]

    # Compute cosine similarities between embeddings
    cosine_similarities = cosine_similarity(embeddings)

    best_matches = {}

    # Finding the best pairs above the threshold
    for i in range(len(all_markets)):
        for j in range(i + 1, len(all_markets)):
            # Only consider matching events from different platforms
            if (
                all_markets[i]["platform"] != all_markets[j]["platform"]
                and cosine_similarities[i, j] >= threshold
            ):
                # Keep track of the best match for market i
                if (
                    i not in best_matches
                    or cosine_similarities[i, j] > best_matches[i][1]
                ):
                    best_matches[i] = (j, cosine_similarities[i, j])

                # Keep track of the best match for market j
                if (
                    j not in best_matches
                    or cosine_similarities[i, j] > best_matches[j][1]
                ):
                    best_matches[j] = (i, cosine_similarities[i, j])

    matched_indices = set()

    # Finding pairs above the threshold
    for i, (j, similarity) in best_matches.items():
        if i in matched_indices or j in matched_indices:
            continue

        platforms = [all_markets[i]["platform"], all_markets[j]["platform"]]
        platforms.sort()

        # Update unmatched markets' unmatched platforms list
        for market in (all_markets[i], all_markets[j]):
            if market["_id"] in unmatched_markets_id_to_idx:
                unmatched_idx = unmatched_markets_id_to_idx[market["_id"]]
                unmatched_market = unmatched_markets[unmatched_idx]
                if (
                    all_markets[j if market == all_markets[i] else i]["platform"]
                    in unmatched_market["unmatched_platforms"]
                ):
                    unmatched_market["unmatched_platforms"].remove(
                        all_markets[j if market == all_markets[i] else i]["platform"]
                    )

        # Not sure why we sometimes get duplicate matches, temp solution to prevent dupes

        query = {
            f"{all_markets[i]['platform']}_id": all_markets[i]["_id"],
            f"{all_markets[j]['platform']}_id": all_markets[j]["_id"],
        }
        existing_pair = mongodb_client.read("{platforms[0]}_{platforms[1]}_map", query)

        if existing_pair is None:
            mongodb_client.create(
                f"{platforms[0]}_{platforms[1]}_map",
                {
                    f"{all_markets[i]['platform']}_id": all_markets[i]["_id"],
                    f"{all_markets[j]['platform']}_id": all_markets[j]["_id"],
                },
            )
            logging.info(
                "matched: %s and %s with similarity %.2f",
                all_markets[i]["question"],
                all_markets[j]["question"],
                similarity,
            )
            matched_indices.update([i, j])

    new_unmatched_markets = []
    unmatched_markets_id_to_idx.clear()

    # Clear out markets that have been matched in unmatched_markets list
    for idx, market in enumerate(unmatched_markets):
        if len(market["unmatched_platforms"]) > 0:
            new_unmatched_markets.append(market)
            unmatched_markets_id_to_idx[market["_id"]] = len(new_unmatched_markets) - 1

    unmatched_markets.clear()
    unmatched_markets.extend(new_unmatched_markets)

    # Add rest of unmatched markets to unmatched_markets list
    for idx, market in enumerate(all_markets):
        if (
            idx not in matched_indices
            and market["_id"] not in unmatched_markets_id_to_idx
        ):
            market["unmatched_platforms"] = [
                p for p in PLATFORMS if p != market["platform"]
            ]
            unmatched_markets.append(market)
            unmatched_markets_id_to_idx[market["_id"]] = len(unmatched_markets) - 1

    print(len(unmatched_markets))


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Script for processing markets")
    parser.add_argument(
        "--start-date-min",
        type=str,
        help="Optional timestamp in ISO 8601 format (e.g., '2022-04-01T00:00:00')",
    )
    args = parser.parse_args()

    # Parse the start_date_min argument if provided, or set it to None
    start_date_min = args.start_date_min

    # Optional: validate the timestamp format
    if start_date_min:
        try:
            start_date_min = datetime.strptime(start_date_min, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            raise ValueError("Timestamp format should be 'YYYY-MM-DDTHH:MM:SS'")

    mongodb_client = MongoDBClient(config["ATLAS_URI"], config["DB_NAME"])
    mongodb_poly_kv_store_client = MongoDBKVStore(
        config["ATLAS_URI"], config["DB_NAME"], "polymarket_kv_store"
    )

    unmatched_markets = mongodb_client.read_all("unmatched_markets")
    unmatched_markets_id_to_idx = {
        getattr(obj, "_id"): idx for idx, obj in enumerate(unmatched_markets)
    }

    offset = 0
    page_num = 1
    new_markets = []
    
    # Ingest all markets first to prevent duplicates
    
    while True:
        new_poly_markets = init_poly(
            offset,
            mongodb_client,
            mongodb_poly_kv_store_client,
            start_date_min=start_date_min,
        )
        new_drift_markets = init_drift(mongodb_client)
        new_limitless_markets = init_limitless(page_num, mongodb_client)
        
        new_parsed_markets = new_poly_markets + new_drift_markets + new_limitless_markets

        new_markets = new_markets + new_parsed_markets

        offset += 50
        if len(new_parsed_markets) == 0:
            break

    match_markets(
        new_markets,
        unmatched_markets,
        unmatched_markets_id_to_idx,
        mongodb_client,
    )

    for market in unmatched_markets:
        mongodb_client.create("unmatched_markets", market)
