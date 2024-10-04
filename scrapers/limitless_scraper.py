import requests

GET = "GET"
POST = "POST"
DELETE = "DELETE"
PUT = "PUT"

HOST = "https://api.limitless.exchange/markets/active"
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
        self.platform = "limitless"


    def __repr__(self):
        return f"Market address:{self.address}, title: {self.title}, createdAt: {self.created_date}, endDate: {self.end_date}, liquidity: {self.liquidity}, volume: {self.volume} \n"


def init_limitless(page_num, mongodb_client):
    paged_req = HOST + f"?page={page_num}"
    resp = requests.request(GET, paged_req)
    if resp.status_code != 200:
        print("Request to limitless API erroring out, stopping execution")
        return
    markets = resp.json()['data']
    while len(markets) > 0:
        new_market_list = []
        for market in markets:
            # print("market: " + str(market))
            m_event = market['markets'] if 'markets' in market else []

            if len(m_event) > 1:
                print(
                    "This is an event with multiple outcomes, skipping for now: {} + id: {}",
                    market["title"]
                )
                continue

            new_market = Market(market)
            new_market_list.append(new_market)

            # find if document exists in collection, otherwise push it
            query = {"address": new_market.address}
            existing_market = mongodb_client.read(COLLECTION_NAME, query)

        new_market = Market(market)

        # find if document exists in collection, otherwise push it
        query = {"_id": new_market._id}
        existing_market = mongodb_client.read(COLLECTION_NAME, query)

        if existing_market is None:
            mongodb_client.create(COLLECTION_NAME, new_market.__dict__)

            # Store each TokenID as K-V (Token - Market Id)
            # mongodb_poly_kv_store_client.set(new_market.tokenIds[0], new_market._id)
            # mongodb_poly_kv_store_client.set(new_market.tokenIds[1], new_market._id)
            new_market_list.append(new_market)

    return new_market_list
