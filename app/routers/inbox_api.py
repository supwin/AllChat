# app/routers/inbox_api.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from ..services.firebase_utils import db
from ..services.line_api import push_line_message
import datetime

router = APIRouter(
    prefix="/api/inbox",
    tags=["Inbox API"],
)

@router.post("/{tenant_id}/{user_id}/mark-as-read")
async def mark_chat_as_read(tenant_id: str, user_id: str):
    """
    อัปเดตเวลาล่าสุดที่แอดมินเปิดอ่านแชทของผู้ใช้คนนี้
    """
    try:
        user_doc_ref = db.collection('chat_sessions').document(tenant_id).collection('users').document(user_id)
        
        # อัปเดตฟิลด์ admin_last_seen_timestamp เป็นเวลาปัจจุบัน
        user_doc_ref.update({
            'admin_last_seen_timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
        return {"status": "ok", "message": f"Chat for {user_id} marked as read."}
    except Exception as e:
        print(f"❌ Error marking chat as read for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AdminMessageRequest(BaseModel):
    message: str

@router.post("/{tenant_id}/{user_id}/send-admin-message")
async def send_admin_message(tenant_id: str, user_id: str, request: AdminMessageRequest):
    """
    รับข้อความจากแอดมินและส่งออกไปหาผู้ใช้ผ่าน Platform ที่เหมาะสม
    """
    try:
        # 1. ดึงข้อมูลผู้ใช้เพื่อหา Platform และ Token
        tenant_doc = db.collection('tenants').document(tenant_id).get()
        user_doc = db.collection('chat_sessions').document(tenant_id).collection('users').document(user_id).get()

        if not tenant_doc.exists or not user_doc.exists:
            raise HTTPException(status_code=404, detail="Tenant or User not found")

        tenant_data = tenant_doc.to_dict()
        user_data = user_doc.to_dict()

        platform = user_data.get('platform')
        message_to_send = request.message

        # ✨ NEW: ดึงข้อมูลแอดมินที่กำลังส่งข้อความ
        admin_uid = current_user.get("uid")
        admin_user_doc = db.collection('users').document(admin_uid).get()
        admin_display_name = admin_user_doc.to_dict().get("displayName", "Admin") if admin_user_doc.exists else "Admin"

        # 2. ตรวจสอบ Platform และส่งข้อความ
        if platform == 'line':
            line_token = tenant_data.get('lineAccessToken')
            if not line_token:
                raise HTTPException(status_code=500, detail="LINE Access Token not configured for this tenant.")
            
            result = push_line_message(user_id, message_to_send, line_token)
            if result.get("status") != "ok":
                raise HTTPException(status_code=500, detail=f"Failed to send LINE message: {result.get('message')}")

        # (ในอนาคตสามารถเพิ่มเงื่อนไขสำหรับ Facebook ที่นี่)
        # elif platform == 'facebook':
        #     ...

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

        # ✨ NEW: 3. สร้างและบันทึกข้อความของแอดมินลงใน history
        admin_message_for_history = {
            "role": "model", # ยังคงใช้ role 'model' เพื่อให้แสดงผลฝั่งขวา
            "parts": [{"text": message_to_send}],
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "sender_type": "admin", # ระบุว่าเป็นแอดมิน
            "sender_id": admin_uid,
            "sender_name": admin_display_name
        }
        
        # ใช้ ArrayUnion เพื่อเพิ่มข้อความใหม่เข้าไปใน array ของ history
        user_chat_doc_ref.update({
            "history": firestore.ArrayUnion([admin_message_for_history])
        })

        return {"status": "ok", "message": f"Message sent to {user_id} via {platform}."}

    except Exception as e:
        print(f"❌ Error sending admin message to {user_id}: {e}")
        # แปลง HTTPException เป็น dict ก่อนส่งกลับ
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))        