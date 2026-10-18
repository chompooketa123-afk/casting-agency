"""
queries.py : SQL ทั้งหมดของระบบอยู่ที่ไฟล์นี้ไฟล์เดียว

หน้าเว็บ (classic_pages/*.py) ไม่เขียน SQL เอง แต่เรียกฟังก์ชันในไฟล์นี้
  -> ถ้าอาจารย์ถามว่า "ปุ่มนี้ดึงตารางไหน" ให้เปิดไฟล์นี้ดูชื่อฟังก์ชันได้เลย
  -> กฎธุรกิจ (คิวชน / ทักษะครบ / กันจ่ายซ้ำ) อยู่ในไฟล์นี้ทั้งหมด

สารบัญ
  [A] ทักษะ                list_skills
  [B] นักแสดง              register_actor, update_actor, list_actors, ...
  [B2] โปรไฟล์สาธารณะ/ผลงาน  set_profile_public, add_work, delete_work, ... (คนที่ซ่อนอยู่ คนอื่นจะไม่เห็น)
  [C] โปรเจกต์             create_project, list_projects, update_project_status
  [D] จับคู่นักแสดง         find_matching_actors, explain_excluded   <-- หัวใจของระบบ
  [E] บทบาท (ROLE)         create_role, respond_to_role, cancel_role, ...
  [F] ตารางนัด / การจ่ายเงิน  schedule_of_actor, payments_of_actor, mark_paid, ...
  [G] ค้นหานักแสดง          search_actors
  [H] Dashboard
"""
import re
from datetime import date, time
from decimal import Decimal

from config import (BUSY_ROLE_STATUSES, BODY_TYPE_LABEL, SKIN_TONE_LABEL, HAIR_COLOR_LABEL,
                    HAIR_LENGTH_LABEL, HAIR_TEXTURE_LABEL, EYE_COLOR_LABEL, CLOTHING_SIZES,
                    EXPERIENCE_LABEL, PROVINCES, WORK_TYPE_LABEL, MAX_WORKS)
from db import query, execute, transaction


class BusinessError(Exception):
    """ผิดกฎของระบบ (ไม่ใช่โปรแกรมพัง) หน้าเว็บจะจับไปโชว์เป็นข้อความสีแดง"""


# สตริง ('Selected','Confirmed') ไว้ต่อใน SQL (เป็นค่าคงที่ของเรา ไม่ได้มาจากผู้ใช้ จึงปลอดภัย)
_BUSY = "(" + ",".join(f"'{s}'" for s in BUSY_ROLE_STATUSES) + ")"


def _clean(rows):
    """แปลง Decimal -> float เพื่อให้ pandas/Streamlit แสดงผลได้ง่าย"""
    for r in rows:
        for k, v in r.items():
            if isinstance(v, Decimal):
                r[k] = float(v)
    return rows


def _marks(items):
    """สร้าง '%s,%s,%s' ตามจำนวนรายการ ไว้ใช้กับ IN (...)"""
    return ",".join(["%s"] * len(items))


def to_money(x):
    return Decimal(str(x)).quantize(Decimal("0.01"))


def _hhmm(t: time):
    return t.strftime("%H:%M")


# =====================================================================
# [A] ทักษะ  (ตาราง SKILL)
# =====================================================================
def list_skills():
    return query("SELECT skill_id, skill_name, skill_type FROM SKILL ORDER BY skill_type, skill_name")


# =====================================================================
# [B] นักแสดง  (ตาราง ACTOR, ACTOR_SKILL)
# =====================================================================
# คอลัมน์รูปลักษณ์ที่ให้กรอก/แก้ได้ (whitelist กัน SQL injection ผ่านชื่อคอลัมน์)
#   ชื่อคอลัมน์ -> (ชนิด, ค่าที่อนุญาต หรือ (ต่ำสุด, สูงสุด))
PROFILE_FIELDS = {
    "birth_date": ("date", None),
    "height_cm": ("int", (100, 230)), "weight_kg": ("float", (25, 250)),
    "bust_chest_cm": ("int", (40, 200)), "waist_cm": ("int", (40, 200)), "hip_cm": ("int", (40, 200)),
    "shoe_size_eu": ("float", (30, 50)), "clothing_size": ("enum", CLOTHING_SIZES),
    "body_type": ("enum", BODY_TYPE_LABEL), "skin_tone": ("enum", SKIN_TONE_LABEL),
    "hair_color": ("enum", HAIR_COLOR_LABEL), "hair_length": ("enum", HAIR_LENGTH_LABEL),
    "hair_texture": ("enum", HAIR_TEXTURE_LABEL), "eye_color": ("enum", EYE_COLOR_LABEL),
    "has_tattoo": ("bool", None), "has_piercing": ("bool", None),
    "experience_level": ("enum", EXPERIENCE_LABEL), "province": ("enum", PROVINCES),
    "can_travel": ("bool", None),
}
_PROFILE_NOT_NULL = {"has_tattoo": False, "has_piercing": False, "can_travel": False,
                     "experience_level": "Beginner"}
_FIELD_TH = {"height_cm": "ส่วนสูง", "weight_kg": "น้ำหนัก", "bust_chest_cm": "รอบอก",
             "waist_cm": "รอบเอว", "hip_cm": "รอบสะโพก", "shoe_size_eu": "เบอร์รองเท้า"}


def clean_profile(profile):
    """ตรวจและแปลงค่ารูปลักษณ์ก่อนบันทึก (ค่าว่าง = NULL) ผิดกฎ -> BusinessError
    อายุต้อง >= 18 ปี ตรวจที่นี่ (ER ไม่ได้บังคับด้วย CHECK เพราะ CHECK ใช้ CURDATE() ไม่ได้)"""
    out = {}
    for col, (kind, rule) in PROFILE_FIELDS.items():
        v = (profile or {}).get(col)
        if v in ("", None):
            out[col] = _PROFILE_NOT_NULL.get(col)
            continue
        if kind == "bool":
            out[col] = bool(v)
        elif kind == "date":
            if not isinstance(v, date):
                raise BusinessError("วันเกิดไม่ถูกต้อง")
            today = date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age < 18:
                raise BusinessError("ระบบรับเฉพาะผู้ที่อายุ 18 ปีขึ้นไป")
            if age > 90:
                raise BusinessError("วันเกิดไม่สมเหตุสมผล")
            out[col] = v
        elif kind in ("int", "float"):
            try:
                v = int(v) if kind == "int" else float(v)
            except (TypeError, ValueError):
                raise BusinessError(f"{_FIELD_TH.get(col, col)} ต้องเป็นตัวเลข")
            lo, hi = rule
            if not lo <= v <= hi:
                raise BusinessError(f"{_FIELD_TH.get(col, col)} ต้องอยู่ระหว่าง {lo}-{hi}")
            out[col] = v
        else:  # enum
            if v not in rule:
                raise BusinessError(f"ค่า {col} ไม่ถูกต้อง")
            out[col] = v
    return out


