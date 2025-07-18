# app/routers/webhook.py
# ✨ ลบ import requests ที่ไม่จำเป็นแล้ว
from fastapi import APIRouter, Request, HTTPException, status
from ..services.firebase_utils import db
from ..services.chatbot_logic import get_bot_response
# ✨ 1. Import ฟังก์ชันที่จำเป็นทั้งหมด
from ..services.facebook_api import send_facebook_message, get_facebook_user_profile
from ..services.line_api import get_line_user_profile, send_line_message
import datetime

router = APIRouter(
    prefix="/webhook",
    tags=["Webhooks"],
)

@router.post("/line/{tenant_id}")
async def line_webhook(tenant_id: str, request: Request):
    body = await request.json()
    events = body.get("events", [])
    
    tenant_ref = db.collection('tenants').document(tenant_id)
    tenant_data = tenant_ref.get().to_dict()
    line_token = tenant_data.get('lineAccessToken')

    if not line_token:
        print(f"❌ Missing LINE Access Token for tenant: {tenant_id}")
        return {"status": "error", "message": "Missing token"}

    for event in events:
        try:
            if event.get("type") != "message" or event.get("message", {}).get("type") != "text":
                continue

            user_id = event["source"]["userId"]
            
            # ดึงข้อมูลโปรไฟล์จาก LINE
            profile_data = get_line_user_profile(user_id, line_token)
            display_name = profile_data.get("displayName", "Unknown User")
            picture_url = profile_data.get("pictureUrl", None)

            # บันทึก/อัปเดตข้อมูลโปรไฟล์ลง Firestore
            user_doc_ref = db.collection('chat_sessions').document(tenant_id).collection('users').document(user_id)
            user_doc_ref.set({
                'displayName': display_name,
                'pictureUrl': picture_url,
                'platform': 'line'
            }, merge=True)

            user_msg = event["message"]["text"]
            reply_token = event["replyToken"]
            current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

            reply_msg = get_bot_response(tenant_id, user_id, user_msg, platform="line", display_name=display_name, last_message_time=current_time)
            
            # ✨ 2. เปลี่ยนมาเรียกใช้ฟังก์ชัน send_line_message
            # เพื่อให้โค้ดมีรูปแบบเดียวกับ Facebook
            if reply_msg:
                send_line_message(reply_token, reply_msg, line_token)

        except Exception as e:
            print(f"❌ Error processing a LINE event for tenant {tenant_id}: {e}")
            continue
    
    return {"status": "ok"}


@router.post("/facebook/{tenant_id}")
async def facebook_webhook_handler(tenant_id: str, request: Request):
    data = await request.json()
    
    tenant_ref = db.collection('tenants').document(tenant_id)
    config = tenant_ref.get().to_dict()
    page_token = config.get('facebookPageToken')

    if not page_token:
        print(f"❌ Missing Facebook Page Token for tenant: {tenant_id}")
        return "EVENT_RECEIVED"

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text")

                    # ดึงข้อมูลโปรไฟล์จาก Facebook
                    profile_data = get_facebook_user_profile(sender_id, page_token)
                    display_name = profile_data.get("name", "Unknown User")
                    picture_url = profile_data.get("profile_pic", None)

                    # บันทึก/อัปเดตข้อมูลโปรไฟล์ลง Firestore
                    user_doc_ref = db.collection('chat_sessions').document(tenant_id).collection('users').document(sender_id)
                    user_doc_ref.set({
                        'displayName': display_name,
                        'pictureUrl': picture_url,
                        'platform': 'facebook'
                    }, merge=True)

                    current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

                    if message_text:
                        reply_text = get_bot_response(tenant_id, sender_id, message_text, platform="facebook", display_name=display_name, last_message_time=current_time)
                        if reply_text:
                            send_facebook_message(sender_id, reply_text, page_token)
                        
    return "EVENT_RECEIVED"

# ✨ อย่าลืมเพิ่มฟังก์ชัน GET สำหรับ Facebook Webhook Verification ด้วย
@router.get("/facebook/{tenant_id}")
async def facebook_webhook_verify(tenant_id: str, request: Request):
    """
    Handles Facebook webhook verification (GET request).
    """
    if 'hub.mode' in request.query_params and 'hub.challenge' in request.query_params and 'hub.verify_token' in request.query_params:
        if not db:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not available.")
        
        tenant_ref = db.collection('tenants').document(tenant_id)
        config = tenant_ref.get().to_dict()
        verify_token_from_db = config.get('facebookVerifyToken')
        
        if request.query_params.get('hub.mode') == 'subscribe' and request.query_params.get('hub.verify_token') == verify_token_from_db:
            print(f"✅ Facebook webhook verified for tenant: {tenant_id}")
            # Facebook expects an integer response for the challenge
            return int(request.query_params.get('hub.challenge'))
    
    print(f"❌ Facebook webhook verification failed for tenant: {tenant_id}")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch.")
