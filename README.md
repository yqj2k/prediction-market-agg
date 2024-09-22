# prediction-market-agg
aggregating prediction market data for arbs n shhiii

# run api locally

Create .env file with ATLAS_URI and DB_NAME
`pip install -r requirements.txt`
`python find_arbitrage.py`    


### to debug

`python find_arbitrage.py >> response.json`

## Order of operations
- Query markets endpoint. Markets contain the odds
- take events metadata (ie. slug, description). Slug contains URL of the single event

## Get slug from event to polymarket URL:
- take slug from event data (ie. 'superbowl-champion-2025' )
- URL is polymarket.com/event/{slug}

## problems
- Create DB entry works, but returns error 500