import os
import google.generativeai as genai
import pandas as pd
import streamlit as st
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import dotenv

# --- 1. การตั้งค่าหน้าจอและสไตล์ (Theme: Tech & Modern) ---
st.set_page_config(page_title="CompTech AI - ผู้ช่วยคอมพิวเตอร์", page_icon="💻", layout="centered")

st.markdown("""
    <style>
    /* ปรับแต่งพื้นหลังและฟอนต์ */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    /* ปรับแต่งหัวข้อ */
    h1 {
        color: #00d4ff;
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        text-shadow: 2px 2px 4px #000000;
    }
    /* ปรับแต่งกล่องแชท */
    .stChatMessage {
        border-radius: 15px;
        margin-bottom: 10px;
    }
    /* ปรับแต่งปุ่มใน Sidebar */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        border: 1px solid #00d4ff;
        background-color: transparent;
        color: #00d4ff;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00d4ff;
        color: #0e1117;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. โหลดค่า Environment ---
dotenv.load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    st.error("🔑 กรุณาตั้งค่า API Key ในระบบก่อนใช้งาน")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# --- 3. ตั้งค่า Model (Gemini 2.5 Flash) ---
model_name = "gemini-2.5-flash" 

generation_config = {
    "temperature": 0.4, # ปรับเพิ่มเล็กน้อยเพื่อให้ AI ช่วยแก้ปัญหาได้ยืดหยุ่นขึ้น
    "top_p": 0.9,
    "max_output_tokens": 2048,
}

# กำหนด System Instruction ให้เป็นผู้เชี่ยวชาญคอมพิวเตอร์
SYSTEM_PROMPT = """คุณคือ 'CompTech AI' ผู้เชี่ยวชาญด้านคอมพิวเตอร์ ฮาร์ดแวร์ ซอฟต์แวร์ และการเขียนโปรแกรม 
บุคลิกของคุณคือ: ฉลาด, ทันสมัย, และอธิบายเรื่องยากให้เข้าใจง่าย 
- หากมีข้อมูลอ้างอิงจากไฟล์ ให้ยึดข้อมูลในไฟล์เท่านั้น
- หากไม่มีข้อมูลในไฟล์ ให้ใช้ความรู้ด้านไอทีของคุณตอบอย่างมืออาชีพ
- พูดจาสุภาพ และใช้คำศัพท์เทคนิคอย่างเหมาะสม"""

model = genai.GenerativeModel(
    model_name=model_name,
    generation_config=generation_config,
    system_instruction=SYSTEM_PROMPT
)

# --- 4. ฟังก์ชันจัดการข้อมูล (Knowledge Base) ---
@st.cache_data
def load_context(path):
    try:
        if os.path.exists(path):
            df = pd.read_excel(path, engine='openpyxl')
            return df.to_string(index=False)
        return None
    except Exception as e:
        return None

# ไฟล์ Excel สำหรับเก็บความรู้เฉพาะทาง (เช่น ราคาอุปกรณ์, วิธีซ่อมเฉพาะอาการ)
file_path = "Computer_Context.xlsx" 
file_content = load_context(file_path)

# --- 5. ส่วน Sidebar ---
with st.sidebar:
    st.markdown("## ⚙️ IT Support Center")
    st.image("https://cdn-icons-png.flaticon.com/512/2001/2001405.png", width=80)
    st.info("สอบถามเรื่อง: จัดสเปกคอม, แก้ไข Windows, เขียนโค้ด หรืออัปเกรดเครื่อง")
    
    if st.button("🗑️ Clear Terminal Cache"):
        st.session_state["messages"] = [
            {"role": "assistant", "content": "ระบบ Reboot เรียบร้อย... มีอะไรให้ CompTech ช่วยดูแลครับ?"}
        ]
        st.rerun()
    
    st.divider()
    st.caption("System Status: Online")
    st.caption("Core: Gemini 2.5 Flash")

# --- 6. ส่วนการแสดงผลแชท ---
st.title("🤖 CompTech AI Support")
st.caption("Professional Computer & Technology Assistant")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "สวัสดีครับ ผม CompTech AI ยินดีต้อนรับเข้าสู่ศูนย์ช่วยเหลือด้านคอมพิวเตอร์ วันนี้มีปัญหาการใช้งานหรือต้องการปรึกษาเรื่องสเปกเครื่องไหมครับ?"}
    ]

# แสดงประวัติการคุย
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# รับคำถาม
if prompt := st.chat_input("สอบถามปัญหาคอมพิวเตอร์... (เช่น คอมเปิดไม่ติดทำไง?)"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing system status..."):
            try:
                history = []
                # ใส่ Context (ถ้ามี)
                if file_content:
                    history.append({"role": "user", "parts": [f"Technical Knowledge Base: {file_content}"]})
                    history.append({"role": "model", "parts": ["รับทราบข้อมูลเทคนิคพื้นฐานครับ"]})
                
                # ดึงประวัติล่าสุด
                for msg in st.session_state["messages"][-6:]:
                    role = "model" if msg["role"] == "assistant" else "user"
                    history.append({"role": role, "parts": [msg["content"]]})

                chat_session = model.start_chat(history=history)
                response = chat_session.send_message(prompt)
                response_text = response.text
                
            except Exception as e:
                response_text = f"ขออภัยครับ เกิดข้อผิดพลาดในระบบประมวลผล: {str(e)}"

            st.write(response_text)
            st.session_state["messages"].append({"role": "assistant", "content": response_text})
