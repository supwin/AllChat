# app/routers/inbox.py
from fastapi import APIRouter, HTTPException
from ..services.firebase_utils import db

# สร้าง Router สำหรับจัดการ API ที่เกี่ยวกับ Inbox
router = APIRouter(
    prefix="/api",  # กำหนดให้ URL ขึ้นต้นด้วย /api
    tags=["Inbox"], # จัดกลุ่มในหน้าเอกสาร API (Swagger UI)
)

@router.get("/chat_users/{tenant_id}")
async def get_chat_users(tenant_id: str):
    """
    ดึงรายชื่อผู้ใช้ทั้งหมดที่มี session การแชทสำหรับ tenant ที่ระบุ
    Endpoint นี้จะถูกเรียกใช้โดยหน้า inbox.html
    """
    try:
        # เข้าถึง collection ของ user ภายใต้ tenant ที่ระบุ
        users_ref = db.collection('chat_sessions').document(tenant_id).collection('users')
        users_docs = users_ref.stream()
        
        users_list = []
        for doc in users_docs:
            user_data = doc.to_dict()
            # เพิ่ม user_id (ซึ่งก็คือ document ID) เข้าไปในข้อมูลที่จะส่งกลับ
            user_data['user_id'] = doc.id
            users_list.append(user_data)
            
        return users_list
    except Exception as e:
        print(f"❌ Error fetching chat users for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while fetching user list.")

