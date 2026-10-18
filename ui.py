"""
ui.py : ตัวช่วยหน้าตาที่ใช้ร่วมกันทุกหน้า (ไม่มี SQL ในไฟล์นี้ ยกเว้นดึงรายชื่อนักแสดงมาทำ dropdown)
"""
from datetime import date, datetime, time
from decimal import Decimal
from html import escape as esc
from pathlib import Path

import altair as alt
import mysql.connector
import pandas as pd
import streamlit as st

import db
import queries as q
import art
from config import (ACTOR_STATUS_LABEL, BODY_TYPE_LABEL, EVENT_TYPE_LABEL, EXPERIENCE_LABEL, EYE_COLOR_LABEL,
                    GENDER_LABEL, HAIR_COLOR_LABEL, HAIR_LENGTH_LABEL, HAIR_TEXTURE_LABEL, PAYMENT_STATUS_LABEL,
                    PROJECT_STATUS_LABEL, PROVINCES, ROLE_STATUS_LABEL, SKILL_TYPE_LABEL, SKILL_TYPES,
                    SKIN_TONE_LABEL, WORK_TYPE_LABEL)


# ---------------------------------------------------------------------
# ข้อความแจ้งผลหลังกดปุ่ม (flash message)
# Streamlit รันสคริปต์ใหม่ทุกครั้งที่กดปุ่ม ข้อความที่แสดงก่อน st.rerun() จะหาย
# จึงเก็บข้อความไว้ใน session_state แล้วค่อยแสดงตอนรันรอบถัดไป
# ---------------------------------------------------------------------
def flash(message, kind="success"):
    st.session_state["_flash"] = (kind, message)


def show_flash():
    item = st.session_state.pop("_flash", None)
    if item:
        kind, message = item
        message = message.lstrip("✅⛔ ")       # กล่องแจ้งผลมีไอคอนของตัวเองอยู่แล้ว
        icons = {"success": ":material/check_circle:", "error": ":material/block:", "warning": ":material/warning:"}
        {"success": st.success, "error": st.error, "warning": st.warning}.get(kind, st.info)(
            message, icon=icons.get(kind))


def do(fn, *args, ok_msg=None, rerun=True, **kwargs):
    """เรียกฟังก์ชันใน queries.py แบบปลอดภัย
    - ผิดกฎของระบบ (BusinessError) -> โชว์กล่องสีแดง ไม่ให้โปรแกรมพัง
    - สำเร็จ -> จดข้อความ แล้ว rerun เพื่อรีเฟรชหน้า
    คืน (สำเร็จไหม, ค่าที่ฟังก์ชันคืน)"""
    try:
        result = fn(*args, **kwargs)
    except q.BusinessError as e:
        st.error(str(e), icon=":material/block:")
        return False, None
    except mysql.connector.Error as e:
        st.error(f"ฐานข้อมูลปฏิเสธคำสั่งนี้: {e}")
        return False, None
    if ok_msg:
        flash(ok_msg)
    if rerun:
        st.rerun()
    return True, result


# ---------------------------------------------------------------------
# เลือกว่า "ฉันคือนักแสดงคนไหน" (ER ไม่มีตารางผู้ใช้/รหัสผ่าน เลยไม่ทำ login)
# ---------------------------------------------------------------------
def actor_label(a):
    mark = "" if a["actor_status"] == "Active" else " [พักงาน]"
    if not a.get("is_public"):
        mark += " [ยังไม่เผยแพร่]"
    return f"{a['full_name']} (#{a['actor_id']}){mark}"


def actor_picker():
    """วาง dropdown เลือกนักแสดงไว้ที่หัวหน้า คืน actor_id (หรือ None ถ้ายังไม่มีนักแสดงในระบบ)"""
    actors = q.list_actors()
    if not actors:
        st.warning("ยังไม่มีนักแสดงในระบบ ไปที่หน้า 'สมัคร / แก้โปรไฟล์' ก่อน")
        return None
    labels = {a["actor_id"]: actor_label(a) for a in actors}
    ids = list(labels)
    saved = st.session_state.get("current_actor_id")
    index = ids.index(saved) if saved in ids else 0
    chosen = st.selectbox(
        "คุณคือนักแสดงคนไหน?", ids, index=index, format_func=labels.get, key="actor_picker_widget",
        help="ER ไม่มีตารางผู้ใช้/รหัสผ่าน จึงไม่ทำระบบ login ให้เลือกชื่อตัวเองแทน")
    st.session_state["current_actor_id"] = chosen   # จำไว้ตอนสลับไปหน้าอื่น
    return chosen


