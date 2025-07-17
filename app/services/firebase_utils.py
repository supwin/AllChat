# app/services/firebase_utils.py
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
from typing import Optional

# Global Firebase instances
_db = None
_auth = None

def _initialize_firebase_once():
    """
    Internal function to initialize Firebase Admin SDK only once.
    This function is called immediately when the module is loaded.
    """
    global _db, _auth
    # Check if a Firebase app is already initialized to prevent re-initialization errors
    if firebase_admin._apps:
        _db = firestore.client()
        _auth = firebase_auth
        print("✅ Firebase Admin SDK already initialized.")
        return

    try:
        # Construct the path to the service account key file
        # Assumes serviceAccountKey.json is in the project root (one level up from 'app' folder)
        cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "serviceAccountKey.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        _auth = firebase_auth
        print("✅ Firebase Admin SDK connection successful.")
    except Exception as e:
        _db = None
        _auth = None
        print(f"❌ CRITICAL: Could not connect to Firebase Admin SDK: {e}")

# Call initialization immediately when this module is imported
_initialize_firebase_once()

# Expose the initialized objects for other modules to import
db = _db
auth = _auth

# --- Functions for updating tenant data in Firestore ---
# These functions are called by the AI assistants (Settings Assistant, Wizard)

def update_bot_persona(tenant_id: str, persona: str) -> str:
    """Updates the bot's persona (role and personality) for a given tenant."""
    if not db: return "Error: Database not available."
    try:
        db.collection('tenants').document(tenant_id).set({'botPersona': persona}, merge=True)
        return f"Bot persona for tenant '{tenant_id}' has been updated successfully."
    except Exception as e: return f"Error updating persona: {e}"

def update_knowledge_base(tenant_id: str, knowledge: str) -> str:
    """Updates the knowledge base for a given tenant's bot."""
    if not db: return "Error: Database not available."
    try:
        db.collection('tenants').document(tenant_id).set({'knowledgeBase': knowledge}, merge=True)
        return f"Knowledge base for tenant '{tenant_id}' has been updated successfully."
    except Exception as e: return f"Error updating knowledge base: {e}"

def update_line_token(tenant_id: str, token: str) -> str:
    """Updates the LINE Channel Access Token for a given tenant."""
    if not db: return "Error: Database not available."
    try:
        db.collection('tenants').document(tenant_id).set({'lineAccessToken': token}, merge=True)
        return f"LINE token for tenant '{tenant_id}' has been updated successfully."
    except Exception as e: return f"Error updating LINE token: {e}"

def update_business_type(tenant_id: str, business_type: str) -> str:
    """Updates the business type for a given tenant."""
    if not db: return "Error: Database not available."
    try:
        db.collection('tenants').document(tenant_id).set({'businessType': business_type}, merge=True)
        return f"Business type for tenant '{tenant_id}' has been updated to '{business_type}' successfully."
    except Exception as e: return f"Error updating business type: {e}"

def update_product_recommendation_setting(tenant_id: str, enabled: bool) -> str:
    """Enables or disables the product recommendation feature for a product-based business."""
    if not db: return "Error: Database not available."
    try:
        db.collection('tenants').document(tenant_id).set({'productRecommendationEnabled': enabled}, merge=True)
        status = "enabled" if enabled else "disabled"
        return f"Product recommendation for tenant '{tenant_id}' has been {status} successfully."
    except Exception as e: return f"Error updating product recommendation setting: {e}"

def update_booking_settings(tenant_id: str, integration_url: Optional[str] = None, bot_enabled: Optional[bool] = None) -> str:
    """Updates booking system integration URL and/or bot booking enablement for service appointment businesses."""
    if not db: return "Error: Database not available."
    try:
        update_data = {}
        if integration_url is not None: update_data['bookingSystemIntegration'] = integration_url
        if bot_enabled is not None: update_data['botBookingEnabled'] = bot_enabled
        if update_data:
            db.collection('tenants').document(tenant_id).set(update_data, merge=True)
            return f"Booking settings for tenant '{tenant_id}' updated successfully."
        return "No booking settings provided for update."
    except Exception as e: return f"Error updating booking settings: {e}"

def update_project_status_setting(tenant_id: str, enabled: bool) -> str:
    """Enables or disables project status update feature for project-based businesses."""
    if not db: return "Error: Database not available."
    try:
        db.collection('tenants').document(tenant_id).set({'projectStatusUpdateEnabled': enabled}, merge=True)
        status = "enabled" if enabled else "disabled"
        return f"Project status update for tenant '{tenant_id}' has been {status} successfully."
    except Exception as e: return f"Error updating project status setting: {e}"

def update_chatbot_general_settings(tenant_id: str, name: Optional[str] = None, welcome_message: Optional[str] = None) -> str:
    """Updates general chatbot settings like name and welcome message."""
    if not db: return "Error: Database not available."
    try:
        update_data = {}
        if name is not None: update_data['chatbotName'] = name
        if welcome_message is not None: update_data['welcomeMessage'] = welcome_message
        if update_data:
            db.collection('tenants').document(tenant_id).set(update_data, merge=True)
            return f"Chatbot general settings for tenant '{tenant_id}' updated successfully."
        return "No general chatbot settings provided for update."
    except Exception as e: return f"Error updating chatbot general settings: {e}"
