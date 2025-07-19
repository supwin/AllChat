# app/dependencies.py
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from .services.firebase_utils import db, firebase_auth

# สมมติว่า Token ถูกส่งมาใน Header ชื่อ 'Authorization'
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_user(token: str = Security(api_key_header)):
    """
    ตรวจสอบ ID Token ที่ส่งมาจาก Frontend และคืนข้อมูล user
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")
    try:
        # โดยปกติ Token จะมี "Bearer " นำหน้า
        if "Bearer " in token:
            token = token.split("Bearer ")[1]
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid authentication credentials: {e}")

async def get_user_tenant_role(tenant_id: str, current_user: dict = Depends(get_current_user)) -> str:
    """
    ตรวจสอบว่าผู้ใช้ปัจจุบันเป็นสมาชิกของ Tenant ที่ระบุหรือไม่ และคืนค่า Role
    """
    try:
        uid = current_user["uid"]
        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found.")
        
        user_data = user_doc.to_dict()
        tenant_roles = user_data.get("tenants", {})
        
        role = tenant_roles.get(tenant_id)
        
        if not role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have access to this tenant.")
            
        return role
    except HTTPException as e:
        raise e # ส่งต่อ HTTP Exception ที่เกิดขึ้น
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))