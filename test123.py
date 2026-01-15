import os
import google.generativeai as genai
import pandas as pd
import streamlit as st
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import dotenv

# --- 1. โหลดค่า Environment ---
dotenv.load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    st.error("🔑 กรุณาตั้งค่า GOOGLE_API_KEY ในไฟล์ .env")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. ตั้งค่า Model ---
generation_config = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
}

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
}

# กำหนด System Instruction เบื้องต้น (หากไม่มีไฟล์ prompt ภายนอก)
SYSTEM_PROMPT = "คุณคือ Workaw ผู้เชี่ยวชาญด้านสิทธิแรงงาน ตอบคำถามโดยอ้างอิงข้อมูลที่ได้รับเท่านั้น ตอบด้วย ค่ะ/คะ เสมอ"

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", # แนะนำ 1.5-flash เพื่อความเสถียร
    safety_settings=SAFETY_SETTINGS,
    generation_config=generation_config,
    system_instruction=SYSTEM_PROMPT
)

# --- 3. ฟังก์ชันการทำงาน ---
def clear_history():
    st.session_state["messages"] = [
        {"role": "model", "content": "Workaw สวัสดีค่ะ คุณลูกค้า สอบถามข้อมูลการคุ้มครองแรงงาน สิทธิและสวัสดิการเรื่องใดคะ"}
    ]
    st.rerun()

# --- 4. การจัดการ UI ---
st.title("💬 Workaw สวัสดีค่ะ")

with st.sidebar:
    st.header("ตั้งค่า")
    if st.button("🗑️ Clear History", use_container_width=True):
        clear_history()

# --- 5. โหลดข้อมูลจาก Excel ---
# ใช้ Path แบบยืดหยุ่น (หากรันบนเครื่องตัวเองให้ใช้ Path เต็มได้ค่ะ)
file_path = "Context for chatbot.xlsx" 

@st.cache_data
def load_context(path):
    try:
        if not os.path.exists(path):
            return None
        df = pd.read_excel(path, engine='openpyxl')
        return df.to_string(index=False)
    except Exception as e:
        return f"Error: {e}"

file_content = load_context(file_path)

if file_content is None or file_content.startswith("Error"):
    st.warning(f"⚠️ ไม่พบไฟล์ข้อมูลที่ {file_path} ระบบจะตอบคำถามทั่วไปแทน")
    file_content = "ไม่มีข้อมูลในฐานข้อมูล"

# --- 6. ระบบ Chat ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "model", "content": "Workaw สวัสดีค่ะ คุณลูกค้า สอบถามข้อมูลการคุ้มครองแรงงานเรื่องใดคะ"}
    ]

# แสดงข้อความเก่า
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# รับข้อความใหม่
if prompt := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("model"):
        with st.spinner("Workaw กำลังหาข้อมูลให้ค่ะ..."):
            if prompt.lower().strip() in ["add", "เพิ่ม"]:
                response_text = "ขอบคุณสำหรับคำแนะนำค่ะ"
            else:
                # สร้างประวัติการคุย โดยส่ง Context เข้าไปใน Message แรกสุดของ Session นั้นๆ
                history = []
                # ใส่ Context เป็นฐานข้อมูลให้ AI รับรู้ก่อน
                history.append({"role": "user", "parts": [f"นี่คือข้อมูลอ้างอิงของคุณ:\n{file_content}"]})
                history.append({"role": "model", "parts": ["รับทราบค่ะ ฉันจะใช้ข้อมูลนี้ตอบคำถามของคุณนะคะ"]})
                
                # ใส่ประวัติการคุยจริง (จำกัด 5-10 ข้อความล่าสุดเพื่อประหยัด Token)
                for msg in st.session_state["messages"][-6:]:
                    history.append({"role": msg["role"], "parts": [msg["content"]]})

                try:
                    chat_session = model.start_chat(history=history)
                    response = chat_session.send_message(prompt)
                    response_text = response.text
                except Exception as e:
                    response_text = f"ขออภัยค่ะ เกิดข้อผิดพลาดทางเทคนิค: {e}"

            st.write(response_text)
            st.session_state["messages"].append({"role": "model", "content": response_text})