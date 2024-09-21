import uuid
from typing import Optional
from pydantic import BaseModel, Field

class Market(BaseModel):
    id: str = Field(alias="market_id")
    event_id: str = Field(alias="event_id")
    slug: str = Field(alias="slug")
    created_at: str = Field(alias="created_at")
    end_date: str = Field(alias="end_date")
    liquidity: str = Field(alias="liquidity")
    outcomes: list[str] = Field(alias="outcomes") # Idx 0 = YES, Idx 1 = NO
    prices: list[str] = Field(alias="prices") # Idx 0 = YES, Idx 1 = NO
    volume: str = Field(alias="volume")
    

class UpdateMarket(BaseModel):
    liquidity: Optional[str]
    outcomes: Optional[ list[str] ]
    prices: Optional[ list[str] ]
    volume: Optional[str]
