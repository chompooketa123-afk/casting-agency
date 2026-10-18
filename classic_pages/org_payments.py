"""
หน้า: งวดจ่ายเงิน (ฝั่งผู้จัดงาน)

รายการงวด                      list_payments            PAYMENT_INSTALLMENT JOIN ROLE JOIN PROJECT JOIN ACTOR
ปุ่ม 'บันทึกจ่าย'               mark_paid                UPDATE PAYMENT_INSTALLMENT ... WHERE payment_status='Pending'
                                                         (กดซ้ำจะไม่มีแถวตรงเงื่อนไข -> ระบบปฏิเสธ = กันจ่ายซ้ำ)
"""
import streamlit as st

import queries as q
import ui
from config import PAYMENT_STATUS_LABEL

ui.page_header("งวดจ่ายเงิน", "ติดตามและบันทึกการจ่ายค่าตัวทีละงวด")

projects = q.list_projects()
f1, f2, f3 = st.columns([2, 2, 2], vertical_alignment="bottom")
proj_labels = {0: "ทุกโปรเจกต์", **{p["project_id"]: p["project_name"] for p in projects}}
pid = f1.selectbox("โปรเจกต์", list(proj_labels), format_func=proj_labels.get)
status = f2.selectbox("สถานะ", [None, *PAYMENT_STATUS_LABEL],
                      format_func=lambda s: "ทุกสถานะ" if s is None else PAYMENT_STATUS_LABEL[s])
overdue_only = f3.toggle("เฉพาะที่เลยกำหนด")

rows = q.list_payments(status, overdue_only, pid or None)

over = sum(r["amount"] for r in rows if r["is_overdue"])
ui.stat_row([
    ("จ่ายแล้ว (บาท)", ui.money(sum(r["amount"] for r in rows if r["payment_status"] == "Paid")), None, "ok"),
    ("รอจ่าย (บาท)", ui.money(sum(r["amount"] for r in rows if r["payment_status"] == "Pending")), None, None),
    ("เลยกำหนด (บาท)", ui.money(over), "ควรรีบจ่าย" if over else None, "bad" if over else None),
])

if not rows:
    st.info("ไม่พบงวดตามเงื่อนไขนี้")
    st.stop()

WIDTHS = [2.6, 1.7, 1.6, 1.2, 1.3, 1.5, 1.5]
with st.container(key="row_head"):
    head = st.columns(WIDTHS)
    for col, t in zip(head, ["โปรเจกต์ / บท", "นักแสดง", "สถานะบท", "จำนวนเงิน", "ครบกำหนด", "สถานะงวด", ""]):
        col.html(f'<span class="colhead">{t}</span>')

for r in rows:
    with st.container(key=f"row_pay_{r['payment_id']}"):
        c = st.columns(WIDTHS, vertical_alignment="center")
        c[0].html(f'<div class="cell-main">{ui.esc(r["project_name"])}</div>'
                  f'<div class="cell-sub">{ui.esc(r["role_name"])}</div>')
        c[1].html(f'<div class="cell-main">{ui.esc(r["full_name"])}</div>')
        c[2].html(ui.role_badge(r["role_status"]))
        c[3].html(f'<div class="cell-money">฿{ui.money(r["amount"])}</div>')
        c[4].html(f'<div class="cell-main">{r["due_date"]}</div>')
        c[5].html(ui.payment_badge(r["payment_status"], r["is_overdue"]))
        if r["payment_status"] == "Pending":
            if c[6].button("บันทึกจ่าย", key=f"pay_{r['payment_id']}", type="primary", width="stretch"):
                ui.do(q.mark_paid, r["payment_id"],
                      ok_msg=f"บันทึกการจ่าย {r['amount']:,.0f} บาท ให้ {r['full_name']} แล้ว")
