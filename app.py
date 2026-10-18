"""
app.py : จุดเริ่มต้นของเว็บ (รันด้วย  streamlit run app.py)

หน้าตาทั้งหมดอยู่ในโฟลเดอร์ ui/ (HTML + CSS + JavaScript ที่ออกแบบเป็นแบบเดโม)
Streamlit ทำหน้าที่ "หลังบ้าน" ตัวเดียว:
    ui/*.js  --(ทุกปุ่มที่บันทึก)-->  bridge.py  -->  queries.py  -->  MySQL
    ui/*.js  <--(ข้อมูลล่าสุดทุกตาราง)--  bridge.snapshot()  <--  MySQL
โครงสร้าง
    app.py        ไฟล์นี้: ต่อ MySQL, ฝังหน้าตา, รับคำสั่งจากปุ่มแล้วส่งต่อ bridge.py
    bridge.py     แปลงคำสั่งจากหน้าเว็บ -> เรียกฟังก์ชันใน queries.py / อ่านทุกตารางส่งกลับ
    queries.py    SQL + กฎธุรกิจทั้งหมด (คิวชน ทักษะครบ กันจ่ายซ้ำ ฯลฯ)
    db.py         เชื่อมต่อ MySQL (pool, transaction, SQL log)
    config.py     ค่าเชื่อมต่อ DB + ป้ายสถานะภาษาไทย
    ui/           หน้าตาและตรรกะฝั่งเบราว์เซอร์ (core.js views.js main.js style.css)
    sql/          schema.sql (ตาราง) + seed.sql (ข้อมูลตัวอย่าง)
    app_classic.py + classic_pages/   เวอร์ชัน Streamlit ล้วนแบบเดิม (สำรอง)
"""
import time
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Casting Agency", page_icon=":material/movie:", layout="wide",
                   initial_sidebar_state="collapsed")

import bridge   # noqa: E402  (ต้อง import หลัง set_page_config)
import db       # noqa: E402

UI = Path(__file__).parent / "ui"

# ซ่อนส่วนเมนู/ขอบของ Streamlit ให้หน้าตาเป็นของเราทั้งหน้า
st.html("""<style>
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer,
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
.stApp { background: #FAF6F2 !important; }
[data-testid="stMainBlockContainer"], .block-container { padding: 0 !important; max-width: none !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stAppViewContainer"] > section, [data-testid="stMain"] { overflow-x: clip; }
</style>""")

error = db.check_connection()
if error:
    st.error("ต่อฐานข้อมูล MySQL ไม่ได้", icon=":material/block:")
    st.code(error)
    st.markdown(
        """
**ลองเช็กตามนี้ทีละข้อ**
1. เปิด **XAMPP Control Panel** แล้วกด **Start** ที่แถว **MySQL** (ต้องขึ้นสีเขียว)
2. ยังไม่เคยสร้างฐานข้อมูล? เปิด Terminal ที่โฟลเดอร์นี้แล้วรัน `python setup_db.py`
3. ตั้งรหัสผ่าน MySQL ไว้? แก้ `password` ใน `config.py` ให้ตรง (ขึ้นเว็บจริง: ใส่ใน Secrets ดู `DEPLOY.md`)

แก้เสร็จแล้วกด **R** บนหน้านี้ หรือรีเฟรชเบราว์เซอร์
""")
    st.stop()


@st.cache_resource
def _component():
    """ลงทะเบียนหน้าตา (ทำครั้งเดียวทั้งแอป)"""
    html = ('<div id="app"><div id="root"><div class="loading">กำลังโหลดข้อมูลจากฐานข้อมูล…</div></div>'
            '<div id="ov"></div><div id="toast" aria-live="polite"></div></div>')
    js = "\n".join((UI / n).read_text(encoding="utf-8") for n in ("head.js", "core.js", "views.js", "main.js", "tail.js"))
    return st.components.v2.component("casting_ui", html=html, css=(UI / "style.css").read_text(encoding="utf-8"), js=js)


def _on_call():
    """ปุ่มในหน้าเว็บส่งคำสั่งมา -> รันกับ MySQL -> เก็บผลไว้ส่งกลับในรอบถัดไป"""
    call = (st.session_state.get("casting_ui") or {}).get("call")
    if call:
        reply = bridge.handle(call.get("op"), call.get("args"))
        reply["id"] = call.get("id")
        st.session_state["reply"] = reply


try:
    snap = bridge.snapshot()      # อ่านทุกตารางสดๆ ทุกครั้ง (ต่อจากคำสั่งที่เพิ่งรัน จึงเห็นผลทันที)
except Exception as e:            # noqa: BLE001
    st.error("อ่านข้อมูลจากฐานข้อมูลไม่ได้ (ยังไม่ได้สร้างตารางหรือเปล่า? รัน `python setup_db.py`)", icon=":material/block:")
    st.code(str(e))
    st.stop()

_component()(key="casting_ui", data={"snap": snap, "ver": time.time_ns(), "reply": st.session_state.get("reply")},
             on_call_change=_on_call)
