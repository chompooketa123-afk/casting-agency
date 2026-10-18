"""
app_classic.py : เว็บแบบ Streamlit ดั้งเดิม (รันด้วย  streamlit run app_classic.py)

หน้าที่ของไฟล์นี้
  1) ตั้งค่าหน้าเว็บ + เช็กว่าต่อ MySQL ได้ไหม (ถ้าไม่ได้ บอกวิธีแก้แล้วหยุด)
  2) ประกาศเมนูทั้งหมด (st.navigation) แบ่งเป็น 3 กลุ่ม: ภาพรวม / ฝั่งนักแสดง / ฝั่งผู้จัดงาน
  3) รันหน้าที่ผู้ใช้เลือก (pg.run()) แล้วปิดท้ายด้วยแถบ "โหมดโชว์ SQL"

โครงสร้างโปรแกรม
    app.py          เมนู + ตั้งค่า          (ไฟล์นี้)
    config.py       ค่าเชื่อมต่อ DB + ป้ายสถานะภาษาไทย
    db.py           เชื่อมต่อ MySQL (pool, transaction, SQL log)
    queries.py      SQL + กฎธุรกิจทั้งหมด
    ui.py           ตัวช่วยหน้าตา (แจ้งผล, dropdown, ตาราง, ป้ายสถานะ, การ์ดนักแสดง, ตัวกรอง)
    art.py          วาดภาพนักแสดงเป็น SVG จากข้อมูลรูปลักษณ์ในตาราง ACTOR
    theme.css       สีและหน้าตาทั้งเว็บ (+ .streamlit/config.toml, static/fonts)
    pages/*.py      หน้าเว็บ หน้าละไฟล์ เรียกฟังก์ชันใน queries.py
    sql/            schema.sql (ตาราง) + seed.sql (ข้อมูลตัวอย่าง)
"""
import streamlit as st

st.set_page_config(page_title="Casting Agency", page_icon=":material/movie:", layout="wide")

import db   # noqa: E402  (ต้อง import หลัง set_page_config)
import ui   # noqa: E402

ui.inject_theme()      # สี ฟอนต์ ตาราง ฯลฯ อยู่ใน theme.css

error = db.check_connection()
if error:
    ui.page_header("Casting Agency", "ต่อฐานข้อมูล MySQL ไม่ได้ ลองเช็กตามขั้นตอนด้านล่าง")
    st.error("ต่อฐานข้อมูล MySQL ไม่ได้", icon=":material/block:")
    st.code(error)
    st.markdown(
        """
**ลองเช็กตามนี้ทีละข้อ**
1. เปิด **XAMPP Control Panel** แล้วกด **Start** ที่แถว **MySQL** (ต้องขึ้นสีเขียว)
2. ยังไม่เคยสร้างฐานข้อมูล? เปิด Terminal ที่โฟลเดอร์นี้แล้วรัน `python setup_db.py`
3. ตั้งรหัสผ่าน MySQL ไว้? แก้ `password` ใน `config.py` ให้ตรง
4. พอร์ตไม่ใช่ 3306? แก้ `port` ใน `config.py`

แก้เสร็จแล้วกด **R** บนหน้านี้ หรือรีเฟรชเบราว์เซอร์
"""
    )
    st.stop()

pages = {
    "ภาพรวม": [
        st.Page("classic_pages/home.py", title="หน้าแรก", icon=":material/home:", default=True),
        st.Page("classic_pages/talent.py", title="แคตตาล็อกนักแสดง", icon=":material/photo_library:"),
        st.Page("classic_pages/dashboard.py", title="Dashboard", icon=":material/insights:"),
    ],
    "ฝั่งนักแสดง": [
        st.Page("classic_pages/actor_register.py", title="สมัคร / แก้โปรไฟล์", icon=":material/person_add:"),
        st.Page("classic_pages/actor_profile.py", title="โปรไฟล์และผลงานของฉัน", icon=":material/badge:"),
        st.Page("classic_pages/actor_jobs.py", title="งานของฉัน (ยอมรับ/ปฏิเสธ)", icon=":material/theater_comedy:"),
        st.Page("classic_pages/actor_schedule.py", title="ตารางนัดของฉัน", icon=":material/calendar_month:"),
        st.Page("classic_pages/actor_payments.py", title="การจ่ายเงินของฉัน", icon=":material/payments:"),
    ],
    "ฝั่งผู้จัดงาน": [
        st.Page("classic_pages/org_projects.py", title="โปรเจกต์", icon=":material/movie:"),
        st.Page("classic_pages/org_casting.py", title="สร้างบท + จับคู่นักแสดง", icon=":material/person_search:"),
        st.Page("classic_pages/org_roles.py", title="จัดการบท / ยกเลิกการจ้าง", icon=":material/assignment:"),
        st.Page("classic_pages/org_payments.py", title="งวดจ่ายเงิน", icon=":material/credit_card:"),
        st.Page("classic_pages/org_search.py", title="ค้นหานักแสดง", icon=":material/search:"),
    ],
}

pg = st.navigation(pages, position="top")
ui.show_flash()     # ข้อความแจ้งผลจากการกดปุ่มรอบก่อน
try:
    pg.run()
finally:
    # ใช้ finally เพราะบางหน้าเรียก st.stop() กลางทาง (เช่นยังไม่มีข้อมูล)
    # ซึ่งจะตัดสคริปต์ทันที ถ้าไม่ใส่ finally แถบ "โหมดโชว์ SQL" จะหายไปในหน้านั้น
    ui.sql_footer()
