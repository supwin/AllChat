# app/routers/user.py
from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_current_user
from ..services.firebase_utils import db

router = APIRouter(
    prefix="/api/user",
    tags=["User"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/me/tenants")
async def get_my_tenants(current_user: dict = Depends(get_current_user)):
    """
    Fetches the profile of the currently logged-in user and returns a list
    of tenants they have access to, along with their role in each.
    """
    try:
        uid = current_user["uid"]
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User profile not found.")

        user_data = user_doc.to_dict()
        tenant_roles = user_data.get("tenants", {})

        if not tenant_roles:
            return [] # Return an empty list if the user is not part of any tenant

        # Fetch details for each tenant
        tenants_details = []
        for tenant_id, role in tenant_roles.items():
            tenant_doc = db.collection('tenants').document(tenant_id).get()
            if tenant_doc.exists:
                tenant_data = tenant_doc.to_dict()
                tenants_details.append({
                    "tenant_id": tenant_id,
                    "tenantName": tenant_data.get("tenantName", "Untitled Shop"),
                    "role": role
                })
        
        return tenants_details
    except Exception as e:
        print(f"❌ Error fetching user tenants: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while fetching tenant data.")
