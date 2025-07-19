import os
import json
from typing import Dict, List, Any
from pathlib import Path

class AIKnowledgeBase:
    def __init__(self):
        self.knowledge_base_path = Path("/app/backend/ai_knowledge_base")
        self.knowledge_cache = {}
        
    def load_knowledge_file(self, category: str, filename: str) -> str:
        """Load a specific knowledge file"""
        try:
            file_path = self.knowledge_base_path / category / filename
            if file_path.exists():
                if filename.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    return json.dumps(data, indent=2)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
            return ""
        except Exception as e:
            print(f"Error loading knowledge file {category}/{filename}: {e}")
            return ""
    
    def load_category_knowledge(self, category: str) -> Dict[str, str]:
        """Load all files from a specific category"""
        try:
            category_path = self.knowledge_base_path / category
            if not category_path.exists():
                return {}
            
            knowledge = {}
            for file_path in category_path.glob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    content = self.load_knowledge_file(category, file_path.name)
                    if content:
                        knowledge[file_path.name] = content
            
            return knowledge
        except Exception as e:
            print(f"Error loading category knowledge {category}: {e}")
            return {}
    
    def get_trading_strategies(self) -> str:
        """Get all trading strategy knowledge"""
        strategies = self.load_category_knowledge("trading_strategies")
        if strategies:
            return "\n\n".join([f"**{name}**:\n{content}" for name, content in strategies.items()])
        return ""
    
    def get_market_knowledge(self) -> str:
        """Get South African market specific knowledge"""
        market_info = self.load_category_knowledge("market_knowledge")
        if market_info:
            return "\n\n".join([f"**{name}**:\n{content}" for name, content in market_info.items()])
        return ""
    
    def get_risk_management_rules(self) -> str:
        """Get risk management principles"""
        risk_info = self.load_category_knowledge("risk_management")
        if risk_info:
            return "\n\n".join([f"**{name}**:\n{content}" for name, content in risk_info.items()])
        return ""
    
    def get_crypto_analysis_templates(self) -> str:
        """Get cryptocurrency analysis templates"""
        analysis_templates = self.load_category_knowledge("crypto_analysis")
        if analysis_templates:
            return "\n\n".join([f"**{name}**:\n{content}" for name, content in analysis_templates.items()])
        return ""
    
    def get_user_preferences(self, user_id: str = "default") -> Dict[str, Any]:
        """Get user-specific preferences and trading history"""
        try:
            user_file = f"{user_id}_preferences.json"
            content = self.load_knowledge_file("user_preferences", user_file)
            if content:
                return json.loads(content)
            return {}
        except Exception as e:
            print(f"Error loading user preferences: {e}")
            return {}
    
    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Save user-specific preferences"""
        try:
            user_file = f"{user_id}_preferences.json"
            file_path = self.knowledge_base_path / "user_preferences" / user_file
            with open(file_path, 'w') as f:
                json.dump(preferences, f, indent=2)
        except Exception as e:
            print(f"Error saving user preferences: {e}")
    
    def get_training_data(self) -> str:
        """Load the comprehensive training data for AI bot"""
        try:
            training_file = self.knowledge_base_path / "Trading Data for AIbot.txt"
            if training_file.exists():
                with open(training_file, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            print(f"Error loading training data: {e}")
            return ""
    
    def get_enhanced_context(self, user_id: str = "default") -> str:
        """Get comprehensive knowledge context for AI"""
        context_parts = []
        
        # Trading strategies
        strategies = self.get_trading_strategies()
        if strategies:
            context_parts.append(f"**TRADING STRATEGIES:**\n{strategies}")
        
        # Market knowledge
        market = self.get_market_knowledge()
        if market:
            context_parts.append(f"**SOUTH AFRICAN MARKET KNOWLEDGE:**\n{market}")
        
        # Risk management
        risk = self.get_risk_management_rules()
        if risk:
            context_parts.append(f"**RISK MANAGEMENT RULES:**\n{risk}")
        
        # Crypto analysis templates
        analysis = self.get_crypto_analysis_templates()
        if analysis:
            context_parts.append(f"**ANALYSIS TEMPLATES:**\n{analysis}")
        
        # User preferences
        user_prefs = self.get_user_preferences(user_id)
        if user_prefs:
            context_parts.append(f"**USER PREFERENCES:**\n{json.dumps(user_prefs, indent=2)}")
        
        return "\n\n" + "="*50 + "\n".join(context_parts) + "\n" + "="*50 + "\n"
    
    def add_knowledge_file(self, category: str, filename: str, content: str):
        """Add a new knowledge file"""
        try:
            file_path = self.knowledge_base_path / category / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"Knowledge file added: {category}/{filename}")
        except Exception as e:
            print(f"Error adding knowledge file: {e}")
    
    def list_knowledge_files(self) -> Dict[str, List[str]]:
        """List all available knowledge files by category"""
        categories = {}
        try:
            for category_path in self.knowledge_base_path.iterdir():
                if category_path.is_dir() and not category_path.name.startswith('.'):
                    category_name = category_path.name
                    files = [f.name for f in category_path.glob("*") if f.is_file() and not f.name.startswith('.')]
                    categories[category_name] = files
        except Exception as e:
            print(f"Error listing knowledge files: {e}")
        
        return categories