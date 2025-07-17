# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Schema for authentication requests (login and register)
class AuthRequest(BaseModel):
    email: str
    password: str
    businessType: Optional[str] = None  # Only for registration

# Schema for updating tenant data
class TenantUpdateRequest(BaseModel):
    botPersona: Optional[str] = None
    knowledgeBase: Optional[str] = None
    lineAccessToken: Optional[str] = None
    facebookPageToken: Optional[str] = None
    facebookVerifyToken: Optional[str] = None
    businessType: Optional[str] = None
    productRecommendationEnabled: Optional[bool] = None
    bookingSystemIntegration: Optional[str] = None
    botBookingEnabled: Optional[bool] = None
    projectStatusUpdateEnabled: Optional[bool] = None
    chatbotName: Optional[str] = None
    welcomeMessage: Optional[str] = None
    owner_uid: Optional[str] = None

    # --- ✨ NEW: Add the missing behavioral toggle fields ---
    is_detailed_response: Optional[bool] = None
    is_sweet_tone: Optional[bool] = None
    show_empathy: Optional[bool] = None
    high_sales_drive: Optional[bool] = None

# Schema for assistant requests (settings assistant, wizard)
class AssistantRequest(BaseModel):
    message: str

# Schema for chat widget requests
class ChatWidgetRequest(BaseModel):
    user_id: str
    message: str

class SocialLoginRequest(BaseModel):
    uid: str
    email: str
    displayName: Optional[str] = None
    providerId: str