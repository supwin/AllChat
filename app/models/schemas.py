# app/routers/tenant.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..services.firebase_utils import db
# from ..routers.auth import get_current_user

router = APIRouter(
    prefix="/api/tenant",
    tags=["Tenant"],
    # dependencies=[Depends(get_current_user)]
)

class TenantSettings(BaseModel):
    tenantName: str
    businessType: str
    # Add other fields from your settings form as needed
    botPersona: str = ""
    knowledgeBase: str = ""
    lineAccessToken: str = ""
    facebookPageToken: str = ""
    facebookVerifyToken: str = ""
    # ... any other settings fields

# # --- ✨ REVISED create_tenant function ---
# @router.post("/")
# async def create_tenant(settings: TenantSettings, current_user: dict = Depends(get_current_user)):
#     """
#     Creates a new tenant (shop), sets the creator as the owner,
#     and updates the user's profile with the new tenant info.
#     """
#     try:
#         uid = current_user["uid"]
        
#         # 1. Create the new tenant document
#         new_tenant_ref = db.collection('tenants').document()
#         tenant_id = new_tenant_ref.id
        
#         tenant_data = settings.dict()
#         tenant_data["owner_uid"] = uid
#         tenant_data["members"] = {
#             uid: "owner" # The creator is the owner
#         }
        
#         new_tenant_ref.set(tenant_data)

#         # 2. Update the user's document to add this new tenant
#         user_ref = db.collection('users').document(uid)
#         user_ref.update({
#             f'tenants.{tenant_id}': 'owner'
#         })

#         return {"tenant_id": tenant_id, "message": "Tenant created successfully"}
#     except Exception as e:
#         print(f"❌ Error creating tenant: {e}")
#         raise HTTPException(status_code=500, detail="Failed to create tenant.")

# --- The rest of the file needs authorization checks, which we will add later ---
# For now, get_tenant and update_tenant remain the same but will need updating.

@router.get("/{tenant_id}")
async def get_tenant(tenant_id: str, current_user: dict = Depends(get_current_user)):
    # WARNING: This needs a proper authorization check later
    try:
        tenant_doc = db.collection('tenants').document(tenant_id).get()
        if not tenant_doc.exists:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return tenant_doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tenant_id}")
async def update_tenant(tenant_id: str, settings: TenantSettings, current_user: dict = Depends(get_current_user)):
    # WARNING: This needs a proper authorization check later
    try:
        tenant_ref = db.collection('tenants').document(tenant_id)
        tenant_ref.update(settings.dict(exclude_unset=True))
        return {"message": "Tenant updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
