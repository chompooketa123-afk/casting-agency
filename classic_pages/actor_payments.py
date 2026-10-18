"""
หน้า: การจ่ายเงินของฉัน (ฝั่งนักแสดง)

หน้านี้ดึง payments_of_actor -> PAYMENT_INSTALLMENT JOIN ROLE JOIN PROJECT
"เลยกำหนด" ไม่ได้เก็บเป็นคอลัมน์ แต่คำนวณตอน query:  payment_status='Pending' AND due_date < CURDATE()
"""
import streamlit as st

import queries as q
import ui

ui.page_header("การจ่ายเงินของฉัน", "ค่าตัวแต่ละงวดที่ได้รับและที่ยังรอรับ")
actor_id = ui.actor_picker()
if not actor_id:
    st.stop()

rows = q.payments_of_actor(actor_id)
if not rows:
    st.info("ยังไม่มีงวดจ่ายเงิน")
    st.stop()

paid = sum(r["amount"] for r in rows if r["payment_status"] == "Paid")
pending = sum(r["amount"] for r in rows if r["payment_status"] == "Pending")
overdue = sum(r["amount"] for r in rows if r["is_overdue"])
ui.stat_row([
    ("ได้รับแล้ว (บาท)", f"{paid:,.0f}", None, "ok"),
    ("รอรับ (บาท)", f"{pending:,.0f}", None, None),
    ("เลยกำหนดจ่าย (บาท)", f"{overdue:,.0f}", "ควรทวงถาม" if overdue else None, "bad" if overdue else None),
])

ui.table(rows, {"project_name": "โปรเจกต์", "role_name": "บท", "due_date": "ครบกำหนด",
                "amount": "จำนวนเงิน (บาท)", "payment_status": "สถานะ"},
         badges={"payment_status": lambda r: ui.payment_badge(r["payment_status"], r["is_overdue"])})
