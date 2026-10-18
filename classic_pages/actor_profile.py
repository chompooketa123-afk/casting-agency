"""
หน้า: โปรไฟล์และผลงานของฉัน (ฝั่งนักแสดง)

นักแสดงใส่ชื่อ แท็กทักษะ และผลงานของตัวเองที่นี่ แล้วกด 'เผยแพร่โปรไฟล์' เพื่อให้ผู้จัดงานเห็นตอนเลือกนักแสดง
กฎ: ถ้ายังไม่ได้ใส่อะไรเลย (ไม่มีทักษะและไม่มีผลงาน) จะเผยแพร่ไม่ได้ และคนอื่นจะไม่เห็นเรา

ปุ่มในหน้านี้                    ฟังก์ชัน (queries.py)    ตารางที่ถูกแตะ
  'เผยแพร่โปรไฟล์' / 'ซ่อนโปรไฟล์'  set_profile_public      UPDATE ACTOR.is_public (เช็กจาก ACTOR_SKILL + PORTFOLIO)
  'บันทึกชื่อและแท็ก'              update_actor            UPDATE ACTOR + DELETE/INSERT ACTOR_SKILL
  'เพิ่มผลงาน'                    add_work                INSERT PORTFOLIO
  'บันทึกการแก้ไข' (ผลงาน)         update_work             UPDATE PORTFOLIO
  'ลบผลงานนี้'                    delete_work             DELETE PORTFOLIO (ถ้าไม่เหลืออะไรเลย ระบบปิดโปรไฟล์ให้เอง)
"""
from datetime import date

import streamlit as st

import queries as q
import ui
from config import MAX_WORKS, WORK_TYPE_LABEL

ui.page_header("โปรไฟล์และผลงานของฉัน",
               "ใส่ชื่อ แท็กทักษะ และผลงาน แล้วกดเผยแพร่ ผู้จัดงานจะเห็นคุณตอนเลือกนักแสดง",
               eyebrow="สำหรับนักแสดงและโมเดล")

actor_id = ui.actor_picker()
if not actor_id:
    st.stop()
actor = q.get_actor(actor_id)                    # SELECT ... FROM ACTOR
ready = q.profile_readiness(actor_id)            # นับทักษะ (ACTOR_SKILL) และผลงาน (PORTFOLIO)

# ---------------------------------------------------------------------
# สถานะการมองเห็น + ปุ่มเผยแพร่/ซ่อน
# ---------------------------------------------------------------------
ui.visibility_panel(ready)
if ready["is_public"]:
    if st.button("ซ่อนโปรไฟล์ (ไม่ให้ใครเห็น)", icon=":material/visibility_off:"):
        ui.do(q.set_profile_public, actor_id, False, ok_msg="ซ่อนโปรไฟล์แล้ว ผู้จัดงานจะไม่เห็นคุณจนกว่าจะเผยแพร่อีกครั้ง")
else:
    if st.button("เผยแพร่โปรไฟล์", type="primary", icon=":material/visibility:", disabled=not ready["ready"],
                 help=None if ready["ready"] else "ต้องมีแท็กทักษะหรือผลงานอย่างน้อย 1 อย่างก่อน"):
        ui.do(q.set_profile_public, actor_id, True, ok_msg="เผยแพร่แล้ว ผู้จัดงานเห็นคุณในแคตตาล็อกและผลจับคู่ได้เลย")

tab_info, tab_works, tab_view = st.tabs(["ข้อมูลและแท็ก", "ผลงาน", "ตัวอย่างที่ผู้จัดงานเห็น"])

# ---------------------------------------------------------------------
# แท็บ 1 : ชื่อ + แนะนำตัว + แท็กทักษะ
# ---------------------------------------------------------------------
with tab_info:
    k = f"pf{actor_id}"
    name = st.text_input("ชื่อที่แสดง", value=actor["full_name"], key=f"{k}_name")
    bio = st.text_area("แนะนำตัวสั้นๆ", value=actor.get("bio") or "", max_chars=500, key=f"{k}_bio",
                       placeholder="เช่น นางแบบสายแฟชั่นและโฆษณา ถนัดเดินรันเวย์ พูดอังกฤษได้ พร้อมเดินทางทั่วประเทศ")
    ui.section("แท็กทักษะ", "เลือกเฉพาะที่ทำได้จริง ผู้จัดงานจะค้นและจับคู่จากแท็กเหล่านี้")
    chosen = ui.skill_group_pickers(k, q.get_actor_skill_ids(actor_id), cols=2)
    if st.button("บันทึกชื่อและแท็ก", type="primary", icon=":material/save:"):
        was_public = ready["is_public"]
        ok, still_public = ui.do(q.update_actor, actor_id, name, actor["gender"], actor["actor_status"],
                                 actor["appearance_detail"], chosen, bio=bio, rerun=False)
        if ok:
            if was_public and not still_public:
                ui.flash("บันทึกแล้ว แต่ไม่เหลือแท็กและผลงานเลย ระบบจึงซ่อนโปรไฟล์ให้ ผู้จัดงานจะไม่เห็นคุณ", "warning")
            else:
                ui.flash("บันทึกชื่อและแท็กแล้ว")
            st.rerun()
    st.caption("อยากแก้ส่วนสูง สัดส่วน สีผม และรูปลักษณ์อื่นๆ ไปที่เมนู 'สมัคร / แก้โปรไฟล์' แท็บ 'แก้ไขโปรไฟล์ที่มีอยู่'")