_KEEP = object()      # ค่าพิเศษ = "ไม่ต้องแตะคอลัมน์นี้" (ใช้แยกจาก None ที่แปลว่าล้างค่า)


def _clean_bio(bio):
    bio = (bio or "").strip()
    if len(bio) > 500:
        raise BusinessError("แนะนำตัวยาวเกิน 500 ตัวอักษร")
    return bio or None


def _sync_visibility(tx, actor_id):
    """รักษากฎ 'ไม่ได้ใส่อะไร = คนอื่นไม่เห็น' : ถ้าโปรไฟล์ยังเปิดอยู่แต่ไม่เหลือทั้งทักษะและผลงาน ให้ปิดเอง
    คืนค่า is_public ล่าสุด"""
    tx.execute(
        "UPDATE ACTOR SET is_public = 0 WHERE actor_id = %s AND is_public = 1 "
        "AND NOT EXISTS (SELECT 1 FROM ACTOR_SKILL WHERE actor_id = %s) "
        "AND NOT EXISTS (SELECT 1 FROM PORTFOLIO WHERE actor_id = %s)", (actor_id, actor_id, actor_id))
    rows = tx.query("SELECT is_public FROM ACTOR WHERE actor_id=%s", (actor_id,))
    return bool(rows and rows[0]["is_public"])


def register_actor(full_name, gender, appearance_detail, skill_ids, profile=None, bio=None, publish=True):
    """ปุ่ม 'สมัครเป็นนักแสดง' : INSERT ACTOR แล้ว INSERT ACTOR_SKILL หลายแถว (ใน transaction เดียว)
    profile = dict รูปลักษณ์ (ส่วนสูง สีผม ฯลฯ) ถ้าไม่ส่งมาก็ปล่อยว่าง
    publish = ขอเปิดโปรไฟล์ให้คนอื่นเห็นทันที แต่จะเปิดให้ก็ต่อเมื่อมีทักษะอย่างน้อย 1 อย่าง"""
    full_name = (full_name or "").strip()
    if not full_name:
        raise BusinessError("กรุณากรอกชื่อ-นามสกุล")
    prof = clean_profile(profile)
    skill_ids = sorted(set(skill_ids))
    cols = ["full_name", "gender", "actor_status", "appearance_detail", "bio", "is_public"] + list(prof)
    vals = [full_name, gender, "Active", (appearance_detail or "").strip() or None, _clean_bio(bio),
            1 if (publish and skill_ids) else 0] + list(prof.values())
    with transaction() as tx:
        _, actor_id = tx.execute(
            f"INSERT INTO ACTOR ({', '.join(cols)}) VALUES ({_marks(cols)})", vals)
        for sid in skill_ids:
            tx.execute("INSERT INTO ACTOR_SKILL (actor_id, skill_id) VALUES (%s, %s)", (actor_id, sid))
    return actor_id


def update_actor(actor_id, full_name, gender, actor_status, appearance_detail, skill_ids, profile=None, bio=_KEEP):
    """ปุ่ม 'บันทึกโปรไฟล์' : UPDATE ACTOR + ลบทักษะเก่า + ใส่ทักษะใหม่ (transaction เดียว)
    ถ้าไม่ส่ง profile มา จะไม่แตะคอลัมน์รูปลักษณ์ / ไม่ส่ง bio มา จะไม่แตะคำแนะนำตัว
    คืน True/False = หลังบันทึกแล้วโปรไฟล์ยังเปิดให้คนอื่นเห็นอยู่ไหม (ลบทักษะหมดและไม่มีผลงาน = ปิดเอง)"""
    full_name = (full_name or "").strip()
    if not full_name:
        raise BusinessError("ชื่อห้ามว่าง")
    sets = ["full_name=%s", "gender=%s", "actor_status=%s", "appearance_detail=%s"]
    vals = [full_name, gender, actor_status, (appearance_detail or "").strip() or None]
    if bio is not _KEEP:
        sets.append("bio=%s")
        vals.append(_clean_bio(bio))
    if profile is not None:
        prof = clean_profile(profile)
        sets += [f"{c}=%s" for c in prof]
        vals += list(prof.values())
    with transaction() as tx:
        tx.execute(f"UPDATE ACTOR SET {', '.join(sets)} WHERE actor_id=%s", vals + [actor_id])
        tx.execute("DELETE FROM ACTOR_SKILL WHERE actor_id=%s", (actor_id,))
        for sid in sorted(set(skill_ids)):
            tx.execute("INSERT INTO ACTOR_SKILL (actor_id, skill_id) VALUES (%s, %s)", (actor_id, sid))
        return _sync_visibility(tx, actor_id)


# =====================================================================
# [B2] โปรไฟล์สาธารณะ + ผลงาน  (ตาราง ACTOR.is_public, PORTFOLIO)
#   กติกา: คนอื่นเห็นนักแสดงก็ต่อเมื่อ is_public = 1 และ is_public ตั้งได้เมื่อมีทักษะหรือผลงานอย่างน้อย 1 อย่าง
#   ทุกคำสั่งฝั่งผู้จัดงาน (แคตตาล็อก ค้นหา จับคู่ หน้าแรก) กรอง a.is_public = 1 ใน SQL
# =====================================================================
_PUBLIC = " AND a.is_public = 1"


def profile_readiness(actor_id):
    """เช็กว่าโปรไฟล์พร้อมเผยแพร่ไหม -> dict  (ใช้โชว์เช็กลิสต์ในหน้า 'โปรไฟล์ของฉัน')"""
    r = query(
        "SELECT a.full_name, a.bio, a.is_public, "
        " (SELECT COUNT(*) FROM ACTOR_SKILL k WHERE k.actor_id=a.actor_id) AS n_skills, "
        " (SELECT COUNT(*) FROM PORTFOLIO w WHERE w.actor_id=a.actor_id) AS n_works "
        "FROM ACTOR a WHERE a.actor_id=%s", (actor_id,))
    if not r:
        raise BusinessError("ไม่พบนักแสดงคนนี้")
    r = r[0]
    out = {"has_name": bool((r["full_name"] or "").strip()), "has_bio": bool(r["bio"]),
           "n_skills": r["n_skills"], "n_works": r["n_works"], "is_public": bool(r["is_public"])}
    out["ready"] = out["has_name"] and (out["n_skills"] > 0 or out["n_works"] > 0)
    return out


