"""
หน้า: จัดการบท / ยกเลิกการจ้าง (ฝั่งผู้จัดงาน)

หน้านี้ดึง                     ฟังก์ชัน (queries.py)    ตาราง
  รายการบททั้งหมด              all_roles                ROLE JOIN PROJECT JOIN ACTOR
  รายละเอียดแต่ละบท             required_skills_of_role / schedule_of_role / installments_of_role
ปุ่ม 'ยกเลิกการจ้าง'            cancel_role              UPDATE ROLE + UPDATE PAYMENT_INSTALLMENT (Pending -> Cancelled)
"""
import streamlit as st

import queries as q
import ui
from config import EVENT_TYPE_LABEL

ui.page_header("จัดการบท / ยกเลิกการจ้าง", "ดูทุกบทพร้อมนักแสดงที่ถูกเลือก และยกเลิกการจ้างได้แม้ยืนยันไปแล้ว")

projects = q.list_projects()
labels = {0: "ทุกโปรเจกต์", **{p["project_id"]: f"#{p['project_id']} {p['project_name']}" for p in projects}}
pid = st.selectbox("กรองตามโปรเจกต์", list(labels), format_func=labels.get)

roles = q.all_roles(pid or None)
if not roles:
    st.info("ยังไม่มีบทในโปรเจกต์นี้")
    st.stop()

for r in roles:
    with st.container(key=f"card_role_{r['role_id']}"):
        st.html(ui.role_head(r["role_name"], f"โปรเจกต์ {r['project_name']}  ·  นักแสดง {r['full_name']} (#{r['actor_id']})",
                             r["agreed_fee"], ui.role_badge(r["role_status"])))

        with st.expander("รายละเอียด"):
            skills = q.required_skills_of_role(r["role_id"])
            st.html("<b>ทักษะที่ต้องการ</b><br>" + (ui.chips(x["skill_name"] for x in skills) or "ไม่ระบุ"))
            sched = q.schedule_of_role(r["role_id"])
            for s in sched:
                s["event_type"] = EVENT_TYPE_LABEL[s["event_type"]]
            ui.table(sched, {"event_type": "ประเภท", "event_date": "วันที่",
                             "start_time": "เริ่ม", "end_time": "เลิก"})
            pay = q.installments_of_role(r["role_id"])
            ui.table(pay, {"due_date": "ครบกำหนด", "amount": "จำนวนเงิน (บาท)", "payment_status": "สถานะ"},
                     badges={"payment_status": lambda x: ui.payment_badge(x["payment_status"])})

        if r["role_status"] in ("Selected", "Confirmed"):
            c1, c2, _ = st.columns([2.4, 1.2, 1.4], vertical_alignment="center")
            sure = c1.checkbox("ยืนยันว่าต้องการยกเลิกการจ้างบทนี้", key=f"sure_{r['role_id']}")
            if c2.button("ยกเลิกการจ้าง", key=f"cancel_{r['role_id']}", disabled=not sure, icon=":material/person_remove:"):
                ui.do(q.cancel_role, r["role_id"], ok_msg=f"ยกเลิกการจ้างบท '{r['role_name']}' แล้ว "
                                                         f"(งวดที่ยังไม่จ่ายถูกยกเลิกด้วย)")
