import json
import logging
import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)

async def subscribe(ws, processor):
    subscribe_msgs = processor.createSubcriptionMessages()

    # Send the subscription message
    for subscription_msg in subscribe_msgs:
        await ws.send(json.dumps(subscription_msg.__dict__))
        logging.info("Sent subscription message: %s", subscription_msg.__dict__)

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