def set_profile_public(actor_id, public):
    """ปุ่ม 'เผยแพร่โปรไฟล์' / 'ซ่อนโปรไฟล์' : UPDATE ACTOR.is_public
    เปิดได้เมื่อมีชื่อ และมีทักษะหรือผลงานอย่างน้อย 1 อย่าง (ถ้าไม่ได้ใส่อะไรเลย คนอื่นจะไม่เห็น)"""
    if public:
        r = profile_readiness(actor_id)
        if not r["ready"]:
            raise BusinessError("ยังเผยแพร่ไม่ได้ ต้องเลือกแท็กทักษะหรือเพิ่มผลงานอย่างน้อย 1 อย่างก่อน")
    execute("UPDATE ACTOR SET is_public=%s WHERE actor_id=%s", (1 if public else 0, actor_id))


_URL_RE = re.compile(r"^https?://[^\s<>\"']+$", re.I)


def _clean_work(title, work_type, role_played, work_year, description, link_url):
    title = (title or "").strip()
    if not title:
        raise BusinessError("กรุณากรอกชื่อผลงาน")
    if len(title) > 150:
        raise BusinessError("ชื่อผลงานยาวเกิน 150 ตัวอักษร")
    if work_type not in WORK_TYPE_LABEL:
        raise BusinessError("ประเภทผลงานไม่ถูกต้อง")
    try:
        work_year = int(work_year)
    except (TypeError, ValueError):
        raise BusinessError("ปีของผลงานต้องเป็นตัวเลข")
    if not 1980 <= work_year <= date.today().year + 1:
        raise BusinessError(f"ปีของผลงานต้องอยู่ระหว่าง 1980-{date.today().year + 1}")
    role_played = (role_played or "").strip() or None
    description = (description or "").strip() or None
    link_url = (link_url or "").strip() or None
    if role_played and len(role_played) > 100:
        raise BusinessError("ชื่อบทยาวเกิน 100 ตัวอักษร")
    if description and len(description) > 500:
        raise BusinessError("รายละเอียดผลงานยาวเกิน 500 ตัวอักษร")
    if link_url and (len(link_url) > 300 or not _URL_RE.match(link_url)):
        raise BusinessError("ลิงก์ต้องขึ้นต้นด้วย http:// หรือ https:// (ยาวไม่เกิน 300 ตัวอักษร)")
    return [title, work_type, role_played, work_year, description, link_url]


def list_works(actor_id):
    """ผลงานของนักแสดง เรียงปีล่าสุดก่อน (ตาราง PORTFOLIO)"""
    return query("SELECT work_id, title, work_type, role_played, work_year, description, link_url "
                 "FROM PORTFOLIO WHERE actor_id=%s ORDER BY work_year DESC, work_id DESC", (actor_id,))


def add_work(actor_id, title, work_type, role_played, work_year, description=None, link_url=None):
    """ปุ่ม 'เพิ่มผลงาน' : INSERT PORTFOLIO (สูงสุด MAX_WORKS ชิ้นต่อคน)"""
    vals = _clean_work(title, work_type, role_played, work_year, description, link_url)
    with transaction() as tx:
        owner = tx.query("SELECT actor_id FROM ACTOR WHERE actor_id=%s FOR UPDATE", (actor_id,))
        if not owner:
            raise BusinessError("ไม่พบนักแสดงคนนี้")
        n = tx.query("SELECT COUNT(*) AS n FROM PORTFOLIO WHERE actor_id=%s", (actor_id,))[0]["n"]
        if n >= MAX_WORKS:
            raise BusinessError(f"เพิ่มผลงานได้สูงสุด {MAX_WORKS} ชิ้น ลบอันเก่าก่อนจึงจะเพิ่มได้")
        _, work_id = tx.execute(
            "INSERT INTO PORTFOLIO (title, work_type, role_played, work_year, description, link_url, actor_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)", vals + [actor_id])
    return work_id


def update_work(actor_id, work_id, title, work_type, role_played, work_year, description=None, link_url=None):
    """ปุ่ม 'บันทึกการแก้ผลงาน' : UPDATE PORTFOLIO (แก้ได้เฉพาะผลงานของตัวเอง)"""
    vals = _clean_work(title, work_type, role_played, work_year, description, link_url)
    n, _ = execute(
        "UPDATE PORTFOLIO SET title=%s, work_type=%s, role_played=%s, work_year=%s, description=%s, link_url=%s "
        "WHERE work_id=%s AND actor_id=%s", vals + [work_id, actor_id])
    if n == 0 and not query("SELECT 1 FROM PORTFOLIO WHERE work_id=%s AND actor_id=%s", (work_id, actor_id)):
        raise BusinessError("ไม่พบผลงานนี้ในโปรไฟล์ของคุณ")


def delete_work(actor_id, work_id):
    """ปุ่ม 'ลบผลงาน' : DELETE PORTFOLIO แล้วเช็กว่าโปรไฟล์ยังมีอะไรให้โชว์ไหม คืน is_public ล่าสุด"""
    with transaction() as tx:
        n, _ = tx.execute("DELETE FROM PORTFOLIO WHERE work_id=%s AND actor_id=%s", (work_id, actor_id))
        if n == 0:
            raise BusinessError("ไม่พบผลงานนี้ในโปรไฟล์ของคุณ")
        return _sync_visibility(tx, actor_id)


# รายการคอลัมน์ที่ดึงมาแสดงการ์ด/โปรไฟล์ : ทุกคอลัมน์ของ ACTOR + อายุ + ทักษะ (รวมเป็นข้อความ)
_ACTOR_COLS = (
    "a.*, TIMESTAMPDIFF(YEAR, a.birth_date, CURDATE()) AS age, "
    "(SELECT GROUP_CONCAT(s.skill_name ORDER BY FIELD(s.skill_type,'Modeling','Performance','Physical','Language','Other'), s.skill_name SEPARATOR ', ') "
    " FROM ACTOR_SKILL ak2 JOIN SKILL s ON s.skill_id = ak2.skill_id "
    " WHERE ak2.actor_id = a.actor_id) AS skills, "
    "(SELECT COUNT(*) FROM PORTFOLIO w WHERE w.actor_id = a.actor_id) AS n_works")


def list_actors(only_active=False, public_only=False):
    """public_only=True = เฉพาะคนที่เปิดโปรไฟล์ให้คนอื่นเห็น (dropdown 'ฉันคือใคร' ต้องเห็นทุกคนจึงไม่ใส่)"""
    sql = f"SELECT {_ACTOR_COLS} FROM ACTOR a WHERE 1=1"
    if only_active:
        sql += " AND a.actor_status = 'Active'"
    if public_only:
        sql += _PUBLIC
    return _clean(query(sql + " ORDER BY a.full_name"))


