"""
หน้า: โปรเจกต์ (ฝั่งผู้จัดงาน)

ปุ่ม 'สร้างโปรเจกต์'     create_project          INSERT PROJECT
ปุ่ม 'เปลี่ยนสถานะ'       update_project_status   UPDATE PROJECT
ตารางรายการโปรเจกต์      list_projects           PROJECT LEFT JOIN ROLE (นับจำนวนบท)
"""
import streamlit as st

import queries as q
import ui
from config import (PROJECT_STATUS_LABEL, PROJECT_STATUSES, PROJECT_TYPE_LABEL, PROJECT_TYPES)

ui.page_header("โปรเจกต์", "งานทั้งหมดของเอเจนซี่ สร้างโปรเจกต์ใหม่ และเปลี่ยนสถานะได้ที่นี่")

with st.expander("สร้างโปรเจกต์ใหม่", expanded=False, icon=":material/add_circle:"):
    with st.form("project_form", clear_on_submit=True, border=False):
        name = st.text_input("ชื่อโปรเจกต์")
        ptype = st.selectbox("ประเภท", PROJECT_TYPES, format_func=PROJECT_TYPE_LABEL.get)
        client = st.text_input("ชื่อลูกค้า / บริษัทเจ้าของงาน")
        go = st.form_submit_button("สร้างโปรเจกต์", type="primary")
    if go:
        ui.do(q.create_project, name, ptype, client, ok_msg="สร้างโปรเจกต์แล้ว")

projects = q.list_projects()
for p in projects:
    p["project_type"] = PROJECT_TYPE_LABEL.get(p["project_type"], p["project_type"])

ui.section("รายการโปรเจกต์")
ui.table(projects, {"project_id": "รหัส", "project_name": "ชื่อโปรเจกต์", "project_type": "ประเภท",
                    "client_name": "ลูกค้า", "project_status": "สถานะ", "role_count": "จำนวนบท"},
         badges={"project_status": lambda r: ui.project_badge(r["project_status"])})

if projects:
    ui.section("เปลี่ยนสถานะโปรเจกต์")
    labels = {p["project_id"]: f"#{p['project_id']} {p['project_name']}" for p in projects}
    c1, c2, c3 = st.columns([3, 2, 1], vertical_alignment="bottom")
    pid = c1.selectbox("โปรเจกต์", list(labels), format_func=labels.get, key="status_project")
    new_status = c2.selectbox("สถานะใหม่", PROJECT_STATUSES, format_func=PROJECT_STATUS_LABEL.get)
    if c3.button("บันทึก", key="save_project_status", type="primary", width="stretch"):
        ui.do(q.update_project_status, pid, new_status, ok_msg="เปลี่ยนสถานะแล้ว")
