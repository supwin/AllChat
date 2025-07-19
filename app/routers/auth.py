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
        tenant_doc_ref = db.collection('tenants').document()
        new_tenant_id = tenant_doc_ref.id
        
        tenant_data = {
            'createdAt': firestore.SERVER_TIMESTAMP,
            'status': 'active',
            'owner_uid': user.uid,
            'email': request.email,
            'businessType': request.businessType,
            'members': {
                user.uid: 'owner'
            }
        }
        tenant_doc_ref.set(tenant_data)
        print(f"✅ New tenant '{new_tenant_id}' created and linked to user '{user.uid}'.")

        # 2.5 Create a user profile document in 'users' collection
        user_doc_ref = db.collection('users').document(user.uid)
        user_doc_ref.set({
            'uid': user.uid,
            'email': request.email,
            'displayName': request.email,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'tenants': {
                new_tenant_id: 'owner'
            }
        })
        print(f"✅ New user profile created for '{user.uid}'.")

        # 3. Generate a Custom Token for the user to login on the client-side
        custom_token = firebase_auth.create_custom_token(user.uid)
        return {"custom_token": custom_token.decode('utf-8'), "uid": user.uid, "tenant_id": new_tenant_id}

    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")
    except Exception as e:
        print(f"❌ Registration error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {e}")

# --- ✨ REVISED login_user function ---
@router.post("/login")
async def login_user(request: AuthRequest):
    """
    (แก้ไขใหม่) ตรวจสอบผู้ใช้และสร้าง Custom Token สำหรับให้ Frontend นำไปเข้าระบบ
    ฟังก์ชันนี้จะไม่ตรวจสอบรหัสผ่านโดยตรง แต่จะสร้าง Token ให้ Frontend
    ที่ทำการ signInWithEmailAndPassword สำเร็จแล้วนำไปใช้ต่อ
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not available.")
    try:
        # Backend จะไม่ตรวจสอบรหัสผ่าน
        # แต่จะหาผู้ใช้จาก Email เพื่อสร้าง Token ให้
        user = firebase_auth.get_user_by_email(request.email)
        
        # สร้าง Custom Token เพื่อส่งกลับให้ Frontend
        custom_token = firebase_auth.create_custom_token(user.uid)
        
        # ไม่ต้องส่ง tenant_id กลับไปแล้ว เพราะจะไปเลือกที่หน้า tenant-selector
        return {"custom_token": custom_token.decode('utf-8'), "uid": user.uid}

    except firebase_auth.UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    except Exception as e:
        # แก้ไขการแสดงผล Error ให้ชัดเจนขึ้น
        print(f"❌ Login error: {type(e).__name__} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login failed: {e}")


@router.post("/social-login")
async def social_login(request: SocialLoginRequest):
    """
    Handles user registration/login from social providers.
    """
    try:
        uid = request.uid
        email = request.email
        display_name = request.displayName

        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if user_doc.exists:
            print(f"✅ Existing social user '{email}' logged in.")
            return {"message": "Existing user logged in.", "uid": uid, "is_new_user": False}
        else:
            print(f"✨ New social user '{email}'. Creating new user profile and tenant...")
            
            tenant_doc_ref = db.collection('tenants').document()
            new_tenant_id = tenant_doc_ref.id
            tenant_data = {
                'createdAt': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'owner_uid': uid,
                'email': email,
                'tenantName': f"{display_name}'s Shop",
                'members': { uid: 'owner' }
            }
            tenant_doc_ref.set(tenant_data)

            user_ref.set({
                'uid': uid,
                'email': email,
                'displayName': display_name,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'tenants': { new_tenant_id: 'owner' }
            })

            return {
                "message": "New user and tenant created successfully.",
                "uid": uid,
                "is_new_user": True,
                "new_tenant_id": new_tenant_id
            }

    except Exception as e:
        print(f"❌ Social Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during social login: {e}"
        )