# ---------------------------------------------------------------------
# แท็บ 2 : ผลงาน (เพิ่ม / แก้ / ลบ)
# ---------------------------------------------------------------------
def work_fields(key, w=None):
    """ช่องกรอกผลงาน (ใช้ทั้งตอนเพิ่มและตอนแก้) คืน (ชื่อ, ประเภท, บท, ปี, รายละเอียด, ลิงก์)"""
    w = w or {}
    types = list(WORK_TYPE_LABEL)
    title = st.text_input("ชื่อผลงาน", value=w.get("title", ""), max_chars=150, key=f"{key}_t")
    c1, c2, c3 = st.columns([1.3, 1.2, .8])
    wtype = c1.selectbox("ประเภท", types, format_func=WORK_TYPE_LABEL.get, key=f"{key}_ty",
                         index=types.index(w["work_type"]) if w.get("work_type") in types else 0)
    role = c2.text_input("บทบาทของคุณ", value=w.get("role_played") or "", max_chars=100, key=f"{key}_r",
                         placeholder="เช่น นำหญิง, โมเดลรันเวย์")
    year = c3.number_input("ปี", 1980, date.today().year + 1, int(w.get("work_year") or date.today().year), key=f"{key}_y")
    desc = st.text_area("รายละเอียด (ไม่บังคับ)", value=w.get("description") or "", max_chars=500, height=90, key=f"{key}_d")
    link = st.text_input("ลิงก์ดูผลงาน (ไม่บังคับ)", value=w.get("link_url") or "", max_chars=300, key=f"{key}_l",
                         placeholder="https://...")
    return title, wtype, role, year, desc, link


with tab_works:
    works = q.list_works(actor_id)                               # SELECT ... FROM PORTFOLIO
    ui.section("เพิ่มผลงาน", f"ลงได้สูงสุด {MAX_WORKS} ชิ้น  ตอนนี้มี {len(works)} ชิ้น")
    nonce = st.session_state.setdefault(f"wk_nonce_{actor_id}", 0)      # เปลี่ยนเลข = ล้างช่องกรอกหลังเพิ่มสำเร็จ
    with st.container(key=f"card_addwork_{actor_id}"):
        vals = work_fields(f"addw{actor_id}_{nonce}")
        if st.button("เพิ่มผลงาน", type="primary", icon=":material/add_circle:", disabled=len(works) >= MAX_WORKS):
            ok, _ = ui.do(q.add_work, actor_id, *vals, rerun=False)
            if ok:
                st.session_state[f"wk_nonce_{actor_id}"] = nonce + 1
                ui.flash("เพิ่มผลงานแล้ว")
                st.rerun()

    ui.section("ผลงานของฉัน")
    if not works:
        st.html('<div class="note">ยังไม่มีผลงาน ถ้าเพิ่งเริ่มก็ไม่เป็นไร ติ๊กแท็กทักษะอย่างเดียวก็เผยแพร่ได้</div>')
    for w in works:
        with st.container(key=f"workcard_{w['work_id']}"):
            st.html(ui.work_html(w))
            with st.expander("แก้ไขผลงานนี้", icon=":material/edit:"):
                new = work_fields(f"ew{w['work_id']}", w)
                if st.button("บันทึกการแก้ไข", key=f"save_w{w['work_id']}", icon=":material/save:"):
                    ui.do(q.update_work, actor_id, w["work_id"], *new, ok_msg="แก้ไขผลงานแล้ว")
            if st.button("ลบผลงานนี้", key=f"del_w{w['work_id']}", icon=":material/delete:"):
                ok, still_public = ui.do(q.delete_work, actor_id, w["work_id"], rerun=False)
                if ok:
                    if ready["is_public"] and not still_public:
                        ui.flash("ลบแล้ว แต่ไม่เหลือแท็กและผลงานเลย ระบบจึงซ่อนโปรไฟล์ให้", "warning")
                    else:
                        ui.flash("ลบผลงานแล้ว")
                    st.rerun()

# ---------------------------------------------------------------------
# แท็บ 3 : ตัวอย่างหน้าโปรไฟล์ที่ผู้จัดงานเห็น
# ---------------------------------------------------------------------
with tab_view:
    if ready["is_public"]:
        st.html('<p class="hint">นี่คือหน้าต่างที่ผู้จัดงานเห็นเมื่อกด \'ดูโปรไฟล์\' ในแคตตาล็อก</p>')
    else:
        st.html('<div class="note">ตอนนี้โปรไฟล์ยังซ่อนอยู่ ผู้จัดงานจะไม่เห็นหน้านี้ นี่คือตัวอย่างว่าจะเห็นอะไรเมื่อเผยแพร่</div>')
    st.html(ui.profile_html(actor, q.get_actor_skills(actor_id), q.list_works(actor_id)))
