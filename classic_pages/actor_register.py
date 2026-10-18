"""
หน้า: สมัคร / แก้โปรไฟล์ (ฝั่งนักแสดง)

ปุ่มในหน้านี้                    ฟังก์ชัน (queries.py)    ตารางที่ถูกแตะ
  'สมัครเป็นนักแสดง'            register_actor           INSERT ACTOR + INSERT ACTOR_SKILL (เผยแพร่ให้ถ้ามีทักษะ)
  'บันทึกโปรไฟล์'                update_actor             UPDATE ACTOR + DELETE/INSERT ACTOR_SKILL
รายการทักษะในแต่ละหมวด           list_skills              SELECT SKILL

ฟอร์มเก็บ "รูปลักษณ์" ครบทุกคอลัมน์ของตาราง ACTOR (ส่วนสูง น้ำหนัก สัดส่วน สีผม สีผิว สีตา ฯลฯ)
ภาพทางขวาวาดจากค่าที่กรอกแบบสดๆ (ดู art.py) เพื่อให้เห็นว่าข้อมูลรูปลักษณ์ถูกนำไปใช้ยังไง
"""
from datetime import date

import streamlit as st

import art
import queries as q
import ui
from config import (ACTOR_STATUS_LABEL, BODY_TYPE_LABEL, CLOTHING_SIZES, EXPERIENCE_LABEL, EYE_COLOR_LABEL,
                    GENDER_LABEL, HAIR_COLOR_LABEL, HAIR_LENGTH_LABEL, HAIR_TEXTURE_LABEL, PROVINCES,
                    SKIN_TONE_LABEL)

ui.page_header("สมัคร / แก้โปรไฟล์นักแสดง",
               "กรอกรูปลักษณ์และทักษะให้ครบ ผู้จัดงานจะค้นเจอคุณตรงกับงานมากขึ้น",
               eyebrow="สำหรับนักแสดงและโมเดล")


def _pick(label, labels, current, key, container=st):
    """selectbox แบบ 'ค่าในฐานข้อมูล -> ป้ายไทย' ถ้าไม่เคยมีค่าให้เลือกตัวแรก"""
    keys = list(labels)
    return container.selectbox(label, keys, index=keys.index(current) if current in keys else 0,
                               format_func=labels.get, key=key)


