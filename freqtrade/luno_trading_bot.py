import os
import sys
import logging
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('user_data/logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class LunoTradingBot:
    def __init__(self):
        logger.info("Luno Trading Bot initialized")
        
    async def run(self):
        logger.info("Luno Trading Bot starting...")
        while True:
            try:
                logger.info(f"Bot running at {datetime.now()}")
                await asyncio.sleep(60)  # Run every minute
            except Exception as e:
                logger.error(f"Bot error: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    bot = LunoTradingBot()
    asyncio.run(bot.run())