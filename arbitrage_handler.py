import logging

logging.basicConfig(level=logging.INFO)


class ArbitrageHandler:
    def __init__(self, db_client):
        self.db_client = db_client

    def handle(self, source, price_change_event):
        logging.info("From %s - %s", source, price_change_event)