def get_actor(actor_id):
    rows = query(f"SELECT {_ACTOR_COLS} FROM ACTOR a WHERE a.actor_id=%s", (actor_id,))
    return _clean(rows)[0] if rows else None


def get_actor_skill_ids(actor_id):
    rows = query("SELECT skill_id FROM ACTOR_SKILL WHERE actor_id=%s", (actor_id,))
    return [r["skill_id"] for r in rows]


def get_actor_skills(actor_id):
    """ทักษะของนักแสดงแบ่งตามหมวด -> {skill_type: [skill_name, ...]}"""
    out = {}
    for r in query("SELECT s.skill_type, s.skill_name FROM ACTOR_SKILL ak JOIN SKILL s "
                   "ON s.skill_id = ak.skill_id WHERE ak.actor_id=%s ORDER BY s.skill_type, s.skill_name",
                   (actor_id,)):
        out.setdefault(r["skill_type"], []).append(r["skill_name"])
    return out


def featured_actors(limit=8):
    """หน้าแรก: โชว์นักแสดงที่ Active + เปิดโปรไฟล์ และมีทักษะเยอะสุดก่อน (ตาราง ACTOR + ACTOR_SKILL)"""
    return _clean(query(
        f"SELECT {_ACTOR_COLS}, (SELECT COUNT(*) FROM ACTOR_SKILL x WHERE x.actor_id=a.actor_id) AS n_skills "
        f"FROM ACTOR a WHERE a.actor_status='Active'{_PUBLIC} ORDER BY n_skills DESC, a.actor_id LIMIT %s",
        (int(limit),)))


def talent_counts():
    """ตัวเลขสั้นๆ ไว้โชว์หน้าแรก"""
    return query("SELECT (SELECT COUNT(*) FROM ACTOR WHERE actor_status='Active' AND is_public=1) AS actors, "
                 "(SELECT COUNT(*) FROM SKILL) AS skills, "
                 "(SELECT COUNT(*) FROM PROJECT) AS projects, "
                 "(SELECT COUNT(*) FROM `ROLE`) AS roles")[0]


# =====================================================================
# ตัวกรองรูปลักษณ์ (traits) : ใช้ร่วมกันทั้งหน้าจับคู่ (org_casting) และหน้าค้นหา
#   traits = {"age_min", "age_max", "height_min", "height_max",
#             "body_types": [..], "skin_tones": [..], "hair_colors": [..], "hair_lengths": [..],
#             "hair_textures": [..], "eye_colors": [..], "experience": [..], "provinces": [..],
#             "tattoo": True/False/None, "piercing": True/False/None, "can_travel": True/None}
# =====================================================================
_TRAIT_LISTS = {  # key ใน traits -> (คอลัมน์, ชื่อไทยไว้เขียนเหตุผล, ตัวแปลงค่าเป็นภาษาไทย)
    "body_types": ("body_type", "รูปร่าง", BODY_TYPE_LABEL),
    "skin_tones": ("skin_tone", "สีผิว", SKIN_TONE_LABEL),
    "hair_colors": ("hair_color", "สีผม", HAIR_COLOR_LABEL),
    "hair_lengths": ("hair_length", "ความยาวผม", HAIR_LENGTH_LABEL),
    "hair_textures": ("hair_texture", "ลักษณะผม", HAIR_TEXTURE_LABEL),
    "eye_colors": ("eye_color", "สีตา", EYE_COLOR_LABEL),
    "experience": ("experience_level", "ระดับประสบการณ์", EXPERIENCE_LABEL),
    "provinces": ("province", "จังหวัด", {p: p for p in PROVINCES}),
}
_TRAIT_FLAGS = {"tattoo": ("has_tattoo", "รอยสัก"), "piercing": ("has_piercing", "เจาะ"),
                "can_travel": ("can_travel", "เดินทางต่างจังหวัด")}
_AGE = "TIMESTAMPDIFF(YEAR, a.birth_date, CURDATE())"


def _traits_sql(traits):
    """แปลง traits เป็นเงื่อนไข SQL (ชื่อคอลัมน์มาจากตารางคงที่ในโค้ด ไม่ใช่จากผู้ใช้)"""
    t = traits or {}
    sql, params = "", []
    for key, op, expr in (("age_min", ">=", _AGE), ("age_max", "<=", _AGE),
                          ("height_min", ">=", "a.height_cm"), ("height_max", "<=", "a.height_cm")):
        if t.get(key) not in (None, ""):
            sql += f" AND {expr} {op} %s"
            params.append(int(t[key]))
    for key, (col, _, _) in _TRAIT_LISTS.items():
        vals = list(t.get(key) or [])
        if vals:
            sql += f" AND a.{col} IN ({_marks(vals)})"
            params += vals
    for key, (col, _) in _TRAIT_FLAGS.items():
        if t.get(key) is not None:
            sql += f" AND a.{col} = %s"
            params.append(1 if t[key] else 0)
    return sql, params


def trait_failures(actor, traits):
    """เหตุผล (ข้อความไทย) ที่นักแสดงคนนี้ไม่ผ่านตัวกรองรูปลักษณ์ -- ใช้ตรรกะเดียวกับ _traits_sql"""
    t, why = traits or {}, []
    age, h = actor.get("age"), actor.get("height_cm")
    if t.get("age_min") not in (None, "") and (age is None or age < t["age_min"]):
        why.append(f"อายุต่ำกว่า {t['age_min']} ปี" if age is not None else "ไม่ระบุอายุ")
    if t.get("age_max") not in (None, "") and (age is None or age > t["age_max"]):
        why.append(f"อายุเกิน {t['age_max']} ปี" if age is not None else "ไม่ระบุอายุ")
    if t.get("height_min") not in (None, "") and (h is None or h < t["height_min"]):
        why.append(f"ส่วนสูง {h} ซม. ต่ำกว่า {t['height_min']}" if h else "ไม่ระบุส่วนสูง")
    if t.get("height_max") not in (None, "") and (h is None or h > t["height_max"]):
        why.append(f"ส่วนสูง {h} ซม. เกิน {t['height_max']}" if h else "ไม่ระบุส่วนสูง")
    for key, (col, th, labels) in _TRAIT_LISTS.items():
        vals = list(t.get(key) or [])
        if vals and actor.get(col) not in vals:
            have = labels.get(actor.get(col), actor.get(col)) or "ไม่ระบุ"
            want = "/".join(str(labels.get(v, v)) for v in vals)
            why.append(f"{th}ไม่ตรง (เป็น {have} ต้องการ {want})")
    for key, (col, th) in _TRAIT_FLAGS.items():
        if t.get(key) is not None and bool(actor.get(col)) != bool(t[key]):
            why.append(f"{th}ไม่ตรง ({'ต้องมี' if t[key] else 'ต้องไม่มี'})")
    return why


