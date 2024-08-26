import os
from dotenv import load_dotenv
import requests

load_dotenv()

GET = "GET"
POST = "POST"
DELETE = "DELETE"
PUT = "PUT"

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
        self.id = market['id']
        # self.question = market['question']
        self.event_id = market[0]['id']
        self.description = events[0]['title']
        self.slug = events[0]['slug']
        self.created_date = market['createdAt']
        self.end_date = market['endDate']
        if 'liquidity' in market:
            self.liquidity = market['liquidity']
        else:
            self.liquidity = '0'
        self.outcomes = market['outcomes']
        self.prices = market['outcomePrices']
        self.volume = market['volume']

    def __repr__(self):
        return f"Market id:{self.id}, event id: {self.event_id}, description: {self.description}, slug: {self.slug}, createdAt: {self.created_date}, endDate: {self.end_date}, liquidity: {self.liquidity}, outcomes: {self.outcomes}, prices: {self.prices}, volume: {self.volume} \n" 
    
    


def main():
    host = "https://gamma-api.polymarket.com/markets?active=true&limit=25&liquidity_num_min=1&volume_num_min=1"

    resp = requests.request(GET, host)
    if resp.status_code != 200:
        print("Request to gamma API erroring out, stopping execution")
        return
    print("STATUS CODE: " + str(resp.status_code))
    print("num of markets: " + str( len( resp.json() ) ) )
    markets = resp.json()
    # print(markets)
    list_markets = []
    for market in markets:
        m_event = market['events']
        
        if len(m_event) > 1:
            print("This market has multiple events: {} + id: {}", market['description'], market['id'])
            continue
        new_market = Market(market, m_event)
        # new_market = Market(market['id'], market['question'], market['createdAt'], market['endDate'], market['liquidity'], market['outcomes'], market['outcomePrices'], market['volume'])
        list_markets.append(new_market)
    print(list_markets)


main()