"""
หน้า: สร้างบท + จับคู่นักแสดง (ฝั่งผู้จัดงาน)  <<< หน้าสำคัญที่สุดของระบบ

ลำดับการทำงาน
  1) ผู้จัดงานกรอก ชื่อบท / ค่าตัว / ทักษะที่ต้องการ / ตารางนัด / งวดจ่าย   (ยังไม่เขียนลง DB)
  2) กด 'ค้นหานักแสดงที่เหมาะสม'
        -> find_matching_actors : SELECT เดียวที่กรอง Active + ทักษะครบ + ไม่คิวชน
        -> explain_excluded     : SELECT อธิบายว่าคนที่ถูกตัดออกเพราะอะไร
  3) กด 'เลือกคนนี้'
        -> create_role : transaction เดียว เขียน ROLE, ROLE_SKILL, SCHEDULE, PAYMENT_INSTALLMENT
           (ตรวจคิวชนซ้ำอีกรอบก่อนเขียน กันกรณีมีคนอื่นเลือกนักแสดงคนเดียวกันตัดหน้า)

ที่ ROLE ถูกเขียนตอนเลือกคนแล้วเท่านั้น เพราะ ER กำหนด ACTED_BY เป็น (1,1) คือทุกบทต้องมีนักแสดงเสมอ
"""
from datetime import date, time, timedelta

import pandas as pd
import streamlit as st

import queries as q
import ui
from config import EVENT_TYPE_LABEL, GENDER_LABEL   # noqa: F401

EVENT_FROM_TH = ui.EVENT_FROM_TH

ui.page_header("สร้างบท + จับคู่นักแสดง", "กรอกรายละเอียดบท ระบบคัดนักแสดงที่ทักษะครบและคิวไม่ชน แล้วคุณเลือกได้ 1 คน")


# ---------------------------------------------------------------------
# ขั้นที่ 0: เลือกโปรเจกต์ (เฉพาะที่ยังไม่ปิด/ยกเลิก)
# ---------------------------------------------------------------------
projects = [p for p in q.list_projects() if p["project_status"] in ("Open", "In_Progress")]
if not projects:
    st.warning("ยังไม่มีโปรเจกต์ที่เปิดอยู่ ไปสร้างที่หน้า 'โปรเจกต์' ก่อน", icon=":material/warning:")
    st.stop()
proj_labels = {p["project_id"]: f"#{p['project_id']} {p['project_name']} (ลูกค้า: {p['client_name']})"
               for p in projects}
project_id = st.selectbox("โปรเจกต์", list(proj_labels), format_func=proj_labels.get)

# ---------------------------------------------------------------------
# ขั้นที่ 1: รายละเอียดบท
# ---------------------------------------------------------------------
ui.section("รายละเอียดบท", no=1)
c1, c2 = st.columns(2)
role_name = c1.text_input("ชื่อบท", placeholder="เช่น นางเอก, พรีเซนเตอร์")
fee = c2.number_input("ค่าตัวที่ตกลง (บาท)", min_value=0.0, value=50000.0, step=1000.0)
skill_ids, skill_labels = ui.skill_options()
st.markdown("**ทักษะที่บทนี้ต้องการ** (ต้องมีครบทุกข้อที่เลือก  ·  ไม่เลือกเลย = ไม่ระบุทักษะ เช่น ตัวประกอบ)")
need_skills = ui.skill_group_pickers("need")
gender_filter = st.selectbox(
    "ตัวกรองเพิ่มเติม: เพศ (ไม่บังคับ ใช้กรองรายชื่อตอนค้นหาเท่านั้น ไม่ได้เก็บลงบท)",
    [None, *GENDER_LABEL], format_func=lambda g: "ไม่กรอง" if g is None else GENDER_LABEL[g])
traits, n_traits = ui.trait_filters("cast")     # ตัวกรองรูปลักษณ์ (ส่วนสูง สีผม ฯลฯ) ใช้กรองรายชื่อตอนค้นหาเท่านั้น

# ---------------------------------------------------------------------
# ขั้นที่ 2-3: ตารางนัด และ งวดจ่าย (ตารางที่เพิ่ม/ลบแถวได้)
# ---------------------------------------------------------------------
ui.section("ตารางนัดหมายของบทนี้", no=2)
st.caption("กดแถวล่างสุดที่ว่างเพื่อเพิ่มนัด เลือกแถวแล้วกด Delete เพื่อลบ  (บทหนึ่งมีนัดกี่ช่วงก็ได้ หรือไม่มีเลยก็ได้)")
default_sched = pd.DataFrame([{
    "ประเภท": "ถ่ายทำ", "วันที่": date.today() + timedelta(days=7), "เริ่ม": time(9, 0), "เลิก": time(17, 0)}])
sched_df = st.data_editor(
    default_sched, num_rows="dynamic", key="sched_editor", width="stretch", hide_index=True,
    column_config={
        "ประเภท": st.column_config.SelectboxColumn(options=list(EVENT_FROM_TH), required=True),
        "วันที่": st.column_config.DateColumn(format="YYYY-MM-DD", required=True),
        "เริ่ม": st.column_config.TimeColumn(format="HH:mm", step=900, required=True),
        "เลิก": st.column_config.TimeColumn(format="HH:mm", step=900, required=True),
    })