# =====================================================================
# [C] โปรเจกต์  (ตาราง PROJECT)
# =====================================================================
def create_project(project_name, project_type, client_name):
    """ปุ่ม 'สร้างโปรเจกต์' : INSERT PROJECT (สถานะเริ่มต้น Open)"""
    project_name, client_name = (project_name or "").strip(), (client_name or "").strip()
    if not project_name or not client_name:
        raise BusinessError("กรุณากรอกชื่อโปรเจกต์และชื่อลูกค้า")
    _, pid = execute(
        "INSERT INTO PROJECT (project_name, project_type, project_status, client_name) "
        "VALUES (%s, %s, 'Open', %s)",
        (project_name, project_type, client_name),
    )
    return pid


def update_project_status(project_id, new_status):
    execute("UPDATE PROJECT SET project_status=%s WHERE project_id=%s", (new_status, project_id))


def list_projects():
    """หน้ารวมโปรเจกต์ : LEFT JOIN ROLE เพื่อนับจำนวนบทในแต่ละโปรเจกต์"""
    return query(
        "SELECT p.project_id, p.project_name, p.project_type, p.project_status, p.client_name, "
        "       COUNT(r.role_id) AS role_count "
        "FROM PROJECT p LEFT JOIN `ROLE` r ON r.project_id = p.project_id "
        "GROUP BY p.project_id, p.project_name, p.project_type, p.project_status, p.client_name "
        "ORDER BY p.project_id DESC"
    )


# =====================================================================
# [D] จับคู่นักแสดง (หัวใจของระบบ)
#
# slots = [{"event_type":..., "event_date": date, "start_time": time, "end_time": time}, ...]
#
# นักแสดงที่ "ผ่านเกณฑ์" ต้องครบ 3 ข้อ (และต้องเปิดโปรไฟล์ is_public = 1 ไว้ก่อน ไม่งั้นไม่มีใครเห็น)
#   1) actor_status = 'Active'
#   2) มีทักษะ "ครบทุกข้อ" ที่บทต้องการ  (นับ DISTINCT skill แล้วเทียบกับจำนวนที่ต้องการ)
#   3) ไม่มีคิวชน : ไม่มี SCHEDULE ของบทอื่นที่ยังไม่ถูกปฏิเสธ/ยกเลิก
#      ในวันเดียวกัน และ start < end_ใหม่  AND  end > start_ใหม่   (สูตรเวลาซ้อนทับ)
# =====================================================================
_CONFLICT_NOT_EXISTS = f"""
  AND NOT EXISTS (
        SELECT 1
        FROM `ROLE` r JOIN SCHEDULE s ON s.role_id = r.role_id
        WHERE r.actor_id = a.actor_id
          AND r.role_status IN {_BUSY}
          AND s.event_date = %s
          AND s.start_time < %s
          AND s.end_time   > %s)"""


def _build_match_sql(skill_ids, slots, gender=None, traits=None):
    skill_ids = sorted(set(skill_ids))
    sql = f"SELECT {_ACTOR_COLS} FROM ACTOR a WHERE a.actor_status = 'Active'{_PUBLIC}"
    params = []
    t_sql, t_params = _traits_sql(traits)   # ตัวกรองรูปลักษณ์ (ไม่ส่งมา = ไม่กรอง)
    sql += t_sql
    params += t_params
    if gender:
        sql += " AND a.gender = %s"
        params.append(gender)
    if skill_ids:   # ถ้าบทไม่ระบุทักษะ (เช่นตัวประกอบ) ข้ามเงื่อนไขนี้
        sql += (f" AND (SELECT COUNT(DISTINCT ak.skill_id) FROM ACTOR_SKILL ak "
                f"WHERE ak.actor_id = a.actor_id AND ak.skill_id IN ({_marks(skill_ids)})) = %s")
        params += skill_ids + [len(skill_ids)]
    for s in slots:  # เช็กคิวชนทีละช่วงเวลา
        sql += _CONFLICT_NOT_EXISTS
        params += [s["event_date"], s["end_time"], s["start_time"]]
    sql += " ORDER BY a.full_name"
    return sql, params


def find_matching_actors(skill_ids, slots, gender=None, traits=None):
    """ปุ่ม 'ค้นหานักแสดงที่เหมาะสม' : คืนรายชื่อที่ผ่านทุกเงื่อนไข"""
    validate_slots(slots)
    sql, params = _build_match_sql(skill_ids, slots, gender, traits)
    rows = _clean(query(sql, params))
    for r in rows:
        r["skills"] = r["skills"] or "-"
    return rows


def explain_excluded(skill_ids, slots, eligible_ids, gender=None, traits=None):
    """แท็บ 'ใครถูกตัดออก เพราะอะไร' : คืนรายชื่อนักแสดงที่ไม่ผ่าน พร้อมเหตุผลเป็นข้อความ"""
    skill_ids = sorted(set(skill_ids))
    eligible_ids = set(eligible_ids)
    # คนที่ปิดโปรไฟล์ไม่ถูกเอามาแสดง (ผู้จัดงานต้องไม่รู้ว่ามีใครซ่อนอยู่)
    actors = [a for a in list_actors(public_only=True) if a["actor_id"] not in eligible_ids]

    # ทักษะที่แต่ละคนมี (เฉพาะทักษะที่บทต้องการ)
    have = {}
    names = {}
    if skill_ids:
        for r in query(
            f"SELECT s.skill_id, s.skill_name FROM SKILL s WHERE s.skill_id IN ({_marks(skill_ids)})",
            skill_ids,
        ):
            names[r["skill_id"]] = r["skill_name"]
        for r in query(
            f"SELECT actor_id, skill_id FROM ACTOR_SKILL WHERE skill_id IN ({_marks(skill_ids)})",
            skill_ids,
        ):
            have.setdefault(r["actor_id"], set()).add(r["skill_id"])

    # คิวที่ชนของแต่ละคน
    conflicts = {}
    for s in slots:
        for r in query(
            f"SELECT r.actor_id, r.role_name, p.project_name, LEFT(s.start_time,5) AS st, "
            f"       LEFT(s.end_time,5) AS et "
            f"FROM `ROLE` r JOIN SCHEDULE s ON s.role_id = r.role_id "
            f"JOIN PROJECT p ON p.project_id = r.project_id "
            f"WHERE r.role_status IN {_BUSY} AND s.event_date = %s "
            f"  AND s.start_time < %s AND s.end_time > %s",
            (s["event_date"], s["end_time"], s["start_time"]),
        ):
            conflicts.setdefault(r["actor_id"], []).append(
                f"คิวชน: ติดงาน '{r['project_name']}' ({r['role_name']}) "
                f"{s['event_date']} {r['st']}-{r['et']}")

    result = []
    for a in actors:
        reasons = []
        if a["actor_status"] != "Active":
            reasons.append("สถานะ Inactive (พักงาน)")
        if gender and a["gender"] != gender:
            reasons.append("เพศไม่ตรงตัวกรอง")
        missing = [names[i] for i in skill_ids if i not in have.get(a["actor_id"], set())]
        if missing:
            reasons.append("ทักษะไม่ครบ: ขาด " + ", ".join(missing))
        reasons += trait_failures(a, traits)
        reasons += conflicts.get(a["actor_id"], [])
        if reasons:
            result.append({"actor_id": a["actor_id"], "full_name": a["full_name"], "reasons": reasons})
    return result


