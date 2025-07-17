# app/routers/auth.py
from fastapi import APIRouter, HTTPException, status
from typing import Optional
from ..models.schemas import AuthRequest, SocialLoginRequest
from ..services.firebase_utils import db, firebase_auth, firestore

# Create an API router specific for authentication
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

@router.post("/register")
async def register_user(request: AuthRequest):
    """
    Registers a new user in Firebase Authentication and creates a linked tenant document.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not available.")
    try:
        # 1. Create user in Firebase Authentication
        user = firebase_auth.create_user(
            email=request.email,
            password=request.password
        )
        print(f"✅ Firebase Auth User created: {user.uid}")

        # 2. Create a new tenant document and link it to the user
        tenant_doc_ref = db.collection('tenants').document()  # Let Firestore generate ID
        new_tenant_id = tenant_doc_ref.id
        
        tenant_data = {
            'createdAt': firestore.SERVER_TIMESTAMP,
            'status': 'active',  # Set to active upon registration
            'owner_uid': user.uid,  # Link tenant to this user
            'email': request.email,  # Store email for reference
            'businessType': request.businessType  # Initial business type from registration
        }
        # Note: .set() is synchronous for the Python Admin SDK
        tenant_doc_ref.set(tenant_data, merge=True)
        print(f"✅ New tenant '{new_tenant_id}' created and linked to user '{user.uid}'.")

        # 3. Generate a Custom Token for the user to login on the client-side
        custom_token = firebase_auth.create_custom_token(user.uid)
        return {"custom_token": custom_token.decode('utf-8'), "uid": user.uid, "tenant_id": new_tenant_id}

    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")
    except Exception as e:
        print(f"❌ Registration error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {e}")

@router.post("/login")
async def login_user(request: AuthRequest):
    """
    Logs in a user by verifying credentials and providing a Firebase Custom Token.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not available.")
    try:
        # In a production scenario, you would NOT pass password from frontend to backend for validation.
        # Instead, the frontend Firebase SDK would handle email/password sign-in,
        # get an ID token, and send that ID token to your backend for verification.
        # For simplicity in this example, we're assuming the user exists and we fetch their UID by email.
        # The client-side will then use the custom_token to sign in.

        user = firebase_auth.get_user_by_email(request.email)
        
        # Find the tenant_id associated with this user
        tenant_query = db.collection('tenants').where('owner_uid', '==', user.uid).limit(1).get()
        tenant_id = None
        for doc in tenant_query:
            tenant_id = doc.id
            break

        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found for this user.")

        # Generate a Custom Token for the user to login on the client-side
        custom_token = firebase_auth.create_custom_token(user.uid)
        return {"custom_token": custom_token.decode('utf-8'), "uid": user.uid, "tenant_id": tenant_id}

    except firebase_auth.UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login failed: {e}")


@router.post("/social-login")
async def social_login(request: SocialLoginRequest):
    """
    Handles user registration/login from social providers.
    If user exists, log them in. If not, create a new user and tenant.
    """
    try:
        # 1. ตรวจสอบว่ามี tenant ที่ผูกกับ UID นี้อยู่แล้วหรือยัง
        tenant_query = db.collection('tenants').where('owner_uid', '==', request.uid).limit(1).get()

        tenant_id = None
        for doc in tenant_query:
            tenant_id = doc.id
            break

        # 2. ถ้ามี tenant อยู่แล้ว (เคยล็อกอินแล้ว) ให้จบการทำงานและส่ง tenant_id กลับไป
        if tenant_id:
            print(f"✅ Existing social user '{request.email}' logged in. Tenant: {tenant_id}")
            return {"tenant_id": tenant_id}

        # 3. ถ้ายังไม่มี ให้สร้าง tenant ใหม่ (เป็นการลงทะเบียนครั้งแรก)
        print(f"✨ New social user '{request.email}'. Creating new tenant...")
        tenant_doc_ref = db.collection('tenants').document()
        new_tenant_id = tenant_doc_ref.id

        tenant_data = {
            'createdAt': firestore.SERVER_TIMESTAMP,
            'status': 'active',
            'owner_uid': request.uid, # ใช้ UID ที่ได้จาก Social Provider
            'email': request.email,
            'tenantName': request.displayName, # ใช้ชื่อจาก Social Provider เป็นค่าเริ่มต้น
            'loginProvider': request.providerId # เก็บข้อมูลว่าล็อกอินมาจากไหน (e.g., 'google.com')
        }
        tenant_doc_ref.set(tenant_data)
        print(f"✅ New tenant '{new_tenant_id}' created for user '{request.uid}'.")

        return {"tenant_id": new_tenant_id}

    except Exception as e:
        print(f"❌ Social Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during social login: {e}"
        )