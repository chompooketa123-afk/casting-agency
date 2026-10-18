"""
หน้า: แคตตาล็อกนักแสดง (ทุกคนเปิดดูได้ ไม่ต้องเลือกบทบาท)

ปุ่ม/การกระทำ                  ฟังก์ชัน (queries.py)   ตารางที่ถูกแตะ
  เปิดหน้า / เปลี่ยนตัวกรอง     search_actors           SELECT ACTOR (+ ACTOR_SKILL ตามตัวกรองทักษะ)
  'ดูโปรไฟล์' (เปิดหน้าต่าง)    get_actor, get_actor_skills   SELECT ACTOR + ACTOR_SKILL + SKILL
ตัวกรองรูปลักษณ์ทั้งหมดเป็นเงื่อนไข AND ใน SQL ชุดเดียว (ดู _traits_sql ใน queries.py)
"""
import streamlit as st

import queries as q
import ui
from config import GENDER_LABEL

ui.page_header("แคตตาล็อกนักแสดงและโมเดล",
               "เลื่อนดูโปรไฟล์ทั้งหมด หรือกรองตามรูปลักษณ์และทักษะ แล้วกด 'ดูโปรไฟล์' เพื่อดูรายละเอียดเต็ม",
               eyebrow="TALENT")

skill_ids, skill_labels = ui.skill_options()
c1, c2, c3 = st.columns([1, 1.4, 2.2])
gender = c1.selectbox("เพศ", [None, *GENDER_LABEL], format_func=lambda g: "ทุกเพศ" if g is None else GENDER_LABEL[g], key="cat_gender")
text = c2.text_input("ค้นหาชื่อ / รูปลักษณ์", placeholder="เช่น ลูกครึ่ง, แว่น, ชนิดา", key="cat_text")
skills = c3.multiselect("ทักษะ (ต้องมีครบทุกข้อที่เลือก)", skill_ids, format_func=skill_labels.get,
                        placeholder="เช่น เดินแบบรันเวย์, ภาษาอังกฤษ", key="cat_skills")
traits, n_traits = ui.trait_filters("cat")

ok, rows = ui.do(q.search_actors, gender, skills, text or None, None, traits=traits, rerun=False)
if not ok:
    st.stop()

filters_on = bool(gender or text or skills or n_traits)
st.html(f'<p class="hint" style="margin:.6rem 0 1rem">พบ <b>{len(rows)}</b> คน'
        f'{" (ตามตัวกรองที่เลือก)" if filters_on else " (ทั้งหมดที่พร้อมรับงาน)"}</p>')
if not rows:
    st.html('<div class="note">ไม่พบนักแสดงที่ตรงทุกเงื่อนไข ลองลดตัวกรองบางข้อ เช่น ขยายช่วงส่วนสูงหรือเอาสีผมออก</div>')
    st.stop()

PER_ROW = 4
limit = st.session_state.setdefault("cat_limit", 12)
if filters_on:
    st.session_state["cat_limit"] = limit = max(limit, 12)
shown = rows[:limit]
with st.container(key="grid"):
    for start in range(0, len(shown), PER_ROW):
        cols = st.columns(PER_ROW)
        for col, a in zip(cols, shown[start:start + PER_ROW]):
            with col:
                with st.container(key=f"t_{a['actor_id']}"):
                    st.html(ui.talent_card(a))
                    if st.button("ดูโปรไฟล์", key=f"view_{a['actor_id']}", width="stretch"):
                        ui.show_profile(a["actor_id"])
if len(rows) > limit:
    if st.button(f"แสดงเพิ่ม (เหลืออีก {len(rows) - limit} คน)", icon=":material/expand_more:"):
        st.session_state["cat_limit"] = limit + 12
        st.rerun()
