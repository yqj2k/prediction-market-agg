import json
import logging
import sys
import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)

async def subscribe(ws, processor):
    subscribe_msg = processor.createSubcriptionMessage()

    # Send the subscription message
    await ws.send(json.dumps(subscribe_msg.__dict__))
    logging.info("Sent subscription message: %s", subscribe_msg.__dict__)

async def listen(ws, processor):
    try:
        async for message in ws:
            await processor.processMessage(message)
    except json.JSONDecodeError as e:
        logging.error(f"Error while listening: {e}")

async def open_ws_connection(url, processor):    
    async with websockets.connect(url) as ws:
        await subscribe(ws, processor)
        await listen(ws, processor)