def profile_form(key, base=None, with_status=False):
    """วาดช่องกรอกทั้งหมด คืน (ค่าที่กรอก, dict ไว้วาดภาพตัวอย่าง)"""
    b = base or {}
    out = {}
    ui.section("ข้อมูลพื้นฐาน", no=1)
    name = st.text_input("ชื่อ-นามสกุล", value=b.get("full_name", ""), key=f"{key}_name")
    c1, c2 = st.columns(2)
    gender = c1.radio("เพศ", list(GENDER_LABEL), format_func=GENDER_LABEL.get, horizontal=True, key=f"{key}_gender",
                      index=list(GENDER_LABEL).index(b["gender"]) if b.get("gender") in GENDER_LABEL else 0)
    status = b.get("actor_status", "Active")
    if with_status:
        status = c2.radio("สถานะ", list(ACTOR_STATUS_LABEL), format_func=ACTOR_STATUS_LABEL.get, horizontal=True,
                          index=list(ACTOR_STATUS_LABEL).index(status), key=f"{key}_status",
                          help="ถ้าตั้งเป็น 'พักงาน' ระบบจะไม่เสนอชื่อคุณในการจับคู่")
    bio = st.text_area("แนะนำตัวสั้นๆ (ไม่บังคับ)", value=b.get("bio") or "", max_chars=500, key=f"{key}_bio",
                       placeholder="เช่น นางแบบสายแฟชั่นและโฆษณา ถนัดเดินรันเวย์ พูดอังกฤษได้")
    c1, c2, c3 = st.columns(3)
    out["birth_date"] = c1.date_input("วันเกิด (ต้องอายุ 18 ปีขึ้นไป)", value=b.get("birth_date") or date(2000, 1, 1),
                                      min_value=date(1940, 1, 1), max_value=date.today(), key=f"{key}_bd")
    out["province"] = _pick("จังหวัดที่อยู่", {p: p for p in PROVINCES}, b.get("province") or "กรุงเทพมหานคร", f"{key}_prov", c2)
    out["experience_level"] = _pick("ระดับประสบการณ์", EXPERIENCE_LABEL, b.get("experience_level"), f"{key}_exp", c3)
    out["can_travel"] = st.toggle("เดินทางไปถ่ายงานต่างจังหวัดได้", value=bool(b.get("can_travel")), key=f"{key}_travel")

    ui.section("รูปร่างและสัดส่วน", "ใช้ตามจริง ผู้จัดงานใช้คัดชุดและคัดคนให้ตรงบท", no=2)
    c1, c2, c3, c4 = st.columns(4)
    out["height_cm"] = c1.number_input("ส่วนสูง (ซม.)", 100, 230, int(b.get("height_cm") or 165), key=f"{key}_h")
    out["weight_kg"] = c2.number_input("น้ำหนัก (กก.)", 25.0, 250.0, float(b.get("weight_kg") or 55.0), step=0.5, key=f"{key}_w")
    out["shoe_size_eu"] = c3.number_input("เบอร์รองเท้า (EU)", 30.0, 50.0, float(b.get("shoe_size_eu") or 38.0), step=0.5, key=f"{key}_shoe")
    out["clothing_size"] = c4.selectbox("ไซซ์เสื้อ", CLOTHING_SIZES, key=f"{key}_size",
                                        index=CLOTHING_SIZES.index(b["clothing_size"]) if b.get("clothing_size") in CLOTHING_SIZES else 1)
    c1, c2, c3, c4 = st.columns(4)
    out["bust_chest_cm"] = c1.number_input("รอบอก/หน้าอก (ซม.)", 40, 200, int(b.get("bust_chest_cm") or 85), key=f"{key}_bust")
    out["waist_cm"] = c2.number_input("รอบเอว (ซม.)", 40, 200, int(b.get("waist_cm") or 65), key=f"{key}_waist")
    out["hip_cm"] = c3.number_input("รอบสะโพก (ซม.)", 40, 200, int(b.get("hip_cm") or 90), key=f"{key}_hip")
    out["body_type"] = _pick("รูปร่าง", BODY_TYPE_LABEL, b.get("body_type"), f"{key}_body", c4)

    ui.section("ลักษณะภายนอก", no=3)
    c1, c2, c3 = st.columns(3)
    out["skin_tone"] = _pick("สีผิว", SKIN_TONE_LABEL, b.get("skin_tone"), f"{key}_skin", c1)
    out["hair_color"] = _pick("สีผม", HAIR_COLOR_LABEL, b.get("hair_color"), f"{key}_hc", c2)
    out["eye_color"] = _pick("สีตา", EYE_COLOR_LABEL, b.get("eye_color"), f"{key}_eye", c3)
    c1, c2, c3, c4 = st.columns(4)
    out["hair_length"] = _pick("ความยาวผม", HAIR_LENGTH_LABEL, b.get("hair_length"), f"{key}_hl", c1)
    out["hair_texture"] = _pick("ลักษณะผม", HAIR_TEXTURE_LABEL, b.get("hair_texture"), f"{key}_ht", c2)
    out["has_tattoo"] = c3.toggle("มีรอยสัก", value=bool(b.get("has_tattoo")), key=f"{key}_tat")
    out["has_piercing"] = c4.toggle("มีเจาะ", value=bool(b.get("has_piercing")), key=f"{key}_pierce")
    appearance = st.text_area("รายละเอียดเพิ่มเติม (ข้อความอิสระ)", value=b.get("appearance_detail") or "",
                              placeholder="เช่น ใส่แว่น มีหนวดเครา ลูกครึ่ง สำเนียงเหนือ", key=f"{key}_look")

    ui.section("ทักษะและภาษา", "มีแค่ไหนติ๊กแค่นั้น อย่าเลือกที่ทำไม่ได้จริง เพราะผู้จัดงานจะจับคู่จากข้อมูลนี้", no=4)
    chosen = ui.skill_group_pickers(key, b.get("skill_ids", ()), cols=2)

    preview = {**out, "actor_id": b.get("actor_id", 0), "full_name": name or "ตัวอย่าง", "gender": gender,
               "appearance_detail": appearance}
    return {"name": name, "gender": gender, "status": status, "appearance": appearance, "bio": bio,
            "skills": chosen, "profile": out}, preview