# =====================================================================
# ตรวจความถูกต้องของข้อมูลที่กรอก (ก่อนจะแตะ DB)
# =====================================================================
def validate_slots(slots):
    for i, s in enumerate(slots, 1):
        if s["end_time"] <= s["start_time"]:
            raise BusinessError(f"ตารางนัดแถวที่ {i}: เวลาเลิกต้องหลังเวลาเริ่ม")
    # ช่วงเวลาของบทเดียวกันห้ามซ้อนกันเอง (คนคนเดียวอยู่สองที่พร้อมกันไม่ได้)
    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            a, b = slots[i], slots[j]
            if (a["event_date"] == b["event_date"]
                    and a["start_time"] < b["end_time"] and a["end_time"] > b["start_time"]):
                raise BusinessError(f"ตารางนัดแถวที่ {i+1} และ {j+1} ซ้อนเวลากันเอง")


def validate_installments(installments, agreed_fee):
    if not installments:                       # ER: HAS_PAYMENT (1,N) ต้องมีอย่างน้อย 1 งวด
        raise BusinessError("ต้องมีงวดจ่ายเงินอย่างน้อย 1 งวด")
    total = sum((to_money(i["amount"]) for i in installments), Decimal("0.00"))
    for n, i in enumerate(installments, 1):
        if to_money(i["amount"]) <= 0:
            raise BusinessError(f"งวดที่ {n}: จำนวนเงินต้องมากกว่า 0")
    if total != to_money(agreed_fee):
        raise BusinessError(
            f"ยอดรวมทุกงวด ({total:,.2f}) ไม่เท่ากับค่าตัวที่ตกลง ({to_money(agreed_fee):,.2f})")


# =====================================================================
# [E] บทบาท (ตาราง ROLE, ROLE_SKILL, SCHEDULE, PAYMENT_INSTALLMENT)
# =====================================================================
def create_role(project_id, role_name, agreed_fee, actor_id, skill_ids, slots, installments):
    """ปุ่ม 'เลือกคนนี้' : เขียน 4 ตารางพร้อมกันใน transaction เดียว

    ลำดับ: ล็อกแถวนักแสดง -> ตรวจกฎซ้ำอีกรอบ -> INSERT ROLE -> ROLE_SKILL -> SCHEDULE -> PAYMENT_INSTALLMENT
    ที่ต้องตรวจซ้ำเพราะระหว่างที่ผู้จัดงานดูรายชื่ออยู่ อาจมีอีกคนเลือกนักแสดงคนเดียวกัน
    FOR UPDATE ทำให้คนที่สองต้องรอคนแรกทำเสร็จก่อน จึงไม่มีทางจองเวลาซ้อนกันได้
    """
    role_name = (role_name or "").strip()
    if not role_name:
        raise BusinessError("กรุณากรอกชื่อบท")
    if to_money(agreed_fee) <= 0:
        raise BusinessError("ค่าตัวต้องมากกว่า 0")
    skill_ids = sorted(set(skill_ids))
    validate_slots(slots)
    validate_installments(installments, agreed_fee)

    with transaction() as tx:
        # ขั้นแรกสุดต้องเป็น "ล็อกแถวนักแสดง" ก่อนอ่านอะไรอย่างอื่น
        # (ถ้าอ่านก่อน MySQL จะถ่าย snapshot ไว้ แล้วคนที่รอล็อกจะมองไม่เห็นบทที่อีกคนเพิ่งสร้าง
        #  ทำให้เช็กคิวชนพลาด -- เทสข้อ 13 จับได้)
        actor = tx.query("SELECT actor_status, is_public FROM ACTOR WHERE actor_id=%s FOR UPDATE", (actor_id,))
        if actor and not actor[0]["is_public"]:
            raise BusinessError("นักแสดงคนนี้ปิดโปรไฟล์อยู่ เลือกเข้าบทไม่ได้")
        if not actor or actor[0]["actor_status"] != "Active":
            raise BusinessError("นักแสดงคนนี้ไม่ได้อยู่ในสถานะ Active")

        proj = tx.query("SELECT project_status FROM PROJECT WHERE project_id=%s", (project_id,))
        if not proj or proj[0]["project_status"] in ("Completed", "Cancelled"):
            raise BusinessError("โปรเจกต์นี้ปิดแล้วหรือถูกยกเลิก เพิ่มบทไม่ได้")

        if skill_ids:
            got = tx.query(
                f"SELECT COUNT(DISTINCT skill_id) AS n FROM ACTOR_SKILL "
                f"WHERE actor_id=%s AND skill_id IN ({_marks(skill_ids)})",
                [actor_id] + skill_ids)[0]["n"]
            if got != len(skill_ids):
                raise BusinessError("นักแสดงมีทักษะไม่ครบตามที่บทต้องการ")

        for s in slots:
            hit = tx.query(
                f"SELECT p.project_name, r.role_name FROM `ROLE` r "
                f"JOIN SCHEDULE sc ON sc.role_id = r.role_id "
                f"JOIN PROJECT p ON p.project_id = r.project_id "
                f"WHERE r.actor_id=%s AND r.role_status IN {_BUSY} "
                f"  AND sc.event_date=%s AND sc.start_time < %s AND sc.end_time > %s LIMIT 1",
                (actor_id, s["event_date"], s["end_time"], s["start_time"]))
            if hit:
                raise BusinessError(
                    f"คิวชน! นักแสดงติดงาน '{hit[0]['project_name']}' ({hit[0]['role_name']}) "
                    f"ในวันที่ {s['event_date']} ช่วง {_hhmm(s['start_time'])}-{_hhmm(s['end_time'])}")

        _, role_id = tx.execute(
            "INSERT INTO `ROLE` (role_name, agreed_fee, role_status, actor_id, project_id) "
            "VALUES (%s, %s, 'Selected', %s, %s)",
            (role_name, to_money(agreed_fee), actor_id, project_id))
        for sid in skill_ids:
            tx.execute("INSERT INTO ROLE_SKILL (role_id, skill_id) VALUES (%s, %s)", (role_id, sid))
        for s in slots:
            tx.execute(
                "INSERT INTO SCHEDULE (event_type, event_date, start_time, end_time, role_id) "
                "VALUES (%s, %s, %s, %s, %s)",
                (s["event_type"], s["event_date"], s["start_time"], s["end_time"], role_id))
        for i in installments:
            tx.execute(
                "INSERT INTO PAYMENT_INSTALLMENT (amount, payment_status, due_date, role_id) "
                "VALUES (%s, 'Pending', %s, %s)",
                (to_money(i["amount"]), i["due_date"], role_id))
    return role_id