# ---------------------------------------------------------------------
# ธีมและชิ้นส่วนหน้าตา (HTML ล้วน ไม่มี SQL)
# ทุกข้อความที่มาจากฐานข้อมูลผ่าน esc() ก่อนใส่ HTML เสมอ (กันตัวอักษร < > แตกหน้า)
# ---------------------------------------------------------------------
_CSS_FILE = Path(__file__).parent / "theme.css"


def inject_theme():
    """ฝัง theme.css ลงหน้าเว็บ (เรียกครั้งเดียวใน app.py)"""
    st.html('<style class="cs-theme">' + _CSS_FILE.read_text(encoding="utf-8") + "</style>")


def page_header(title, subtitle=None, eyebrow=None):
    sub = f"<p>{esc(subtitle)}</p>" if subtitle else ""
    eb = f'<div class="eyebrow">{art.sparkle_svg(12)}{esc(eyebrow)}</div>' if eyebrow else ""
    st.html(f'<header class="pg-head">{eb}<h1>{esc(title)}</h1>{sub}</header>')


def section(title, note=None, no=None):
    """หัวข้อย่อย  no = เลขขั้นตอน (ใช้เฉพาะที่เป็นลำดับขั้นจริงๆ)"""
    badge_no = f'<span class="no">{no}</span>' if no else ""
    note_html = f"<p>{esc(note)}</p>" if note else ""
    st.html(f'<div class="sec">{badge_no}<h2>{esc(title)}</h2>{note_html}</div>')


def stat_row(items):
    """items = [(ชื่อ, ค่า, หมายเหตุ หรือ None, โทน 'ok'/'bad'/None), ...]"""
    cells = []
    for item in items:
        label, value, note, tone = (list(item) + [None, None])[:4]
        cells.append(f'<div class="stat {tone or ""}"><div class="l">{esc(str(label))}</div>'
                     f'<div class="v">{esc(str(value))}</div>'
                     + (f'<div class="n">{esc(str(note))}</div>' if note else "") + "</div>")
    st.html(f'<div class="stats">{"".join(cells)}</div>')


def badge(text, tone):
    return f'<span class="badge b-{tone}">{esc(text)}</span>'


ROLE_TONE = {"Selected": "wait", "Confirmed": "ok", "Rejected_by_Actor": "bad", "Cancelled_by_Organizer": "off"}
PAYMENT_TONE = {"Pending": "wait", "Paid": "ok", "Cancelled": "off"}
PROJECT_TONE = {"Open": "ok", "In_Progress": "info", "Completed": "off", "Cancelled": "off"}
ACTOR_TONE = {"Active": "ok", "Inactive": "off"}


def role_badge(code):
    return badge(ROLE_STATUS_LABEL[code], ROLE_TONE[code])


def payment_badge(code, overdue=False):
    if overdue:                                   # "เลยกำหนด" คำนวณตอน query ไม่ได้เก็บเป็นสถานะ
        return badge("เลยกำหนดจ่าย", "bad")
    return badge(PAYMENT_STATUS_LABEL[code], PAYMENT_TONE[code])


def project_badge(code):
    return badge(PROJECT_STATUS_LABEL[code], PROJECT_TONE[code])


def actor_badge(code):
    return badge(ACTOR_STATUS_LABEL[code], ACTOR_TONE[code])


def chips(items):
    return "".join(f'<span class="chip">{esc(i)}</span>' for i in items if i)


def money(x):
    return f"{x:,.0f}"


def initial(name):
    """ตัวอักษรในวงกลมของ comp card (ข้ามสระนำ เ แ โ ใ ไ ของชื่อไทย)"""
    for ch in (name or "").strip():
        if ch not in "เแโใไ":
            return ch.upper()
    return "?"


def trait_line(a):
    """สรุปรูปลักษณ์สั้นๆ เช่น 'ผมดำยาว · รูปร่างเพรียว' (ใช้ในการ์ด)"""
    bits = []
    if a.get("hair_color"):
        hair = HAIR_COLOR_LABEL.get(a["hair_color"], "")
        if a.get("hair_length"):
            hair += HAIR_LENGTH_LABEL.get(a["hair_length"], "")
        bits.append("ผม" + hair)
    if a.get("body_type"):
        bits.append(BODY_TYPE_LABEL.get(a["body_type"], ""))
    return " · ".join(b for b in bits if b)


