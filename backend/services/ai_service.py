import logging

logger = logging.getLogger(__name__)

class AICoachService:
    def __init__(self):
        logger.info("AICoachService initialized")

    async def get_response(self, user_query: str):
        return {"response": f"Mock AI response for: {user_query}", "status": "success"}