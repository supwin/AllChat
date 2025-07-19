# app/routers/inbox_api.py

# ✨ 1. แก้ไขบรรทัดนี้: เพิ่ม Depends เข้าไปใน import
from fastapi import APIRouter, HTTPException, Depends, Body 
from firebase_admin import firestore
import datetime

from ..services.firebase_utils import db
from ..services.line_api import push_line_message
# ✨ ตรวจสอบให้แน่ใจว่าได้ import dependencies ที่สร้างไว้ครบถ้วน
from ..dependencies import get_current_user, get_user_tenant_role

router = APIRouter(
    prefix="/api/inbox",
    tags=["Inbox API"],
)

@router.post("/{tenant_id}/{user_id}/mark-as-read")
async def mark_chat_as_read(
    tenant_id: str, 
    user_id: str,
    # ✨ 2. เพิ่ม Dependency เพื่อตรวจสอบสิทธิ์การเข้าถึง Tenant
    role: str = Depends(get_user_tenant_role)
):
    """
    อัปเดตเวลาล่าสุดที่แอดมินเปิดอ่านแชทของผู้ใช้คนนี้
    """
    try:
        user_doc_ref = db.collection('chat_sessions').document(tenant_id).collection('users').document(user_id)
        user_doc_ref.update({
            'admin_last_seen_timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
        return {"status": "ok", "message": f"Chat for {user_id} marked as read."}
    
        user_doc_ref = db.collection('chat_sessions').document(tenant_id).collection('users').document(user_id)
        
        # อัปเดตฟิลด์ admin_last_seen_timestamp เป็นเวลาปัจจุบัน
    except Exception as e:
        print(f"❌ Error marking chat as read for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tenant_id}/{user_id}/send-admin-message")
async def send_admin_message(
    tenant_id: str, 
    user_id: str, 
    # ✨ 3. รับ message ตรงๆ และเพิ่ม Dependencies สำหรับตรวจสอบสิทธิ์และดึงข้อมูลผู้ใช้
    message: str = Body(..., embed=True),
    role: str = Depends(get_user_tenant_role),
    current_user: dict = Depends(get_current_user)
):
    """
    รับข้อความจากแอดมินและส่งออกไปหาผู้ใช้ผ่าน Platform ที่เหมาะสม
    """
    try:
        # 1. ดึงข้อมูลผู้ใช้เพื่อหา Platform และ Token
        tenant_doc_ref = db.collection('tenants').document(tenant_id)
        user_chat_doc_ref = db.collection('chat_sessions').document(tenant_id).collection('users').document(user_id) # ✨ แก้ไข: กำหนดตัวแปรนี้ไว้เลย
        
        tenant_doc = tenant_doc_ref.get()
        user_doc = user_chat_doc_ref.get()

        if not tenant_doc.exists() or not user_doc.exists():
            raise HTTPException(status_code=404, detail="Tenant or User chat session not found")

        tenant_data = tenant_doc.to_dict()
        user_data = user_doc.to_dict()
        platform = user_data.get('platform')

        # ✨ 4. ดึงข้อมูลแอดมินจาก current_user ที่ได้จาก Dependency
        admin_uid = current_user["uid"]
        # ไม่จำเป็นต้องดึงข้อมูลแอดมินซ้ำซ้อนจาก DB เพราะใน get_current_user เราอาจจะใส่ displayName ไว้แล้ว
        # หรือถ้าต้องการชื่อล่าสุด ก็ดึงแบบเดิมได้
        admin_display_name = current_user.get("name", "Admin") # สมมติว่าใน token มี 'name'

        # 2. ตรวจสอบ Platform และส่งข้อความ
        if platform == 'line':
            line_token = tenant_data.get('lineAccessToken')
            if not line_token:
                raise HTTPException(status_code=500, detail="LINE Access Token not configured for this tenant.")
            
            result = push_line_message(user_id, message, line_token)
            if result.get("status") != "ok":
                raise HTTPException(status_code=500, detail=f"Failed to send LINE message: {result.get('message')}")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

        # 3. สร้างและบันทึกข้อความของแอดมินลงใน history
        admin_message_for_history = {
            "role": "model",
            "parts": [{"text": message}],
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "sender_type": "admin",
            "sender_id": admin_uid,
            "sender_name": admin_display_name
        }
        
        # ✨ 5. ใช้ `user_chat_doc_ref` ที่เรากำหนดไว้ตอนแรก
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