def _vital_meta(a):
    parts = []
    if a.get("age") is not None:
        parts.append(f"{a['age']} ปี")
    if a.get("height_cm"):
        parts.append(f"{a['height_cm']} ซม.")
    if a.get("province"):
        parts.append(a["province"])
    return " · ".join(parts)


def talent_card(a, tag_html=""):
    """การ์ดนักแสดงสีพาสเทลพร้อมภาพประกอบ (a = แถวจาก queries ที่ดึงด้วย _ACTOR_COLS)"""
    off = "" if a.get("actor_status", "Active") == "Active" else " off"
    skills = [x for x in (a.get("skills") or "").split(", ") if x and x != "-"]
    shown = chips_soft(skills[:2]) + (f'<span class="chip soft">+{len(skills) - 2}</span>' if len(skills) > 2 else "")
    tag_cls = "tag"
    if not tag_html and a.get("n_works"):
        tag_html, tag_cls = f'<span class="badge b-works">{a["n_works"]} ผลงาน</span>', "tag low"   # มุมล่าง: มุมบนโดนขอบโค้งของกรอบตัดจนอ่านไม่ออก
    tag = f'<div class="{tag_cls}">{tag_html}</div>' if tag_html else ""
    return (
        f'<div class="tcard {art.tile_of(a)}{off}">'
        f'<div class="frame">{art.avatar_svg(a, label=False)}{tag}</div>'
        '<div class="body">'
        f'<div class="nm">{esc(a["full_name"])}</div>'
        f'<div class="meta">{esc(_vital_meta(a) or gender_th(a["gender"]))}<br>{esc(trait_line(a))}</div>'
        f'{shown}</div></div>')


def chips_soft(items):
    return "".join(f'<span class="chip soft">{esc(i)}</span>' for i in items if i)


def comp_card(a):
    """comp card นักแสดง 1 คนในผลจับคู่ (a = แถวจาก find_matching_actors)"""
    skills = [x for x in (a.get("skills") or "").split(", ") if x and x != "-"]
    skill_html = chips(skills) or '<span class="meta">ยังไม่ระบุทักษะ</span>'
    tile = (f'<div class="tcard {art.tile_of(a)}"><div class="frame">'
            f'{art.avatar_svg(a, label=False)}</div></div>')
    return (
        '<div class="comp">' + tile +
        '<div class="info">'
        f'<div class="nm">{esc(a["full_name"])}</div>'
        f'<div class="meta">{esc(gender_th(a["gender"]))} · {esc(_vital_meta(a) or "ยังไม่ระบุรูปร่าง")} '
        f'· รหัส <b>#{a["actor_id"]}</b></div>'
        f'<div class="meta">{esc(trait_line(a))}</div>'
        f'{skill_html}'
        f'<div class="look">{esc(a.get("appearance_detail") or "ไม่ระบุรูปลักษณ์")}</div>'
        '</div></div>')


def work_html(w):
    """ผลงาน 1 ชิ้น (ข้อความทุกช่องผ่าน esc; ลิงก์รับเฉพาะ http/https ซึ่ง queries.py ตรวจไว้ตอนบันทึกแล้ว)"""
    meta = " · ".join(x for x in [WORK_TYPE_LABEL.get(w["work_type"], ""), w.get("role_played") or ""] if x)
    desc = f'<p>{esc(w["description"])}</p>' if w.get("description") else ""
    url = w.get("link_url") or ""
    link = (f'<a class="wlink" href="{esc(url, quote=True)}" target="_blank" rel="noopener noreferrer">ดูผลงาน ↗</a>'
            if url.lower().startswith(("http://", "https://")) else "")
    return (f'<div class="work"><div class="yr">{esc(str(w["work_year"]))}</div><div class="wb">'
            f'<h4>{esc(w["title"])}</h4><div class="wm">{esc(meta)}</div>{desc}{link}</div></div>')


def works_html(works):
    if not works:
        return '<span class="meta">ยังไม่มีผลงานที่ลงไว้</span>'
    return '<div class="works">' + "".join(work_html(w) for w in works) + "</div>"


