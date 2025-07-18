# app/main.py
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import Firebase instances (db, auth) which are initialized directly when firebase_utils is imported
from .services.firebase_utils import db, auth
# No need to import end_user_model, wizard_model directly here anymore
# from .config.settings import initialize_ai_models, end_user_model, wizard_model 

# Import routers
from .routers import auth, tenant, webhook, assistant, inbox, inbox_api

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Define the path to the static files directory
# It's one level up from 'app' folder, then into 'static'
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
# Mount static files to be served from the /static URL path
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# No need to call initialize_ai_models() here anymore as models are initialized lazily
@app.on_event("startup")
async def startup_event():
    # initialize_ai_models() # <--- REMOVED THIS CALL
    print("✅ Application startup complete: AI models will be initialized on first access.")

# Include API routers to organize endpoints
app.include_router(auth.router)       # Authentication endpoints (register, login)
app.include_router(tenant.router)     # Tenant data management endpoints (get, update)
app.include_router(webhook.router)    # Webhook endpoints for LINE and Facebook
app.include_router(assistant.router)  # AI assistant endpoints (settings assistant, wizard)
app.include_router(inbox.router)
app.include_router(inbox_api.router)


# --- HTML Serving Endpoints ---
# These endpoints serve the main HTML pages from the static directory

@app.get("/", response_class=FileResponse)
async def read_root():
    """Serves the main index.html page."""
    return os.path.join(static_dir, "index.html")

@app.get("/setup", response_class=FileResponse)
async def read_setup():
    """Serves the wizard_setup_ui.html page."""
    return os.path.join(static_dir, "wizard_setup_ui.html")

@app.get("/dashboard", response_class=FileResponse)
async def read_dashboard():
    """Serves the dashboard.html page."""
    return os.path.join(static_dir, "dashboard.html")

@app.get("/inbox", response_class=FileResponse)
async def serve_inbox_page(): 
    """This route serves the main inbox HTML file."""
    return os.path.join(static_dir, "inbox.html")

@app.get("/settings", response_class=FileResponse)
async def read_settings():
    """Serves the settings.html page."""
    return os.path.join(static_dir, "settings.html")

@app.get("/line-setup-guide", response_class=FileResponse)
async def read_line_guide():
    """Serves the line-setup-guide.html page."""
    return os.path.join(static_dir, "line-setup-guide.html")

@app.get("/facebook-setup-guide", response_class=FileResponse)
async def read_facebook_guide():
    """Serves the facebook-setup-guide.html page."""
    return os.path.join(static_dir, "facebook-setup-guide.html")

@app.get("/website-setup-guide", response_class=FileResponse)
async def read_website_guide():
    """Serves the website-setup-guide.html page."""
    return os.path.join(static_dir, "website-setup-guide.html")    

@app.get("/login", response_class=FileResponse)
async def read_login():
    """Serves the login.html page."""
    return os.path.join(static_dir, "login.html")

# Note: The uvicorn command for running this app will now be:
# uvicorn app.main:app --host 0.0.0.0 --port $PORT
