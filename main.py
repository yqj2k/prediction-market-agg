from fastapi import FastAPI
from dotenv import dotenv_values
from pymongo import MongoClient
from contextlib import asynccontextmanager
from routes import router as market_router

config = dotenv_values(".env")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    app.mongodb_client = MongoClient(config["ATLAS_URI"])
    app.database = app.mongodb_client[config["DB_NAME"]]
    print("Connected to Polymarket MongoDB database!")
    yield
    
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan)

app.include_router(market_router, tags=["markets"], prefix="/markets")