def profile_html(a, grouped, works=()):
    """หน้าโปรไฟล์เต็ม (ใน dialog) : ภาพ + แนะนำตัว + สัดส่วน + ลักษณะ + ทักษะแยกหมวด + ผลงาน"""
    def v(label, val, unit=""):
        if val in (None, ""):
            return ""
        return f'<div><span>{esc(label)}</span><b>{esc(str(val))}</b><small>{esc(unit)}</small></div>'
    vit = "".join([
        v("อายุ", a.get("age"), "ปี"), v("ส่วนสูง", a.get("height_cm"), "ซม."), v("น้ำหนัก", a.get("weight_kg") and f"{a['weight_kg']:g}", "กก."),
        v("รอบอก/หน้าอก", a.get("bust_chest_cm"), "ซม."), v("รอบเอว", a.get("waist_cm"), "ซม."), v("รอบสะโพก", a.get("hip_cm"), "ซม."),
        v("เบอร์รองเท้า", a.get("shoe_size_eu") and f"{a['shoe_size_eu']:g}", "EU"), v("ไซซ์เสื้อ", a.get("clothing_size")),
    ])
    look = "".join(chips_soft([
        BODY_TYPE_LABEL.get(a.get("body_type"), ""), "ผิว" + SKIN_TONE_LABEL.get(a.get("skin_tone"), "") if a.get("skin_tone") else "",
        ("ผม" + HAIR_COLOR_LABEL.get(a.get("hair_color"), "")) if a.get("hair_color") else "",
        HAIR_LENGTH_LABEL.get(a.get("hair_length"), ""), HAIR_TEXTURE_LABEL.get(a.get("hair_texture"), ""),
        ("ตา" + EYE_COLOR_LABEL.get(a.get("eye_color"), "")) if a.get("eye_color") else "",
        "มีรอยสัก" if a.get("has_tattoo") else "", "มีเจาะ" if a.get("has_piercing") else "",
    ]))
    groups = "".join(
        f'<div class="skillgroup"><h5>{esc(SKILL_TYPE_LABEL[t])}</h5>{chips(grouped[t])}</div>'
        for t in SKILL_TYPES if grouped.get(t)) or '<span class="meta">ยังไม่ระบุทักษะ</span>'
    extra = " · ".join(x for x in [
        EXPERIENCE_LABEL.get(a.get("experience_level"), ""), a.get("province") or "",
        "พร้อมเดินทางต่างจังหวัด" if a.get("can_travel") else "ไม่สะดวกเดินทางต่างจังหวัด"] if x)
    return (
        '<div class="comp">'
        f'<div class="tcard {art.tile_of(a)}"><div class="frame">{art.avatar_svg(a, label=False)}</div></div>'
        '<div class="info">'
        f'<div class="nm">{esc(a["full_name"])}</div>'
        f'<div class="meta">{esc(gender_th(a["gender"]))} · {actor_badge(a["actor_status"])} · รหัส <b>#{a["actor_id"]}</b></div>'
        f'<div class="meta">{esc(extra)}</div>'
        + (f'<div class="bio">{esc(a["bio"])}</div>' if a.get("bio") else "") +
        f'<div class="vitals">{vit}</div>{look}'
        f'<div class="look">{esc(a.get("appearance_detail") or "")}</div>'
        f'</div></div><div class="sec" style="margin-bottom:.2rem"><h2 style="font-size:1.2rem">ทักษะ</h2></div>{groups}'
        f'<div class="sec" style="margin-bottom:.4rem"><h2 style="font-size:1.2rem">ผลงาน</h2></div>{works_html(works)}')


