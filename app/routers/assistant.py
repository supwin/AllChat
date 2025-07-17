# app/routers/assistant.py
import os
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
from google.generativeai.types import content_types

from ..config.settings import get_gemini_wizard_model # <--- CHANGED IMPORT
from ..prompts.settings_assistant_prompt import SETTINGS_ASSISTANT_PROMPT
from ..prompts.wizard_prompt import WIZARD_PROMPT
from ..services.firebase_utils import (
    update_bot_persona, update_knowledge_base, update_line_token,
    update_business_type, update_product_recommendation_setting,
    update_booking_settings, update_project_status_setting,
    update_chatbot_general_settings
)

# Create an API router specific for AI assistants
router = APIRouter(
    tags=["AI Assistants"],
)

# In-memory storage for assistant chat sessions (for simplicity)
settings_assistant_sessions = {}
wizard_chat_sessions = {}

class AssistantRequest(BaseModel):
    message: str

@router.post("/api/settings_assistant/{tenant_id}")
async def handle_settings_assistant(tenant_id: str, request: AssistantRequest):
    """
    Handles conversational updates to tenant settings via the Settings Assistant.
    """
    wizard_model = get_gemini_wizard_model() # <--- GET MODEL INSTANCE HERE
    if not wizard_model:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Assistant model is not available.")
    
    # Manage conversation history
    if tenant_id not in settings_assistant_sessions:
        settings_assistant_sessions[tenant_id] = wizard_model.start_chat(history=[
            {'role': 'user', 'parts': [{'text': SETTINGS_ASSISTANT_PROMPT}]},
            {'role': 'model', 'parts': [{'text': "สวัสดีครับ ผมคือผู้ช่วยจัดการ มีอะไรให้ผมช่วยอัปเดตการตั้งค่าบอทของคุณไหมครับ?"}]}
        ])
    
    chat = settings_assistant_sessions[tenant_id]
    
    # Send message to AI and handle Function Calling
    response = chat.send_message(request.message)
    
    if response.candidates and response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        function_name = function_call.name
        args = function_call.args
        
        print(f"🛠️ Settings Assistant wants to call function: {function_name} with args: {args}")

        result = "Unknown function" # Default result

        # Call the appropriate function based on AI's request
        if function_name == "update_bot_persona":
            result = update_bot_persona(tenant_id, args['persona'])
        elif function_name == "update_knowledge_base":
            result = update_knowledge_base(tenant_id, args['knowledge'])
        elif function_name == "update_line_token":
            result = update_line_token(tenant_id, args['token'])
        elif function_name == "update_business_type":
            result = update_business_type(tenant_id, args['business_type'])
        elif function_name == "update_product_recommendation_setting":
            result = update_product_recommendation_setting(tenant_id, args['enabled'])
        elif function_name == "update_booking_settings":
            result = update_booking_settings(
                tenant_id,
                integration_url=args.get('integration_url'),
                bot_enabled=args.get('bot_enabled')
            )
        elif function_name == "update_project_status_setting":
            result = update_project_status_setting(tenant_id, args['enabled'])
        elif function_name == "update_chatbot_general_settings":
            result = update_chatbot_general_settings(
                tenant_id,
                name=args.get('name'),
                welcome_message=args.get('welcome_message')
            )
        else:
            result = "Unknown function"
            
        # Send the function result back to AI to generate final response
        response = chat.send_message(
            content_types.to_content(
                content_types.FunctionResponse(name=function_name, response={'result': result})
            )
        )

    return {"reply": response.text}

@router.post("/wizard/{tenant_id}")
async def wizard_chatbot(tenant_id: str, request: Request):
    """
    Handles conversational setup via the Setup Wizard.
    """
    wizard_model = get_gemini_wizard_model() # <--- GET MODEL INSTANCE HERE
    if not wizard_model:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Wizard model is not available.")
    
    body = await request.json()
    user_input = body.get("message")
    
    # Manage conversation history
    if tenant_id not in wizard_chat_sessions:
        wizard_chat_sessions[tenant_id] = wizard_model.start_chat(history=[
            {'role': 'user', 'parts': [{'text': WIZARD_PROMPT}]},
            {'role': 'model', 'parts': [{'text': "สวัสดีครับ ผมคือผู้ช่วยตั้งค่าอัจฉริยะ ยินดีที่ได้ช่วยเหลือคุณสร้างแชทบอทครับ! ก่อนอื่น บอทของคุณลูกค้าจะให้ชื่อว่าอะไรดีครับ?"}]}
        ])
    
    chat = wizard_chat_sessions[tenant_id]
    response = chat.send_message(user_input)
    
    if response.candidates and response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        function_name = function_call.name
        args = function_call.args
        print(f"🪄 Wizard wants to call function: {function_name} with args: {args}")
        
        result = "Unknown function" # Default result
        # Call the appropriate function
        if function_name == "update_bot_persona":
            result = update_bot_persona(tenant_id, args['persona'])
        elif function_name == "update_knowledge_base":
            result = update_knowledge_base(tenant_id, args['knowledge'])
        elif function_name == "update_line_token":
            result = update_line_token(tenant_id, args['token'])
        # Add new function calls for wizard if needed, but for now, settings assistant handles specific settings
        else:
            result = "Unknown function"
            
        response = chat.send_message(content_types.to_content(content_types.FunctionResponse(name=function_name, response={'result': result})))
    return {"reply": response.text}
