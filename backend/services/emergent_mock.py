"""
Mock implementation for emergentintegrations
This provides fallback functionality when emergentintegrations is not available
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class UserMessage:
    """Mock UserMessage class"""
    def __init__(self, content: str):
        self.content = content
        self.role = "user"

class LlmChat:
    """Mock LlmChat class for emergentintegrations fallback"""
    
    def __init__(self, model_name: str = "mock-llm"):
        self.model_name = model_name
        logger.warning(f"Using mock LlmChat for {model_name}. No actual AI calls will be made.")
    
    async def send_message(self, message: str, history: Optional[List[Any]] = None) -> str:
        """Mock send_message implementation"""
        logger.warning(f"Mock LlmChat received message: {message[:50]}... Returning dummy response.")
        
        # Provide basic mock responses based on message content
        if "market" in message.lower() or "crypto" in message.lower():
            return f"Mock analysis: The cryptocurrency market is showing mixed signals. This is a mock response for development purposes."
        elif "trade" in message.lower() or "buy" in message.lower() or "sell" in message.lower():
            return f"Mock trading advice: Consider your risk tolerance before making any trades. This is a mock response."
        elif "portfolio" in message.lower():
            return f"Mock portfolio analysis: Your portfolio appears to be well-diversified. This is a mock response."
        else:
            return f"Mock response for '{message[:30]}...' from {self.model_name}. (This is a mock, replace with real LLM integration)"
    
    def send_message_sync(self, message: str, history: Optional[List[Any]] = None) -> str:
        """Synchronous version of send_message"""
        return asyncio.run(self.send_message(message, history))