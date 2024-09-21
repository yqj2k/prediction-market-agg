import asyncio
from websocket_processors.poly_ws_processor import PolyWSProcessor, PolySubscriptionMessage
import websocket_handler
import signal
import logging
import sys

async def main():

    
    poly_ws_processor = PolyWSProcessor(PolySubscriptionMessage(
        {},
        [], 
        [
            "21742633143463906290569050155826241533067272736897614950488156847949938836455",
            "48331043336612883890938759509493159234755048973500640148014422747788308965732"
        ],
        "Market"  
    ))
    await websocket_handler.open_ws_connection("wss://ws-subscriptions-clob.polymarket.com/ws/market", poly_ws_processor)


def signal_handler(sig, frame):
    logging.info("Interrupt received, closing connection")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())