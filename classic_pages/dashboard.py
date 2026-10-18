"""
หน้า: Dashboard -- สรุปภาพรวมด้วย SQL แบบ GROUP BY / SUM / COUNT
ทุกตัวเลขมาจาก queries.dashboard_numbers() (เปิดโหมดโชว์ SQL ดูได้)
"""
import pandas as pd
import streamlit as st

import queries as q
import ui
from config import PAYMENT_STATUS_LABEL, ROLE_STATUS_LABEL

ui.page_header("Dashboard", "สรุปภาพรวมของนักแสดง โปรเจกต์ บท และการเงิน")
n = q.dashboard_numbers()

a = {r["status"]: r["n"] for r in n["actors_by_status"]}
p = {r["status"]: r["n"] for r in n["projects_by_status"]}
overdue = n["overdue"]
ui.stat_row([
    ("นักแสดงพร้อมรับงาน", a.get("Active", 0), f"พักงาน {a.get('Inactive', 0)} คน", None),
    ("โปรเจกต์ที่เปิดอยู่", p.get("Open", 0) + p.get("In_Progress", 0), None, None),
    ("งวดเลยกำหนดจ่าย", overdue["n"], f"รวม {overdue['total']:,.0f} บาท" if overdue["n"] else "ไม่มีงวดค้าง",
     "bad" if overdue["n"] else "ok"),
    ("บทที่รอนักแสดงตอบ", {r["status"]: r["n"] for r in n["roles_by_status"]}.get("Selected", 0), None, None),
])

left, right = st.columns(2, gap="large")
with left:
    ui.section("บทแยกตามสถานะ")
    df = pd.DataFrame(n["roles_by_status"])
    if not df.empty:
        df["status"] = df["status"].map(ROLE_STATUS_LABEL)
        ui.hbar(df, "status", "n", colors=ui.ROLE_COLOR)
with right:
    ui.section("ยอดเงินแยกตามสถานะงวด", "หน่วย: บาท")
    df = pd.DataFrame(n["payments_by_status"])
    if not df.empty:
        df["status"] = df["status"].map(PAYMENT_STATUS_LABEL)
        df["total"] = df["total"].astype(float)
        ui.hbar(df, "status", "total", colors=ui.PAYMENT_COLOR)

left, right = st.columns(2, gap="large")
with left:
    ui.section("ทักษะที่นักแสดงมีมากที่สุด", "จำนวนนักแสดง")
    df = pd.DataFrame(n["skill_popularity"])
    if not df.empty:
        ui.hbar(df, "skill_name", "actors")
with right:
    ui.section("จ่ายแล้ว และรอจ่าย ต่อโปรเจกต์", "หน่วย: บาท")
    df = pd.DataFrame(n["payments_by_project"])
    if not df.empty:
        df = df.rename(columns={"paid": "จ่ายแล้ว", "pending": "รอจ่าย"})
        long = df.melt(id_vars="project_name", value_vars=["จ่ายแล้ว", "รอจ่าย"], var_name="status", value_name="amount")
        long["amount"] = long["amount"].astype(float)
        ui.stacked_money(long, "project_name", "status", {"จ่ายแล้ว": ui.EMERALD, "รอจ่าย": ui.GOLD})
