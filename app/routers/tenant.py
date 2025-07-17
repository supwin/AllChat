# app/routers/tenant.py
from fastapi import APIRouter, HTTPException, status
from typing import Optional
from ..models.schemas import TenantUpdateRequest
from ..services.firebase_utils import db, firestore

# Create an API router specific for tenant management
router = APIRouter(
    prefix="/api/tenant",
    tags=["Tenant Management"],
)

@router.get("/{tenant_id}")
async def get_tenant_data(tenant_id: str):
    """
    Retrieves the configuration data for a specific tenant.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not available.")
    try:
        doc_ref = db.collection('tenants').document(tenant_id)
        doc = doc_ref.get() # .get() is synchronous
        if not doc.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{tenant_id}")
async def update_tenant_data(tenant_id: str, data: TenantUpdateRequest):
    """
    Updates the configuration data for a specific tenant.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not available.")
    try:
        update_data = data.dict(exclude_none=True)
        if not update_data:
            return {"message": "No data to update."}
        doc_ref = db.collection('tenants').document(tenant_id)
        doc_ref.set(update_data, merge=True) # .set() is synchronous
        return {"message": "Tenant data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