def respond_to_role(role_id, actor_id, accept):
    """ปุ่ม 'ยอมรับงาน' / 'ปฏิเสธงาน' ของนักแสดง
    เงื่อนไขใน WHERE : ต้องเป็นบทของตัวเอง และสถานะยังเป็น Selected (รอตอบ) เท่านั้น
    ถ้าปฏิเสธ -> งวดที่ยังไม่จ่ายของบทนี้ถูกยกเลิกด้วย"""
    new_status = "Confirmed" if accept else "Rejected_by_Actor"
    with transaction() as tx:
        n, _ = tx.execute(
            "UPDATE `ROLE` SET role_status=%s "
            "WHERE role_id=%s AND actor_id=%s AND role_status='Selected'",
            (new_status, role_id, actor_id))
        if n == 0:
            raise BusinessError("ตอบรับไปแล้ว หรือบทนี้ถูกยกเลิกแล้ว")
        if not accept:
            tx.execute(
                "UPDATE PAYMENT_INSTALLMENT SET payment_status='Cancelled' "
                "WHERE role_id=%s AND payment_status='Pending'", (role_id,))


def cancel_role(role_id):
    """ปุ่ม 'ยกเลิกการจ้าง' ของผู้จัดงาน (ทำได้แม้นักแสดงยืนยันไปแล้ว ตามขอบเขตในสไลด์)
    งวดที่จ่ายไปแล้ว (Paid) คงไว้เป็นประวัติ ส่วนงวดที่ยังรอจ่าย (Pending) -> Cancelled"""
    with transaction() as tx:
        n, _ = tx.execute(
            f"UPDATE `ROLE` SET role_status='Cancelled_by_Organizer' "
            f"WHERE role_id=%s AND role_status IN {_BUSY}", (role_id,))
        if n == 0:
            raise BusinessError("บทนี้ถูกปฏิเสธหรือยกเลิกไปแล้ว")
        tx.execute(
            "UPDATE PAYMENT_INSTALLMENT SET payment_status='Cancelled' "
            "WHERE role_id=%s AND payment_status='Pending'", (role_id,))


def roles_of_actor(actor_id):
    """หน้า 'งานของฉัน'"""
    return _clean(query(
        "SELECT r.role_id, r.role_name, r.agreed_fee, r.role_status, "
        "       p.project_name, p.project_type, p.client_name "
        "FROM `ROLE` r JOIN PROJECT p ON p.project_id = r.project_id "
        "WHERE r.actor_id=%s ORDER BY r.role_id DESC", (actor_id,)))


def all_roles(project_id=None):
    """หน้า 'จัดการบท' ของผู้จัดงาน : ROLE + PROJECT + ACTOR"""
    sql = ("SELECT r.role_id, r.role_name, r.agreed_fee, r.role_status, p.project_id, "
           "       p.project_name, a.actor_id, a.full_name "
           "FROM `ROLE` r JOIN PROJECT p ON p.project_id = r.project_id "
           "JOIN ACTOR a ON a.actor_id = r.actor_id")
    params = []
    if project_id:
        sql += " WHERE r.project_id = %s"
        params.append(project_id)
    return _clean(query(sql + " ORDER BY r.role_id DESC", params))


def required_skills_of_role(role_id):
    return query(
        "SELECT s.skill_name FROM ROLE_SKILL rs JOIN SKILL s ON s.skill_id = rs.skill_id "
        "WHERE rs.role_id=%s ORDER BY s.skill_name", (role_id,))


def schedule_of_role(role_id):
    return query(
        "SELECT event_type, event_date, LEFT(start_time,5) AS start_time, LEFT(end_time,5) AS end_time "
        "FROM SCHEDULE WHERE role_id=%s ORDER BY event_date, start_time", (role_id,))


def installments_of_role(role_id):
    return _clean(query(
        "SELECT payment_id, amount, payment_status, due_date, "
        "       (payment_status='Pending' AND due_date < CURDATE()) AS is_overdue "
        "FROM PAYMENT_INSTALLMENT WHERE role_id=%s ORDER BY due_date", (role_id,)))


# =====================================================================
# [F] ตารางนัดหมาย และ การจ่ายเงิน
# =====================================================================
def schedule_of_actor(actor_id):
    """หน้า 'ตารางนัดของฉัน' : SCHEDULE JOIN ROLE JOIN PROJECT (เฉพาะบทที่ยังไม่ถูกปฏิเสธ/ยกเลิก)"""
    return query(
        f"SELECT s.event_date, LEFT(s.start_time,5) AS start_time, LEFT(s.end_time,5) AS end_time, "
        f"       s.event_type, r.role_name, r.role_status, p.project_name "
        f"FROM SCHEDULE s JOIN `ROLE` r ON r.role_id = s.role_id "
        f"JOIN PROJECT p ON p.project_id = r.project_id "
        f"WHERE r.actor_id=%s AND r.role_status IN {_BUSY} "
        f"ORDER BY s.event_date, s.start_time", (actor_id,))


def payments_of_actor(actor_id):
    """หน้า 'การจ่ายเงินของฉัน' : PAYMENT_INSTALLMENT JOIN ROLE JOIN PROJECT
    is_overdue คำนวณตอน query (Pending และเลยวันครบกำหนด) ไม่ได้เก็บเป็นคอลัมน์"""
    return _clean(query(
        "SELECT pi.payment_id, p.project_name, r.role_name, pi.amount, pi.due_date, "
        "       pi.payment_status, (pi.payment_status='Pending' AND pi.due_date < CURDATE()) AS is_overdue "
        "FROM PAYMENT_INSTALLMENT pi JOIN `ROLE` r ON r.role_id = pi.role_id "
        "JOIN PROJECT p ON p.project_id = r.project_id "
        "WHERE r.actor_id=%s ORDER BY pi.due_date", (actor_id,)))


