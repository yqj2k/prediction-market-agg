import requests
from datetime import datetime

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
        self.created_date = datetime.strptime(market["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ") 
        if "deadline" in market:
            self.end_date = datetime.strptime(market["deadline"], "%Y-%m-%dT%H:%M:%S.%fZ") 
        else:
            print("This market is missing a deadline: " + market["address"])
            self.end_date = datetime.strptime("2024-10-05T12:00:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ") 
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

    new_market_list = []
    for market in markets:
        res_markets = market["markets"] if "markets" in market else [market]

        if len(res_markets) > 1:
            res_markets = list(
                map(
                    lambda x: {
                        **x,
                        "title": f"{market["title"]} {x["title"]}",
                        "collateralToken": market["collateralToken"],
                        "deadline": market["deadline"],
                    },
                    res_markets,
                )
            )

        for res_market in res_markets:
            new_market = Market(res_market)
        
            # find if document exists in collection, otherwise push it
            query = {"_id": new_market._id}
            existing_market = mongodb_client.read(COLLECTION_NAME, query)

            if existing_market is None:
                mongodb_client.create(COLLECTION_NAME, new_market.__dict__)
                new_market_list.append(new_market)
    return new_market_list
