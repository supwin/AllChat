# app/routers/tenant.py
from fastapi import APIRouter, HTTPException, status, Depends
from ..models.schemas import TenantUpdateRequest # สมมติว่าคุณมี schema นี้
from typing import Optional
from ..services.firebase_utils import db
from ..dependencies import get_user_tenant_role # ✨ Import dependency

# Create an API router specific for tenant management
router = APIRouter(
    prefix="/api/tenant",
    tags=["Tenant Management"],
)

@router.get("/{tenant_id}")
async def get_tenant_data(tenant_id: str, role: str = Depends(get_user_tenant_role)):

    """
    Retrieves the configuration data for a specific tenant.
    """
    # if not db:
    #     raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not available.")
    try:
        doc_ref = db.collection('tenants').document(tenant_id)
        doc = doc_ref.get() # .get() is synchronous
        if not doc.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{tenant_id}")
async def update_tenant_data(tenant_id: str, data: TenantUpdateRequest, role: str = Depends(get_user_tenant_role)):
      
    if role != 'owner':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can update tenant settings.")

    try:
        update_data = data.dict(exclude_none=True)
        doc_ref = db.collection('tenants').document(tenant_id)
        doc_ref.update(update_data)
        return {"message": "Tenant data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
