from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List

from models import Market, UpdateMarket

router = APIRouter()

@router.post("/", response_description="Create a new market", status_code=status.HTTP_201_CREATED, response_model=Market)
def create_market(request: Request, market: Market = Body()):
    market = jsonable_encoder(market)
    new_market = request.app.database["polymarket_events"].insert_one(market)
    created_market = request.app.database["polymarket_events"].find_one(
        {"market_id": new_market.inserted_id}
    )

    return created_market



@router.get("/", response_description="List all markets", response_model=List[Market])
def list_markets(request: Request):
    markets = list(request.app.database["polymarket_events"].find(limit=100))
    return markets


@router.get("/{market_id}", response_description="Get a single Market by market_id", response_model=Market)
def find_market(market_id: str, request: Request):
    if (market := request.app.database["polymarket_events"].find_one({"market_id": market_id})) is not None:
        return market
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"market with market_id {market_id} not found")


@router.put("/{market_id}", response_description="Update a market", response_model=UpdateMarket)
def update_market(market_id: str, request: Request, market: UpdateMarket = Body()):
    market = {k: v for k, v in market.model_dump().items() if v is not None}
    if len(market) >= 1:
        update_result = request.app.database["polymarket_events"].update_one(
            {"market_id": market_id}, {"$set": market}
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"market with ID {id} not found")

    if (
        existing_market := request.app.database["polymarket_events"].find_one({"market_id": market_id})
    ) is not None:
        return existing_market

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Market with market_ID {market_id} not found")


@router.delete("/{market_id}", response_description="Delete a market")
def delete_market(market_id: str, request: Request, response: Response):
    delete_result = request.app.database["polymarket_events"].delete_one({"market_id": market_id})

    if delete_result.deleted_count == 1:
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Market with market_id {market_id} not found")