"""
หน้า: ค้นหานักแสดง (ฝั่งผู้จัดงาน) -- แก้ปัญหา "ค้นหาแบบเจาะจงเงื่อนไขไม่ได้" ในสไลด์

ปุ่ม 'ค้นหา'   search_actors   ACTOR (+ ACTOR_SKILL / SKILL / ROLE / SCHEDULE ตามตัวกรองที่เลือก)
ตัวกรองทั้งหมดทำงาน "พร้อมกัน" (AND) : เพศ, ทักษะ (ต้องมีครบ), คำในรูปลักษณ์, ว่างในช่วงเวลา, สถานะ
"""
from datetime import date, time, timedelta

import streamlit as st

import queries as q
import ui
from config import GENDER_LABEL

ui.page_header("ค้นหานักแสดง", "ตัวกรองทุกข้อทำงานพร้อมกัน หาคนที่ตรงเงื่อนไขของงานจริงๆ  ทั้งทักษะ รูปลักษณ์ และความว่าง", eyebrow="สำหรับผู้จัดงาน")

skill_ids, skill_labels = ui.skill_options()

traits, n_traits = ui.trait_filters("srch")      # ตัวกรองรูปลักษณ์ (อยู่นอกฟอร์ม เพราะ expander ซ้อนในฟอร์มได้แต่เลื่อนค้าง)
with st.form("search_form", border=True):
    c1, c2 = st.columns(2)
    gender = c1.selectbox("เพศ", [None, *GENDER_LABEL],
                          format_func=lambda g: "ทุกเพศ" if g is None else GENDER_LABEL[g])
    text = c2.text_input("คำในรายละเอียดรูปลักษณ์", placeholder="เช่น ผมสั้น, สูง 17")
    st.markdown("**ทักษะ / ภาษา** (ต้องมีครบทุกข้อที่เลือก)")
    skills = ui.skill_group_pickers("srch")
    use_avail = st.checkbox("ต้องว่างในช่วงเวลา")
    d1, d2, d3 = st.columns(3)
    a_date = d1.date_input("วันที่", value=date.today() + timedelta(days=7))
    a_start = d2.time_input("เริ่ม", value=time(9, 0), step=900)
    a_end = d3.time_input("เลิก", value=time(17, 0), step=900)
    include_inactive = st.checkbox("รวมนักแสดงที่พักงานด้วย")
    go = st.form_submit_button("ค้นหา", type="primary")

if go:
    avail = {"event_date": a_date, "start_time": a_start, "end_time": a_end} if use_avail else None
    ok, rows = ui.do(q.search_actors, gender, skills, text or None, avail,
                     only_active=not include_inactive, traits=traits, rerun=False)
    if ok:
        st.success(f"พบ {len(rows)} คน", icon=":material/check_circle:")
        left, right = st.columns(2, gap="medium")
        for i, r in enumerate(rows):
            with (left if i % 2 == 0 else right):
                with st.container(key=f"card_found_{r['actor_id']}"):
                    st.html(ui.comp_card(r))
                    st.html(ui.actor_badge(r["actor_status"]))
