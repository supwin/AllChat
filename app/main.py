# Force update
# app/main.py
     
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# 1. Import Routers ทั้งหมดที่คุณมี
# ตรวจสอบให้แน่ใจว่าชื่อตรงกับไฟล์ในโฟลเดอร์ /routers
from .routers import auth, tenant, webhook, assistant, inbox, inbox_api, user

# --- App Initialization ---
app = FastAPI(
    title="AllChat API",
    description="Backend services for the AllChat Platform.",
    version="1.0.0"
)

# --- CORS Middleware ---
# สำคัญมากเพื่อให้ Frontend คุยกับ Backend ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ใน Production ควรระบุ Domain ของ Frontend จริงๆ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
# 2. ลงทะเบียน API Router ทั้งหมด
app.include_router(auth.router)
app.include_router(tenant.router)
app.include_router(webhook.router)
app.include_router(assistant.router)
app.include_router(inbox.router)
app.include_router(inbox_api.router)
app.include_router(user.router)


# --- Static Files and HTML Page Serving ---

# 3. Mount โฟลเดอร์ 'static' เพื่อให้เข้าถึงไฟล์ CSS, JS, รูปภาพได้
# ทุก request ที่ขึ้นต้นด้วย /static จะถูกหาจากในโฟลเดอร์ static
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# 4. สร้าง Route เพื่อเสิร์ฟไฟล์ HTML แต่ละหน้า
# ทำให้เราสามารถเข้าหน้าเว็บด้วย URL สวยๆ เช่น /login, /dashboard

@app.get("/", response_class=HTMLResponse, tags=["Frontend Pages"])
async def read_root():
    """ส่งผู้ใช้ไปที่หน้า login เป็นหน้าแรก"""
    return FileResponse(os.path.join(static_dir, 'login.html'))

@app.get("/login", response_class=HTMLResponse, tags=["Frontend Pages"])
async def read_login():
    return FileResponse(os.path.join(static_dir, 'login.html'))

@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend Pages"])
async def read_dashboard():
    return FileResponse(os.path.join(static_dir, 'dashboard.html'))

@app.get("/tenant-selector", response_class=HTMLResponse, tags=["Frontend Pages"])
async def read_tenant_selector():
    return FileResponse(os.path.join(static_dir, 'tenant-selector.html'))

# --- เพิ่ม Route สำหรับหน้าอื่นๆ ที่คุณมี ---

@app.get("/wizard_setup_ui.html", response_class=HTMLResponse, tags=["Frontend Pages"])
async def read_wizard():
    return FileResponse(os.path.join(static_dir, 'wizard_setup_ui.html'))

@app.get("/settings", response_class=HTMLResponse, tags=["Frontend Pages"])
async def read_settings():
    return FileResponse(os.path.join(static_dir, 'settings.html'))

@app.get("/inbox", response_class=HTMLResponse, tags=["Frontend Pages"])
async def read_inbox():
    return FileResponse(os.path.join(static_dir, 'inbox.html'))

@app.get("/line-setup-guide", response_class=HTMLResponse, tags=["Frontend Pages"])
async def read_line_guide():
    return FileResponse(os.path.join(static_dir, 'line-setup-guide.html'))

@app.get("/facebook-setup-guide", response_class=HTMLResponse, tags=["Frontend Pages"])
async def read_facebook_guide():
    return FileResponse(os.path.join(static_dir, 'facebook-setup-guide.html'))

@app.get("/website-setup-guide", response_class=HTMLResponse, tags=["Frontend Pages"])
async def read_website_guide():
    return FileResponse(os.path.join(static_dir, 'website-setup-guide.html'))

