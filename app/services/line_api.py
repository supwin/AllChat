# app/services/line_api.py
import requests
from typing import Dict, Any # ✨ เพิ่มการ import Type Hint

def send_line_message(reply_token: str, message_text: str, line_access_token: str) -> Dict[str, Any]:
    """
    Sends a reply message back to LINE using the LINE Messaging API.
    """
    if not line_access_token:
        print("❌ LINE API: Missing LINE Channel Access Token.")
        return {"status": "error", "message": "Missing LINE token"}

    line_headers = {
        "Authorization": f"Bearer {line_access_token}",
        "Content-Type": "application/json"
    }
    reply_body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message_text.strip()}]
    }

    try:
        response = requests.post("https://api.line.me/v2/bot/message/reply", headers=line_headers, json=reply_body)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        print(f"✅ LINE API: Message sent successfully. Response: {response.json()}")
        return {"status": "ok", "response": response.json()}
    except requests.exceptions.RequestException as e:
        print(f"❌ LINE API: Failed to send message: {e}")
        return {"status": "error", "message": f"Failed to send LINE message: {e}"}

# ✨ --- เพิ่มฟังก์ชันใหม่ด้านล่างนี้ --- ✨
def get_line_user_profile(user_id: str, access_token: str) -> dict:
    """
    ดึงข้อมูลโปรไฟล์ผู้ใช้จาก LINE โดยใช้ User ID
    """
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not fetch LINE profile for {user_id}: {e}")
        return {} # คืนค่า dict ว่างเปล่าหากเกิดข้อผิดพลาด

def push_line_message(user_id: str, message_text: str, line_access_token: str) -> Dict[str, Any]:
    """
    Sends a push message to a specific user via the LINE Messaging API.
    Used for admin-initiated messages.
    """
    if not line_access_token:
        print("❌ LINE API (Push): Missing LINE Channel Access Token.")
        return {"status": "error", "message": "Missing LINE token"}

    push_url = "https://api.line.me/v2/bot/message/push"
    
    headers = {
        "Authorization": f"Bearer {line_access_token}",
        "Content-Type": "application/json"
    }

    body = {
        "to": user_id,
        "messages": [{"type": "text", "text": message_text.strip()}]
    }

    try:
        response = requests.post(push_url, headers=headers, json=body)
        response.raise_for_status() # Raise an exception for HTTP errors
        print(f"✅ LINE API (Push): Message pushed successfully to {user_id}.")
        return {"status": "ok", "response": response.json()}
    except requests.exceptions.RequestException as e:
        print(f"❌ LINE API (Push): Failed to push message: {e}")
        return {"status": "error", "message": f"Failed to push LINE message: {e}"}