ui.section("งวดจ่ายเงิน", "ยอดรวมทุกงวดต้องเท่ากับค่าตัว", no=3)
default_pay = pd.DataFrame([
    {"ครบกำหนดจ่าย": date.today() + timedelta(days=14), "จำนวนเงิน": 25000.0},
    {"ครบกำหนดจ่าย": date.today() + timedelta(days=30), "จำนวนเงิน": 25000.0}])
pay_df = st.data_editor(
    default_pay, num_rows="dynamic", key="pay_editor", width="stretch", hide_index=True,
    column_config={
        "ครบกำหนดจ่าย": st.column_config.DateColumn(format="YYYY-MM-DD", required=True),
        "จำนวนเงิน": st.column_config.NumberColumn(min_value=0.0, step=1000.0, format="%.2f", required=True),
    })
paid_sum = float(pd.to_numeric(pay_df["จำนวนเงิน"], errors="coerce").fillna(0).sum())
if abs(paid_sum - fee) < 0.005:
    st.success(f"ยอดรวมงวด {paid_sum:,.2f} เท่ากับค่าตัว {fee:,.2f}", icon=":material/check_circle:")
else:
    st.warning(f"ยอดรวมงวด {paid_sum:,.2f} ยังไม่เท่ากับค่าตัว {fee:,.2f}", icon=":material/warning:")

# ---------------------------------------------------------------------
# ขั้นที่ 4: ค้นหา
# ---------------------------------------------------------------------
ui.section("ค้นหานักแสดงที่เหมาะสม", no=4)
if st.button("ค้นหานักแสดงที่เหมาะสม", type="primary", icon=":material/search:"):
    try:
        if not role_name.strip():
            raise q.BusinessError("กรุณากรอกชื่อบท")
        slots = ui.parse_slots(sched_df)
        installments = ui.parse_installments(pay_df)
        q.validate_slots(slots)
        q.validate_installments(installments, fee)
        eligible = q.find_matching_actors(need_skills, slots, gender_filter, traits)            # SELECT จับคู่
        excluded = q.explain_excluded(need_skills, slots, [a["actor_id"] for a in eligible], gender_filter, traits)
    except q.BusinessError as e:
        st.error(str(e), icon=":material/block:")
        st.session_state.pop("match", None)
    else:
        # เก็บ "ภาพถ่ายของฟอร์ม ณ ตอนค้นหา" ไว้ เพื่อให้ปุ่ม 'เลือกคนนี้' ใช้ข้อมูลชุดเดียวกับที่คัดรายชื่อมา
        st.session_state["match"] = {
            "project_id": project_id, "role_name": role_name.strip(), "fee": fee, "skills": list(need_skills),
            "gender": gender_filter, "traits": traits, "slots": slots, "installments": installments,
            "eligible": eligible, "excluded": excluded}

match = st.session_state.get("match")
if match:
    st.divider()
    skills_text = ", ".join(skill_labels[s] for s in match["skills"]) or "ไม่ระบุ"
    slots_text = " | ".join(ui.slot_text(s) for s in match["slots"]) or "ไม่มีนัด"
    ui.section(f"ผลค้นหาสำหรับบท {match['role_name']}", f"โปรเจกต์ #{match['project_id']}")
    st.html(f'<div class="note"><b>ทักษะที่ต้องมี</b> {ui.esc(skills_text)}<br>'
            f'<b>ช่วงเวลา</b> {ui.esc(slots_text)}</div>')

    with st.expander("ดู query ที่ใช้จับคู่ (SQL)", icon=":material/code:"):
        sql, params = q._build_match_sql(match["skills"], match["slots"], match["gender"], match["traits"])
        st.code(sql, language="sql")
        st.caption(f"พารามิเตอร์ที่ใส่แทน %s ตามลำดับ: {params}")

    tab_ok, tab_no = st.tabs([f"ผ่านเกณฑ์ ({len(match['eligible'])})",
                              f"ถูกตัดออก ({len(match['excluded'])})"])
    with tab_ok:
        if not match["eligible"]:
            st.warning("ไม่มีนักแสดงที่ผ่านทุกเงื่อนไข ลองลดทักษะที่ต้องการ หรือเปลี่ยนช่วงเวลา (ดูเหตุผลที่แท็บถัดไป)",
                       icon=":material/warning:")
        for a in match["eligible"]:
            with st.container(key=f"card_pick_{a['actor_id']}"):
                left, right = st.columns([5, 1.4], vertical_alignment="center")
                left.html(ui.comp_card(a))
                if right.button("เลือกคนนี้", key=f"pick_{a['actor_id']}", type="primary", width="stretch"):
                    ok, _ = ui.do(
                        q.create_role, match["project_id"], match["role_name"], match["fee"], a["actor_id"],
                        match["skills"], match["slots"], match["installments"], rerun=False)
                    if ok:
                        st.session_state.pop("match", None)
                        ui.flash(f"สร้างบท '{match['role_name']}' และเลือก {a['full_name']} แล้ว "
                                 f"สถานะ: รอนักแสดงตอบรับ")
                        st.rerun()
    with tab_no:
        rows = [{"actor_id": r["actor_id"], "full_name": r["full_name"], "reason": " / ".join(r["reasons"])}
                for r in match["excluded"]]
        ui.table(rows, {"actor_id": "รหัส", "full_name": "ชื่อ", "reason": "เหตุผลที่ถูกตัดออก"})

    if st.button("ล้างผลการค้นหา", icon=":material/restart_alt:"):
        st.session_state.pop("match", None)
        st.rerun()
