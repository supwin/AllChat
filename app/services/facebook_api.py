# app/services/facebook_api.py
import requests
from typing import Dict, Any

def send_facebook_message(recipient_id: str, message_text: str, page_access_token: str) -> Dict[str, Any]:
    """
    Sends a message back to Facebook Messenger.
    """
    if not page_access_token:
        print("❌ Facebook API: Missing Facebook Page Access Token.")
        return {"status": "error", "message": "Missing Facebook Page Token"}

    params = {"access_token": page_access_token}
    headers = {"Content-Type": "application/json"}
    data = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}

    try:
        r = requests.post("https://graph.facebook.com/v20.0/me/messages", params=params, headers=headers, json=data)
        r.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        print(f"✅ Facebook API: Message sent successfully. Response: {r.json()}")
        return {"status": "ok", "response": r.json()}
    except requests.exceptions.RequestException as e:
        print(f"❌ Facebook API: Failed to send message: {e}")
        return {"status": "error", "message": f"Failed to send Facebook message: {e}"}

# ✨ --- เพิ่มฟังก์ชันใหม่ด้านล่างนี้ --- ✨
def get_facebook_user_profile(user_id: str, page_access_token: str) -> dict:
    """
    ดึงข้อมูลโปรไฟล์ผู้ใช้จาก Facebook Graph API
    """
    url = f"https://graph.facebook.com/{user_id}?fields=name,profile_pic&access_token={page_access_token}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not fetch Facebook profile for {user_id}: {e}")
        return {} # คืนค่า dict ว่างเปล่าหากเกิดข้อผิดพลาด
