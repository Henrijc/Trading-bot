import logging
from typing import List, Dict, Any, Optional

# Corrected import for emergent_mock
from backend.services.emergent_mock import LlmChat, UserMessage

logger = logging.getLogger(__name__)

class AICoachService:
    def __init__(self, model_name: str = "gemini-pro"):
        self.llm_chat = LlmChat(model_name=model_name)
        self.conversation_history = [] # Stores list of UserMessage/LlmChat objects
        logger.info(f"AICoachService initialized with model: {model_name}")

    def add_message(self, role: str, content: str):
        """Adds a message to the conversation history."""
        if role == "user":
            self.conversation_history.append(UserMessage(content))
        elif role == "model":
            self.conversation_history.append(LlmChat(content))
        else:
            logger.warning(f"Unsupported role: {role}. Message not added to history.")

    async def get_response(self, user_query: str) -> Dict[str, Any]:
        """
        Sends a query to the LLM and gets a response.
        Adds query and response to conversation history.
        """
        try:
            # Add the user's query to history before sending
            self.add_message("user", user_query)

            # Send the message to the LLM
            response_content = await self.llm_chat.send_message(user_query, history=self.conversation_history[:-1]) # Exclude current user query from history for sending, as send_message will add it

            # Add the model's response to history
            self.add_message("model", response_content)

            logger.info(f"Received AI response for query: {user_query[:50]}...")
            return {"response": response_content, "history_length": len(self.conversation_history)}
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return {"error": str(e), "response": "Could not get a response from AI service."}

    def get_full_history(self) -> List[Dict[str, str]]:
        """Returns the full conversation history in a list of dicts."""
        return [{"role": msg.role, "content": msg.content} for msg in self.conversation_history]

    def clear_history(self):
        """Clears the conversation history."""
        self.conversation_history = []
        logger.info("AI conversation history cleared.")

    async def analyze_sentiment(self, text: str) -> Dict[str, str]:
        """Analyzes sentiment of a given text using the LLM."""
        try:
            prompt = f"Analyze the sentiment of the following text (positive, negative, neutral): '{text}'"
            response = await self.llm_chat.send_message(prompt)
            logger.info(f"Sentiment analysis for '{text[:30]}...': {response}")
            return {"sentiment": response.strip().lower()}
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"error": str(e)}

    async def summarize_text(self, text: str, max_words: int = 50) -> Dict[str, str]:
        """Summarizes a given text using the LLM."""
        try:
            prompt = f"Summarize the following text in maximum {max_words} words: '{text}'"
            response = await self.llm_chat.send_message(prompt)
            logger.info(f"Summarized text '{text[:30]}...': {response}")
            return {"summary": response.strip()}
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return {"error": str(e)}

# Mock implementation (as per WARNING in logs)
# This class would typically live in its own file or be part of a real integration
# For the sake of getting the app running, we assume a simple mock or it exists.
# If this part is from a separate 'emergent_mock.py' file, that file needs to be there.
# WARNING: The log indicated 'services.emergent_mock' not found. This mock needs to be a real module.
# IF THIS IS ACTUALLY A MOCK, WE NEED TO ENSURE THE 'emergent_mock.py' FILE EXISTS
# IN /app/backend/services/
class LlmChat:
    def __init__(self, model_name: str = "mock-llm"):
        self.model_name = model_name
        logger.warning(f"Using mock LlmChat for {model_name}. No actual AI calls will be made.")

    async def send_message(self, message: str, history: Optional[List[Any]] = None) -> str:
        logger.warning(f"Mock LlmChat received message: {message}. Returning dummy response.")
        return f"Mock response for '{message[:50]}...' from {self.model_name}. (This is a mock, replace with real LLM integration)"

class UserMessage:
    def __init__(self, content: str):
        self.content = content
        self.role = "user"