def preview_panel(preview, title="ตัวอย่างภาพของคุณ"):
    st.html(f'<div class="tcard {art.tile_of(preview)}" style="max-width:260px"><div class="frame">'
            f'{art.avatar_svg(preview, label=False)}</div><div class="body"><div class="nm">{ui.esc(preview["full_name"])}</div>'
            f'<div class="meta">{ui.esc(ui.trait_line(preview))}</div></div></div>')
    st.caption(f"{title} วาดจากสีผิว สีผม ทรงผม รูปร่างที่เลือกไว้")


tab_new, tab_edit = st.tabs(["สมัครใหม่", "แก้ไขโปรไฟล์ที่มีอยู่"])

# ---------------------------------------------------------------------
with tab_new:
    nonce = st.session_state.setdefault("reg_nonce", 0)        # เปลี่ยนเลขนี้ = ล้างฟอร์มให้ว่างหลังสมัครสำเร็จ
    left, right = st.columns([3, 1.15], gap="large")
    with left:
        vals, preview = profile_form(f"reg{nonce}")
    with right:
        with st.container(key="card_preview"):
            preview_panel(preview)
    publish = st.toggle("เผยแพร่ให้ผู้จัดงานเห็นทันที", value=True, key=f"reg{nonce}_pub",
                        help="เผยแพร่ให้เมื่อเลือกทักษะอย่างน้อย 1 อย่าง ถ้าไม่ได้ใส่อะไรเลย คนอื่นจะไม่เห็นคุณ (ไปเพิ่มแท็กและผลงานทีหลังได้)")
    if st.button("สมัครเป็นนักแสดง", type="primary", icon=":material/person_add:"):
        ok, new_id = ui.do(q.register_actor, vals["name"], vals["gender"], vals["appearance"], vals["skills"],
                           vals["profile"], bio=vals["bio"], publish=publish, rerun=False)
        if ok:
            st.session_state["reg_nonce"] = nonce + 1
            st.session_state["current_actor_id"] = new_id
            if publish and vals["skills"]:
                ui.flash(f"สมัครสำเร็จ รหัสนักแสดงของคุณคือ #{new_id} โปรไฟล์เผยแพร่แล้ว ไปเพิ่มผลงานได้ที่ 'โปรไฟล์และผลงานของฉัน'")
            else:
                ui.flash(f"สมัครสำเร็จ รหัส #{new_id} แต่โปรไฟล์ยังซ่อนอยู่ (ยังไม่มีทักษะหรือไม่ได้เลือกเผยแพร่) "
                         "ไปที่ 'โปรไฟล์และผลงานของฉัน' เพื่อเพิ่มแท็กหรือผลงานแล้วกดเผยแพร่", "warning")
            st.rerun()

# ---------------------------------------------------------------------
with tab_edit:
    actor_id = ui.actor_picker()
    if actor_id:
        actor = q.get_actor(actor_id)                                 # SELECT ... FROM ACTOR WHERE actor_id=?
        actor["skill_ids"] = q.get_actor_skill_ids(actor_id)          # SELECT skill_id FROM ACTOR_SKILL
        with st.container(key="card_profile"):
            st.html(ui.comp_card(actor))
        left, right = st.columns([3, 1.15], gap="large")
        with left:
            vals, preview = profile_form(f"edit{actor_id}", actor, with_status=True)
        with right:
            with st.container(key="card_preview_edit"):
                preview_panel(preview, "ภาพตัวอย่างหลังบันทึก")
        if st.button("บันทึกโปรไฟล์", type="primary", icon=":material/save:"):
            was_public = bool(actor.get("is_public"))
            ok, still_public = ui.do(q.update_actor, actor_id, vals["name"], vals["gender"], vals["status"],
                                     vals["appearance"], vals["skills"], vals["profile"], bio=vals["bio"], rerun=False)
            if ok:
                if was_public and not still_public:
                    ui.flash("บันทึกแล้ว แต่ไม่เหลือทักษะและผลงานเลย ระบบจึงซ่อนโปรไฟล์ให้ ผู้จัดงานจะไม่เห็นคุณ", "warning")
                else:
                    ui.flash("บันทึกโปรไฟล์แล้ว")
                st.rerun()
