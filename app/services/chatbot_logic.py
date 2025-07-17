# app/services/chatbot_logic.py
import re
from typing import List, Dict, Any, Optional
from google.generativeai.types import content_types
import datetime
from firebase_admin import firestore # ✨ เพิ่ม import ที่จำเป็น

# ✨ ย้าย `db` มา import จาก `firebase_utils` ที่เดียวกับ `firestore` เพื่อความสอดคล้องกัน
from ..services.firebase_utils import db
from ..config.settings import get_gemini_end_user_model, get_openai_client
from ..prompts.summarization_prompt import SUMMARIZATION_PROMPT

# Constants for conversational summarization
SUMMARIZATION_THRESHOLD = 10
RECENT_MESSAGES_TO_KEEP = 4


# ✨ 1. สร้างฟังก์ชันกลางสำหรับสร้าง Log ของ Error
def create_error_log_entry(user_input: str, error_message: str, failure_type: str) -> dict:
    """
    ฟังก์ชันกลางสำหรับสร้าง Dictionary ของข้อความที่เกิดข้อผิดพลาด
    """
    print(f"INFO: Creating error log entry. Type: '{failure_type}', Details: {error_message}")

    # กำหนดสถานะของข้อความตามประเภทของความล้มเหลว
    status = 'requires_manual_reply' if failure_type in ['full_fallback_failed', 'core_logic_error', 'initialization_error'] else 'requires_review'

    # สร้างและ return Dictionary ของข้อความที่มีปัญหา
    error_entry = {
        'role': 'user', # ข้อความที่ทำให้เกิดปัญหามาจาก user
        'parts': [{'text': user_input}],
        'status': status,
        'failure_type': failure_type,
        'error_details': error_message,
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    return error_entry


# ✨ 2. นี่คือฟังก์ชัน get_bot_response ทั้งหมดที่ถูกปรับปรุงใหม่
def get_bot_response(
    tenant_id: str,
    user_id: str,
    user_input: str,
    platform: str = "unknown",
    display_name: Optional[str] = None,
    last_message_time: Optional[str] = None
) -> str:
    """
    Generates a bot response using Gemini, with OpenAI fallback, and robust error logging.
    """
    end_user_model = get_gemini_end_user_model()
    openai_client = get_openai_client()
    history_ref = db.collection('chat_sessions').document(tenant_id).collection('users').document(user_id)
    
    # ดึงข้อมูลการตั้งค่าและประวัติแชท
    try:
        tenant_ref = db.collection('tenants').document(tenant_id)
        tenant_data = tenant_ref.get()
        if not tenant_data.exists:
            return "ขออภัยค่ะ ไม่พบข้อมูลผู้ให้บริการ"
        config = tenant_data.to_dict()

        history_doc = history_ref.get()
        user_profile_data = history_doc.to_dict() if history_doc.exists else {}
        history_data_from_db = user_profile_data.get('history', [])
        current_summary = user_profile_data.get('summary', "")
        
        # --- ส่วนของโค้ด Summarization ---
        messages_to_summarize = [msg for msg in history_data_from_db if not msg.get('summarized', False)]
        if len(messages_to_summarize) > SUMMARIZATION_THRESHOLD and end_user_model:
            print(f"🔄 Tenant {tenant_id}: New messages exceed threshold. Attempting summarization...")
            try:
                new_conversation_text = ""
                for msg in messages_to_summarize:
                    role = msg['role']
                    text_parts = [part['text'] for part in msg['parts'] if 'text' in part]
                    new_conversation_text += f"{role}: {' '.join(text_parts)}\n"
                context_for_summarizer = f"PREVIOUS SUMMARY:\n{current_summary}\n\n---\n\nNEW MESSAGES TO ADD TO SUMMARY:\n{new_conversation_text}"
                summarization_chat = end_user_model.start_chat(history=[])
                summary_response = summarization_chat.send_message(
                    SUMMARIZATION_PROMPT.format(conversation_history=context_for_summarizer)
                )
                new_summary = summary_response.text
                print(f"✅ Tenant {tenant_id}: Summarization successful.")
                current_summary = new_summary
                for msg in history_data_from_db:
                    if not msg.get('summarized'):
                        msg['summarized'] = True
                print(f"✅ Tenant {tenant_id}: Marked {len(messages_to_summarize)} messages as summarized.")
            except Exception as sum_e:
                # หากการสรุปล้มเหลว ให้สร้าง Log แต่ยังคงทำงานต่อไป
                error_entry = create_error_log_entry(user_input, str(sum_e), "summarization_failed")
                history_data_from_db.append(error_entry)
                print(f"⚠️ Tenant {tenant_id}: Summarization failed but process continues.")

        # --- ส่วนของ Prompt Template ---
        behavioral_instructions = []
        if config.get('is_detailed_response', False): behavioral_instructions.append("- จงตอบคำถามอย่างละเอียดและให้ข้อมูลครบถ้วน")
        else: behavioral_instructions.append("- จงตอบคำถามให้สั้น กระชับ และตรงประเด็น")
        if config.get('is_sweet_tone', False): behavioral_instructions.append("- จงใช้น้ำเสียงที่อ่อนหวาน สุภาพ และกล่าวชื่นชมลูกค้าตามความเหมาะสม")
        else: behavioral_instructions.append("- สามารถสอดแทรกมุกตลกเล็กๆ น้อยๆ หรือใช้คำพูดที่ดูเท่ห์และทันสมัยได้")
        if config.get('show_empathy', False): behavioral_instructions.append("- จงแสดงความใส่ใจในปัญหาของลูกค้า ถามไถ่ด้วยความเป็นห่วงเป็นใย")
        if config.get('high_sales_drive', False): behavioral_instructions.append("- จงพยายามหาโอกาสในการปิดการขายอย่างสม่ำเสมอ เสนอสินค้าหรือบริการที่เกี่ยวข้องเพื่อกระตุ้นการตัดสินใจ")
        else: behavioral_instructions.append("- จงเน้นการให้ข้อมูลที่เป็นประโยชน์และตอบคำถามให้ชัดเจน ไม่ต้องกดดันลูกค้าให้ซื้อสินค้า")
        behavioral_prompt_section = "\n".join(behavioral_instructions)
        base_persona = config.get('botPersona', "คุณคือผู้ช่วย AI")
        prompt_template = f"{base_persona}\n\n--- คำสั่งและลักษณะนิสัยเพิ่มเติม ---\n{behavioral_prompt_section}"
        knowledge_base = config.get('knowledgeBase', "")
        
        # --- ส่วนเตรียม History สำหรับ Model ---
        chat_history_for_model = []
        if current_summary:
            chat_history_for_model.append(content_types.to_content({'role': 'user', 'parts': [{'text': f"Summary of previous conversation:\n{current_summary}"}]}))
            chat_history_for_model.append(content_types.to_content({'role': 'model', 'parts': [{'text': "OK, I understand the context."}]}))
        
        clean_history = [{'role': item['role'], 'parts': item['parts']} for item in history_data_from_db[-RECENT_MESSAGES_TO_KEEP:] if item.get('status') is None]
        chat_history_for_model.extend([content_types.to_content(item) for item in clean_history])

        keywords = re.split(r'\s+', user_input)
        relevant_chunks = [chunk.strip() for chunk in knowledge_base.split('###') if any(kw in chunk for kw in keywords if len(kw) > 2)]
        retrieved_info = "\n\n".join(relevant_chunks) if relevant_chunks else "ไม่มีข้อมูลที่เกี่ยวข้องโดยตรง"
        final_prompt = f"{prompt_template}\n\n--- ข้อมูลอ้างอิง ---\n{retrieved_info}\n\n--- คำถามล่าสุด ---\n{user_input}"

    except Exception as e:
        print(f"❌ INITIALIZATION ERROR for tenant {tenant_id}, user {user_id}: {e}")
        error_entry = create_error_log_entry(user_input, str(e), "initialization_error")
        try:
            history_ref.update({'history': firestore.ArrayUnion([error_entry])})
        except Exception as db_e:
            print(f"❌ CRITICAL DB ERROR during init: Could not log error. Reason: {db_e}")
        return "ขออภัยค่ะ ระบบขัดข้อง โปรดลองอีกครั้ง"

    # --- ส่วน Logic การสร้างคำตอบที่ปรับปรุงใหม่ ---
    history_to_save = list(history_data_from_db)
    reply_msg = ""
    is_successful = False

    try:
        if not end_user_model: raise Exception("Gemini model not available")
        chat = end_user_model.start_chat(history=chat_history_for_model)
        response = chat.send_message(final_prompt)
        reply_msg = response.text
        is_successful = True
        print(f"✅ Tenant {tenant_id}: Got response from Gemini.")

    except Exception as gemini_e:
        print(f"⚠️ Tenant {tenant_id}: Gemini failed ({gemini_e}). Attempting fallback to OpenAI...")
        try:
            if not openai_client: raise Exception("OpenAI client not available for fallback")
            openai_messages = []
            if current_summary: openai_messages.append({"role": "system", "content": f"Summary of previous conversation:\n{current_summary}"})
            openai_messages.extend([{"role": "assistant" if item['role'] == 'model' else item['role'], "content": ' '.join([p['text'] for p in item['parts'] if 'text' in p])} for item in clean_history])
            openai_messages.append({"role": "user", "content": final_prompt})
            completion = openai_client.chat.completions.create(model="gpt-3.5-turbo", messages=openai_messages)
            reply_msg = completion.choices[0].message.content
            is_successful = True
            print(f"✅ Tenant {tenant_id}: Got response from OpenAI fallback.")
        except Exception as openai_e:
            print(f"❌ Tenant {tenant_id}: OpenAI fallback also failed: {openai_e}")
            error_entry = create_error_log_entry(user_input, str(openai_e), "full_fallback_failed")
            history_to_save.append(error_entry)
            reply_msg = "ขออภัยค่ะ ขณะนี้ระบบ AI ทั้งระบบหลักและระบบสำรองขัดข้อง โปรดลองอีกครั้งภายหลัง"

    # --- ส่วนสุดท้าย: การบันทึกข้อมูลลง DB เพียงครั้งเดียว ---
    try:
        if is_successful:
            user_msg_for_history = {
                'role': 'user',
                'parts': [{'text': user_input}],
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            model_reply_for_history = {
                'role': 'model',
                'parts': [{'text': reply_msg}],
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            history_to_save.append(user_msg_for_history)
            history_to_save.append(model_reply_for_history)
        
        user_profile_data['history'] = history_to_save
        user_profile_data['summary'] = current_summary
        user_profile_data['lastMessageTime'] = last_message_time if last_message_time else datetime.datetime.now(datetime.timezone.utc).isoformat()
        if display_name: user_profile_data['displayName'] = display_name
        if 'platform' not in user_profile_data: user_profile_data['platform'] = platform

        history_ref.set(user_profile_data)
        print(f"✅ Tenant {tenant_id}: Final data saved to Firestore. Success: {is_successful}")

    except Exception as final_db_e:
        print(f"❌ CRITICAL FINAL SAVE ERROR for tenant {tenant_id}: {final_db_e}")

    return reply_msg