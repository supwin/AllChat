# app/config/settings.py
import os
import google.generativeai as genai
import openai

# Import functions for AI model tools
from ..services.firebase_utils import (
    update_bot_persona, update_knowledge_base, update_line_token,
    update_business_type, update_product_recommendation_setting,
    update_booking_settings, update_project_status_setting,
    update_chatbot_general_settings
)

# Private global variables to store initialized models
_end_user_model_instance = None
_wizard_model_instance = None
_openai_client_instance = None

def get_gemini_end_user_model():
    """Returns the initialized Gemini end-user model instance."""
    global _end_user_model_instance
    if _end_user_model_instance is None:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                _end_user_model_instance = genai.GenerativeModel('gemini-1.5-flash')
                print("✅ Gemini end-user model initialized on first access.")
            except Exception as e:
                print(f"❌ CRITICAL: Could not configure Gemini API for end-user model: {e}")
        else:
            print("⚠️ GEMINI_API_KEY not found. Gemini end-user model will not be available.")
    return _end_user_model_instance

def get_gemini_wizard_model():
    """Returns the initialized Gemini wizard model instance."""
    global _wizard_model_instance
    if _wizard_model_instance is None:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY) # Configure might be called multiple times, but it's idempotent
                tools = [
                    update_bot_persona, update_knowledge_base, update_line_token,
                    update_business_type, update_product_recommendation_setting,
                    update_booking_settings, update_project_status_setting,
                    update_chatbot_general_settings
                ]
                _wizard_model_instance = genai.GenerativeModel('gemini-1.5-flash', tools=tools)
                print("✅ Gemini wizard model initialized on first access.")
            except Exception as e:
                print(f"❌ CRITICAL: Could not configure Gemini API for wizard model: {e}")
        else:
            print("⚠️ GEMINI_API_KEY not found. Gemini wizard model will not be available.")
    return _wizard_model_instance

def get_openai_client():
    """Returns the initialized OpenAI client instance."""
    global _openai_client_instance
    if _openai_client_instance is None:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if OPENAI_API_KEY:
            try:
                _openai_client_instance = openai.OpenAI(api_key=OPENAI_API_KEY)
                print("✅ OpenAI client initialized on first access.")
            except Exception as e:
                print(f"❌ CRITICAL: Could not initialize OpenAI client: {e}")
        else:
            print("⚠️ OPENAI_API_KEY not found. OpenAI client will not be available.")
    return _openai_client_instance

# Remove initialize_ai_models as models are now initialized lazily
# def initialize_ai_models():
#     print("AI models will be initialized on first access.")
