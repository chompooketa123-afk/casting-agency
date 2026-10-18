"""
หน้า: งานของฉัน (ฝั่งนักแสดง)

หน้านี้ดึง                      ฟังก์ชัน (queries.py)    ตาราง
  รายการบทของฉัน               roles_of_actor           ROLE JOIN PROJECT
  ทักษะที่บทต้องการ              required_skills_of_role  ROLE_SKILL JOIN SKILL
  ตารางนัดของบทนั้น              schedule_of_role         SCHEDULE
  งวดจ่ายของบทนั้น              installments_of_role     PAYMENT_INSTALLMENT
ปุ่ม 'ยอมรับงาน' / 'ปฏิเสธงาน'  respond_to_role          UPDATE ROLE (+ UPDATE PAYMENT_INSTALLMENT ถ้าปฏิเสธ)
"""
import streamlit as st

import queries as q
import ui
from config import EVENT_TYPE_LABEL

ui.page_header("งานของฉัน", "บทที่ผู้จัดงานเลือกคุณ ตอบรับหรือปฏิเสธได้ที่นี่")
actor_id = ui.actor_picker()
if not actor_id:
    st.stop()

roles = q.roles_of_actor(actor_id)
if not roles:
    st.info("ยังไม่มีผู้จัดงานเลือกคุณเข้าบทไหน")
    st.stop()

waiting = [r for r in roles if r["role_status"] == "Selected"]
if waiting:
    st.warning(f"คุณมี {len(waiting)} งานที่รอตอบรับ", icon=":material/notifications_active:")

for r in roles:
    with st.container(key=f"card_job_{r['role_id']}"):
        st.html(ui.role_head(r["role_name"], f"โปรเจกต์ {r['project_name']}  ·  ลูกค้า {r['client_name']}",
                             r["agreed_fee"], ui.role_badge(r["role_status"])))

        with st.expander("ดูรายละเอียด ตารางนัด และงวดจ่าย"):
            skills = q.required_skills_of_role(r["role_id"])
            st.html("<b>ทักษะที่บทนี้ต้องการ</b><br>" + (ui.chips(s["skill_name"] for s in skills) or "ไม่ระบุ"))
            sched = q.schedule_of_role(r["role_id"])
            for s in sched:
                s["event_type"] = EVENT_TYPE_LABEL[s["event_type"]]
            ui.table(sched, {"event_type": "ประเภท", "event_date": "วันที่",
                             "start_time": "เริ่ม", "end_time": "เลิก"})
            pay = q.installments_of_role(r["role_id"])
            ui.table(pay, {"due_date": "ครบกำหนด", "amount": "จำนวนเงิน (บาท)", "payment_status": "สถานะ"},
                     badges={"payment_status": lambda x: ui.payment_badge(x["payment_status"])})

        if r["role_status"] == "Selected":       # ตอบได้เฉพาะบทที่รอการตอบรับ
            c1, c2, _ = st.columns([1.2, 1.2, 3])
            if c1.button("ยอมรับงาน", key=f"acc_{r['role_id']}", type="primary", icon=":material/check:"):
                ui.do(q.respond_to_role, r["role_id"], actor_id, True, ok_msg="ยอมรับงานแล้ว")
            if c2.button("ปฏิเสธงาน", key=f"rej_{r['role_id']}", icon=":material/close:"):
                ui.do(q.respond_to_role, r["role_id"], actor_id, False, ok_msg="ปฏิเสธงานแล้ว")