def list_payments(status=None, overdue_only=False, project_id=None):
    """หน้า 'งวดจ่ายเงิน' ของผู้จัดงาน (กรองได้)"""
    sql = ("SELECT pi.payment_id, p.project_name, r.role_name, a.full_name, r.role_status, "
           "       pi.amount, pi.due_date, pi.payment_status, "
           "       (pi.payment_status='Pending' AND pi.due_date < CURDATE()) AS is_overdue "
           "FROM PAYMENT_INSTALLMENT pi JOIN `ROLE` r ON r.role_id = pi.role_id "
           "JOIN PROJECT p ON p.project_id = r.project_id "
           "JOIN ACTOR a ON a.actor_id = r.actor_id WHERE 1=1")
    params = []
    if status:
        sql += " AND pi.payment_status = %s"
        params.append(status)
    if overdue_only:
        sql += " AND pi.payment_status = 'Pending' AND pi.due_date < CURDATE()"
    if project_id:
        sql += " AND r.project_id = %s"
        params.append(project_id)
    return _clean(query(sql + " ORDER BY pi.due_date", params))


def mark_paid(payment_id):
    """ปุ่ม 'บันทึกว่าจ่ายแล้ว' -- จุดกันจ่ายซ้ำ

    UPDATE มีเงื่อนไข payment_status='Pending' ใน WHERE
    ครั้งแรก  : Pending -> Paid  (แก้ 1 แถว)
    กดซ้ำ     : ไม่มีแถวไหนตรงเงื่อนไข (แก้ 0 แถว) -> ระบบปฏิเสธ
    และจ่ายได้เฉพาะบทที่นักแสดงยืนยันแล้ว (Confirmed) เท่านั้น"""
    n, _ = execute(
        "UPDATE PAYMENT_INSTALLMENT pi JOIN `ROLE` r ON r.role_id = pi.role_id "
        "SET pi.payment_status='Paid' "
        "WHERE pi.payment_id=%s AND pi.payment_status='Pending' AND r.role_status='Confirmed'",
        (payment_id,))
    if n == 0:
        row = query(
            "SELECT pi.payment_status, r.role_status FROM PAYMENT_INSTALLMENT pi "
            "JOIN `ROLE` r ON r.role_id = pi.role_id WHERE pi.payment_id=%s", (payment_id,))
        if not row:
            raise BusinessError("ไม่พบงวดนี้")
        if row[0]["payment_status"] == "Paid":
            raise BusinessError("งวดนี้จ่ายไปแล้ว จ่ายซ้ำไม่ได้")
        if row[0]["payment_status"] == "Cancelled":
            raise BusinessError("งวดนี้ถูกยกเลิกแล้ว")
        raise BusinessError("จ่ายได้เฉพาะบทที่นักแสดงยืนยันแล้ว (Confirmed)")


# =====================================================================
# [G] ค้นหานักแสดง (หน้า 'ค้นหานักแสดง')
# =====================================================================
def search_actors(gender=None, skill_ids=(), text=None, avail=None, only_active=True, traits=None):
    """กรองได้พร้อมกันหลายเงื่อนไข: เพศ / ทักษะ (ต้องมีครบ) / คำในรายละเอียดรูปลักษณ์ / ว่างในช่วงเวลา
    / ตัวกรองรูปลักษณ์ (traits : อายุ ส่วนสูง สีผม สีผิว ฯลฯ)
    avail = {"event_date": date, "start_time": time, "end_time": time} หรือ None"""
    skill_ids = sorted(set(skill_ids))
    sql = f"SELECT {_ACTOR_COLS} FROM ACTOR a WHERE 1=1{_PUBLIC}"      # คนที่ปิดโปรไฟล์จะไม่โผล่ในผลค้นหา
    params = []
    if only_active:
        sql += " AND a.actor_status = 'Active'"
    t_sql, t_params = _traits_sql(traits)
    sql += t_sql
    params += t_params
    if gender:
        sql += " AND a.gender = %s"
        params.append(gender)
    if text:
        sql += " AND (a.appearance_detail LIKE %s OR a.full_name LIKE %s)"
        params += [f"%{text.strip()}%"] * 2
    if skill_ids:
        sql += (f" AND (SELECT COUNT(DISTINCT ak.skill_id) FROM ACTOR_SKILL ak "
                f"WHERE ak.actor_id = a.actor_id AND ak.skill_id IN ({_marks(skill_ids)})) = %s")
        params += skill_ids + [len(skill_ids)]
    if avail:
        if avail["end_time"] <= avail["start_time"]:
            raise BusinessError("เวลาสิ้นสุดต้องหลังเวลาเริ่ม")
        sql += _CONFLICT_NOT_EXISTS
        params += [avail["event_date"], avail["end_time"], avail["start_time"]]
    rows = _clean(query(sql + " ORDER BY a.full_name", params))
    for r in rows:
        r["skills"] = r["skills"] or "-"
    return rows


# =====================================================================
# [H] Dashboard
# =====================================================================
def dashboard_numbers():
    d = {}
    d["actors_by_status"] = query(
        "SELECT actor_status AS status, COUNT(*) AS n FROM ACTOR GROUP BY actor_status")
    d["projects_by_status"] = query(
        "SELECT project_status AS status, COUNT(*) AS n FROM PROJECT GROUP BY project_status")
    d["roles_by_status"] = query(
        "SELECT role_status AS status, COUNT(*) AS n FROM `ROLE` GROUP BY role_status")
    d["overdue"] = _clean(query(
        "SELECT COUNT(*) AS n, COALESCE(SUM(amount),0) AS total FROM PAYMENT_INSTALLMENT "
        "WHERE payment_status='Pending' AND due_date < CURDATE()"))[0]
    d["payments_by_status"] = _clean(query(
        "SELECT payment_status AS status, COUNT(*) AS n, COALESCE(SUM(amount),0) AS total "
        "FROM PAYMENT_INSTALLMENT GROUP BY payment_status"))
    d["skill_popularity"] = query(
        "SELECT s.skill_name, COUNT(ak.actor_id) AS actors "
        "FROM SKILL s LEFT JOIN ACTOR_SKILL ak ON ak.skill_id = s.skill_id "
        "GROUP BY s.skill_id, s.skill_name ORDER BY actors DESC, s.skill_name")
    d["payments_by_project"] = _clean(query(
        "SELECT p.project_name, "
        "       COALESCE(SUM(CASE WHEN pi.payment_status='Paid'    THEN pi.amount END),0) AS paid, "
        "       COALESCE(SUM(CASE WHEN pi.payment_status='Pending' THEN pi.amount END),0) AS pending "
        "FROM PROJECT p LEFT JOIN `ROLE` r ON r.project_id = p.project_id "
        "LEFT JOIN PAYMENT_INSTALLMENT pi ON pi.role_id = r.role_id "
        "GROUP BY p.project_id, p.project_name ORDER BY p.project_id"))
    return d