def visibility_panel(r):
    """แผงบอกสถานะโปรไฟล์ของฉัน (r = ผลจาก q.profile_readiness) : คนอื่นเห็นอยู่ไหม + เช็กลิสต์ว่าใส่อะไรแล้วบ้าง"""
    if r["is_public"]:
        cls, icon = "on", art.eye_svg(False, "#2F6F57")
        title, text = "โปรไฟล์ของคุณเผยแพร่อยู่", "ผู้จัดงานเห็นคุณในแคตตาล็อก ผลค้นหา และผลจับคู่นักแสดง"
    else:
        cls, icon = "", art.eye_svg(True, "#6E6468")
        title = "ซ่อนอยู่ ผู้จัดงานยังไม่เห็นคุณ"
        text = ("ข้อมูลพร้อมแล้ว กดปุ่ม 'เผยแพร่โปรไฟล์' เพื่อให้ผู้จัดงานเห็นคุณตอนเลือกนักแสดง" if r["ready"] else
                "ยังไม่ได้ใส่แท็กทักษะหรือผลงานเลย ใส่อย่างน้อย 1 อย่าง แล้วจึงเผยแพร่ได้ ถ้าไม่ได้ใส่อะไร คนอื่นจะไม่เห็นคุณ")

    def chk(done, label):
        return f'<span class="{"done" if done else ""}">{"✓" if done else "○"} {esc(label)}</span>'
    checks = "".join([chk(r["has_name"], "ชื่อ"), chk(r["n_skills"] > 0, f"แท็กทักษะ {r['n_skills']} อย่าง"),
                      chk(r["n_works"] > 0, f"ผลงาน {r['n_works']} ชิ้น"), chk(r["has_bio"], "แนะนำตัว (ไม่บังคับ)")])
    st.html(f'<div class="vis {cls}"><div class="ic">{icon}</div><div><h3>{esc(title)}</h3><p>{esc(text)}</p></div></div>'
            f'<div class="checks">{checks}</div>')


@st.dialog("โปรไฟล์นักแสดง", width="large")
def show_profile(actor_id):
    """หน้าต่างโปรไฟล์ (ปุ่ม 'ดูโปรไฟล์' ในหน้าแคตตาล็อก) : SELECT ACTOR + ACTOR_SKILL + PORTFOLIO
    โปรไฟล์ที่ปิดอยู่ (is_public = 0) จะไม่แสดงให้คนอื่นเห็น"""
    a = q.get_actor(actor_id)
    if not a or not a["is_public"]:
        st.warning("ไม่พบโปรไฟล์นี้ หรือเจ้าของยังไม่เผยแพร่")
        return
    st.html(profile_html(a, q.get_actor_skills(actor_id), q.list_works(actor_id)))


# ---------------------------------------------------------------------
# ตัวกรองรูปลักษณ์ + ตัวเลือกทักษะแยกหมวด (ใช้ซ้ำหลายหน้า)
# ---------------------------------------------------------------------
_TRI = {"ไม่สนใจ": None, "ต้องมี": True, "ต้องไม่มี": False}


def trait_filters(key, expanded=False):
    """ตัวกรองรูปลักษณ์แบบพับได้ คืน (traits dict, จำนวนตัวกรองที่เปิดใช้)  key = คำนำหน้าชื่อ widget"""
    traits = {}
    with st.expander("ตัวกรองรูปลักษณ์  (อายุ ส่วนสูง รูปร่าง สีผม สีผิว สีตา ฯลฯ)", expanded=expanded, icon=":material/tune:"):
        c1, c2 = st.columns(2)
        age = c1.slider("ช่วงอายุ (ปี)", 18, 70, (18, 70), key=f"{key}_age")
        height = c2.slider("ช่วงส่วนสูง (ซม.)", 140, 200, (140, 200), key=f"{key}_h")
        if age != (18, 70):
            traits["age_min"], traits["age_max"] = age
        if height != (140, 200):
            traits["height_min"], traits["height_max"] = height
        c1, c2, c3 = st.columns(3)
        pick = [
            (c1, "body_types", "รูปร่าง", BODY_TYPE_LABEL), (c2, "skin_tones", "สีผิว", SKIN_TONE_LABEL),
            (c3, "eye_colors", "สีตา", EYE_COLOR_LABEL), (c1, "hair_colors", "สีผม", HAIR_COLOR_LABEL),
            (c2, "hair_lengths", "ความยาวผม", HAIR_LENGTH_LABEL), (c3, "hair_textures", "ลักษณะผม", HAIR_TEXTURE_LABEL),
            (c1, "experience", "ระดับประสบการณ์", EXPERIENCE_LABEL),
        ]
        for col, k, label, labels in pick:
            vals = col.multiselect(label, list(labels), format_func=labels.get, key=f"{key}_{k}", placeholder="ทั้งหมด")
            if vals:
                traits[k] = vals
        prov = c2.multiselect("จังหวัด", PROVINCES, key=f"{key}_prov", placeholder="ทั้งหมด")
        if prov:
            traits["provinces"] = prov
        c1, c2, c3 = st.columns(3)
        for col, k, label in ((c1, "tattoo", "รอยสัก"), (c2, "piercing", "เจาะหู/เจาะอื่นๆ"), (c3, "can_travel", "เดินทางต่างจังหวัดได้")):
            ans = col.selectbox(label, list(_TRI), key=f"{key}_{k}")
            if _TRI[ans] is not None:
                traits[k] = _TRI[ans]
    return traits, len([k for k in traits if k not in ("age_max", "height_max")])


