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
            'status': 'active',
            'owner_uid': user.uid,
            'email': request.email,
            'businessType': request.businessType,
            'members': { # ✨ NEW: Add members map with the creator as owner
                user.uid: 'owner'
            }
        }
        tenant_doc_ref.set(tenant_data)
        print(f"✅ New tenant '{new_tenant_id}' created and linked to user '{user.uid}'.")

        # ✨ NEW: 2.5 Create a user profile document in 'users' collection
        user_doc_ref = db.collection('users').document(user.uid)
        user_doc_ref.set({
            'uid': user.uid,
            'email': request.email,
            'displayName': request.email, # Use email as initial display name
            'createdAt': firestore.SERVER_TIMESTAMP,
            'tenants': {
                new_tenant_id: 'owner' # Add the new tenant with 'owner' role
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
        uid = request.uid
        email = request.email
        display_name = request.displayName

        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        # 1. ตรวจสอบว่ามี tenant ที่ผูกกับ UID นี้อยู่แล้วหรือยัง
        if user_doc.exists:
            print(f"✅ Existing social user '{email}' logged in.")
            # The frontend will then call another endpoint to get the list of tenants
            return {"message": "Existing user logged in.", "uid": uid, "is_new_user": False}

        # Case 2: New User
        else:
            print(f"✨ New social user '{email}'. Creating new user profile and tenant...")
            
            # 2.1 Create a new tenant document
            tenant_doc_ref = db.collection('tenants').document()
            new_tenant_id = tenant_doc_ref.id
            tenant_data = {
                'createdAt': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'owner_uid': uid,
                'email': email,
                'tenantName': f"{display_name}'s Shop", # Default tenant name
                'members': { uid: 'owner' }
            }
            tenant_doc_ref.set(tenant_data)
            print(f"✅ New tenant '{new_tenant_id}' created for user '{uid}'.")

            # 2.2 Create the new user profile document
            user_ref.set({
                'uid': uid,
                'email': email,
                'displayName': display_name,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'tenants': { new_tenant_id: 'owner' }
            })
            print(f"✅ New user profile created for '{uid}'.")

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