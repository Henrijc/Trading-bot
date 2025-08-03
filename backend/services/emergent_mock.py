# Temporary mock for emergentintegrations until proper package is available
"""
Mock implementation of emergentintegrations.llm.chat module
This allows the application to run while the real package is being resolved
"""

class UserMessage:
    def __init__(self, text: str):
        self.text = text

class LlmChat:
    def __init__(self, api_key: str, session_id: str = None, system_message: str = None):
        self.api_key = api_key
        self.session_id = session_id
        self.system_message = system_message
        self.model_name = "gemini"
        self.model_version = "gemini-2.0-flash"
        self.max_tokens = 4000
        
    def with_model(self, provider: str, model: str):
        """Chain method to set model"""
        self.model_name = provider
        self.model_version = model
        return self
        
    def with_max_tokens(self, tokens: int):
        """Chain method to set max tokens"""
        self.max_tokens = tokens
        return self
        
    async def send_message(self, message: UserMessage) -> str:
        """Send message using Google Gemini API"""
        try:
            import google.generativeai as genai
            
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Build full prompt with system message
            full_prompt = ""
            if self.system_message:
                full_prompt += f"System: {self.system_message}\n\n"
            full_prompt += f"User: {message.text}"
            
            # Generate response
            response = await model.generate_content_async(full_prompt)
            return response.text
            
        except Exception as e:
            print(f"Error in mock LlmChat: {e}")
            # Fallback response if Gemini fails
            return f"""I'm currently experiencing technical difficulties with the AI service. 

Your message has been received: "{message.text[:100]}..."

**Your Trading Goals Noted:**
- Monthly profit target: R100,000
- Risk management: Conservative approach
- Portfolio optimization focus

**Available Actions:**
- Check your portfolio on the Dashboard tab
- Review Technical Analysis for market insights
- View trading opportunities in the Campaign tab

I'll be back online shortly to provide detailed trading advice."""