def skill_group_pickers(key, default_ids=(), cols=2):
    """เลือกทักษะแยกตามหมวด (หมวดละ 1 multiselect) คืน list ของ skill_id ที่เลือกทั้งหมด"""
    default_ids = set(default_ids)
    by_type = {}
    for s_ in q.list_skills():
        by_type.setdefault(s_["skill_type"], []).append(s_)
    chosen = []
    grid = st.columns(cols)
    for i, t in enumerate(SKILL_TYPES):
        items = by_type.get(t, [])
        labels = {x["skill_id"]: x["skill_name"] for x in items}
        sel = grid[i % cols].multiselect(
            f"{SKILL_TYPE_LABEL[t]}  ({len(items)})", list(labels), format_func=labels.get,
            default=[x for x in labels if x in default_ids], key=f"{key}_sk_{t}", placeholder="เลือกทักษะ")
        chosen += sel
    return chosen


def role_head(role_name, sub, fee, status_html):
    return (
        '<div class="rhead"><div>'
        f'<h3>{esc(role_name)}</h3><div class="sub">{esc(sub)}</div>'
        f'<div class="rstate">{status_html}</div></div>'
        f'<div class="fee"><span>ค่าตัว</span><b>฿{money(fee)}</b></div></div>')


# ---------------------------------------------------------------------
# แปลง list ของ dict เป็นตาราง
# ---------------------------------------------------------------------
def _cell(key, value, fmt):
    if key in fmt:
        return esc(str(fmt[key](value))), ""
    if value is None or value == "":
        return "–", "dim"
    if isinstance(value, bool):
        return ("ใช่" if value else "ไม่"), ""
    if key.endswith("_id"):
        return f"#{value}", "id"
    if isinstance(value, (int, float, Decimal)):
        return (f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"), "num"
    if isinstance(value, time):
        return value.strftime("%H:%M"), ""
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d"), ""
    text = str(value)
    return esc(text), ("wrap" if len(text) > 40 else "")


def table(rows, columns, height=None, badges=None, fmt=None):
    """columns = {"ชื่อคอลัมน์ในข้อมูล": "หัวตารางภาษาไทย"}  (เรียงตามลำดับที่ใส่)
    badges   = {"ชื่อคอลัมน์": ฟังก์ชัน(แถว) -> HTML ของป้ายสถานะ}
    fmt      = {"ชื่อคอลัมน์": ฟังก์ชัน(ค่า) -> ข้อความ}"""
    if not rows:
        st.html('<div class="note">ยังไม่มีข้อมูลในส่วนนี้</div>')
        return
    badges, fmt = badges or {}, fmt or {}
    head, body = [], []
    first = rows[0]
    numeric = {k for k in columns if k not in badges and k not in fmt
               and isinstance(first.get(k), (int, float, Decimal)) and not isinstance(first.get(k), bool)
               and not k.endswith("_id")}
    for k, title in columns.items():
        head.append(f'<th class="{"num" if k in numeric else ""}">{esc(title)}</th>')
    for r in rows:
        tds = []
        for k in columns:
            if k in badges:
                tds.append(f"<td>{badges[k](r)}</td>")
            else:
                text, cls = _cell(k, r.get(k), fmt)
                tds.append(f'<td class="{cls}">{text}</td>')
        body.append("<tr>" + "".join(tds) + "</tr>")
    style = f' style="max-height:{int(height)}px"' if height else ""
    st.html(f'<div class="ctable-wrap"{style}><table class="ctable"><thead><tr>{"".join(head)}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def skill_options():
    """คืน (list ของ skill_id, dict id -> ข้อความที่ใช้แสดง) สำหรับ multiselect ทักษะ"""
    skills = q.list_skills()
    labels = {s["skill_id"]: f"{s['skill_name']} ({SKILL_TYPE_LABEL[s['skill_type']]})" for s in skills}
    return list(labels), labels


def gender_th(g):
    return GENDER_LABEL.get(g, g)


def actor_status_th(s):
    return ACTOR_STATUS_LABEL.get(s, s)


EVENT_FROM_TH = {v: k for k, v in EVENT_TYPE_LABEL.items()}    # 'ถ่ายทำ' -> 'Shoot'


# ---------------------------------------------------------------------
# ตัวช่วยแปลงค่าจากตารางที่ผู้ใช้กรอก (data_editor) ให้เป็นชนิดข้อมูลที่ SQL ใช้ได้
# ---------------------------------------------------------------------
def _to_date(x):
    return pd.to_datetime(x).date()


def _to_time(x):
    if isinstance(x, str):
        return datetime.strptime(x[:5], "%H:%M").time()
    if isinstance(x, datetime):          # รวม pandas.Timestamp ด้วย
        return x.time()
    return x                              # datetime.time อยู่แล้ว


def parse_slots(df):
    slots = []
    for n, (_, row) in enumerate(df.iterrows(), 1):
        vals = [row["ประเภท"], row["วันที่"], row["เริ่ม"], row["เลิก"]]
        if all(pd.isna(v) for v in vals):
            continue                       # แถวว่าง ข้ามไป
        if any(pd.isna(v) for v in vals):
            raise q.BusinessError(f"ตารางนัดแถวที่ {n}: กรอกไม่ครบ")
        slots.append({"event_type": EVENT_FROM_TH[row["ประเภท"]], "event_date": _to_date(row["วันที่"]),
                      "start_time": _to_time(row["เริ่ม"]), "end_time": _to_time(row["เลิก"])})
    return slots


def parse_installments(df):
    items = []
    for n, (_, row) in enumerate(df.iterrows(), 1):
        vals = [row["ครบกำหนดจ่าย"], row["จำนวนเงิน"]]
        if all(pd.isna(v) for v in vals):
            continue
        if any(pd.isna(v) for v in vals):
            raise q.BusinessError(f"งวดจ่ายแถวที่ {n}: กรอกไม่ครบ")
        items.append({"due_date": _to_date(row["ครบกำหนดจ่าย"]), "amount": float(row["จำนวนเงิน"])})
    return items


def slot_text(s):
    return (f"{EVENT_TYPE_LABEL[s['event_type']]} {s['event_date']} "
            f"{s['start_time'].strftime('%H:%M')}-{s['end_time'].strftime('%H:%M')}")


# ---------------------------------------------------------------------
# แถบ "ดู SQL" ที่แถบด้านข้าง
# ---------------------------------------------------------------------
def sql_footer():
    """สวิตช์ 'โหมดโชว์ SQL' อยู่ท้ายหน้า ส่วนรายการ SQL แสดงต่อจากสวิตช์ (กว้างพอให้อ่านได้ทั้งบรรทัด)"""
    with st.container(key="sqlbar"):
        st.divider()
        show = st.toggle(
            "โหมดโชว์ SQL  (ไว้อธิบายอาจารย์ว่าปุ่มไหนดึงตารางไหน)", key="show_sql",
            help="เปิดแล้วจะเห็นคำสั่ง SQL ที่หน้าเว็บส่งไปที่ MySQL")
        if show:
            _sql_log()
    site_footer()


def _sql_log():
    log = db.get_sql_log()
    section("SQL ที่หน้าเว็บส่งไปที่ MySQL", "เรียงจากใหม่ไปเก่า")
    c1, c2 = st.columns([3, 1])
    mode = c1.radio("แสดง", ["ทุกคำสั่ง", "เฉพาะคำสั่งที่แก้ข้อมูล (INSERT/UPDATE/DELETE)"],
                    horizontal=True, key="sql_filter", label_visibility="collapsed")
    if c2.button("ล้างรายการ", key="clear_sql_log"):
        db.clear_sql_log()
        st.rerun()
    only_write = mode.startswith("เฉพาะ")
    shown = [(sql, p) for sql, p in reversed(log)
             if not only_write or sql.split()[0].upper() in ("INSERT", "UPDATE", "DELETE")]
    st.caption(f"เรียงจากใหม่ไปเก่า  ·  แสดง {len(shown)} จาก {len(log)} คำสั่งล่าสุด  ·  "
               f"%s คือช่องที่ระบบใส่ค่าแทนให้ตามลำดับพารามิเตอร์ (กัน SQL injection)")
    if not shown:
        st.info("ยังไม่มีคำสั่ง ลองกดปุ่มในหน้านี้ แล้วกลับมาดู")
    for sql, params in shown:
        st.code(sql, language="sql", wrap_lines=True)
        if params:
            st.caption(f"พารามิเตอร์: {list(params) if not isinstance(params, dict) else params}")


def site_footer():
    """ฟุตเตอร์ตัวอักษรใหญ่ท้ายทุกหน้า"""
    st.html(
        '<footer class="site-foot"><div class="cols">'
        '<div><b>Casting Agency</b><br>ระบบเอเจนซี่นักแสดงและโมเดลลิ่ง</div>'
        '<div><b>CSS222 Database Systems</b><br>KMUTT · Statistics &amp; Data Science</div>'
        '<div><b>เทคโนโลยี</b><br>Python · Streamlit · MySQL</div></div>'
        '<div class="mark">CASTING</div></footer>')


# ---------------------------------------------------------------------
# กราฟ (Altair) -- สีตามสถานะเดียวกันทุกกราฟ (สีติดกับ "สถานะ" ไม่ใช่ลำดับแท่ง)
# ---------------------------------------------------------------------
INK, MUTED, MAG, GOLD, EMERALD = "#1F1A1D", "#7A6F73", "#5E1A2E", "#B8955A", "#2F6F57"
ROLE_COLOR = {"รอนักแสดงตอบรับ": GOLD, "ยืนยันแล้ว": EMERALD, "นักแสดงปฏิเสธ": "#9B2340", "ผู้จัดงานยกเลิก": "#A39A9E"}
PAYMENT_COLOR = {"รอจ่าย": GOLD, "จ่ายแล้ว": EMERALD, "ยกเลิก": "#A39A9E"}


def _style(chart):
    return (chart.configure_view(stroke=None)
            .configure(font="Prompt, sans-serif", background="rgba(0,0,0,0)")
            .configure_axis(labelColor=MUTED, labelFontSize=12, titleColor=MUTED, domain=False, ticks=False,
                            gridColor="#E8DDD6", labelLimit=240)
            .configure_legend(labelColor=INK, titleColor=MUTED, labelFontSize=12, orient="top", title=None))


def hbar(df, cat, val, colors=None, height=None, unit=""):
    """แท่งแนวนอนเรียงมากไปน้อย ใส่ตัวเลขท้ายแท่ง  colors = {ชื่อหมวด: สี} (ไม่ใส่ = ชมพูแมเจนต้า)"""
    base = alt.Chart(df).encode(
        y=alt.Y(f"{cat}:N", sort="-x", title=None),
        x=alt.X(f"{val}:Q", title=None, axis=None))
    if colors:
        color = alt.Color(f"{cat}:N", scale=alt.Scale(domain=list(colors), range=list(colors.values())), legend=None)
        bars = base.mark_bar(cornerRadiusEnd=4, size=16).encode(color=color)
    else:
        bars = base.mark_bar(cornerRadiusEnd=4, size=16, color=MAG)
    labels = base.mark_text(align="left", dx=6, color=INK, fontSize=12, font="Prompt").encode(
        text=alt.Text(f"{val}:Q", format=",.0f"))
    chart = (bars + labels).properties(height=height or max(90, 38 * len(df)))
    st.altair_chart(_style(chart), width="stretch")


def stacked_money(df, cat, series, colors, height=None):
    """แท่งซ้อนแนวนอน : df เป็นตารางแบบยาว (cat, series, amount)"""
    chart = alt.Chart(df).mark_bar(cornerRadiusEnd=3, size=18, stroke="#FAF6F2", strokeWidth=2).encode(
        y=alt.Y(f"{cat}:N", title=None, sort=None),
        x=alt.X("amount:Q", title=None, axis=alt.Axis(format=",.0f", grid=True)),
        color=alt.Color(f"{series}:N", scale=alt.Scale(domain=list(colors), range=list(colors.values()))),
        tooltip=[cat, series, alt.Tooltip("amount:Q", format=",.0f", title="บาท")],
    ).properties(height=height or 70 * df[cat].nunique() + 70)
    st.altair_chart(_style(chart), width="stretch")
