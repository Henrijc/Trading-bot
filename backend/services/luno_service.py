import logging

logger = logging.getLogger(__name__)

class LunoService:
    def __init__(self):
        logger.info("LunoService initialized")

    def get_ticker(self, pair="XBTZAR"):
        return {"pair": pair, "price": "1000000", "status": "success"}