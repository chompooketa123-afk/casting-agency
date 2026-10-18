"""
bridge.py : ตัวกลางระหว่าง "หน้าเว็บ" (ui/app.js) กับ MySQL

หน้าเว็บ (JavaScript) ไม่แตะฐานข้อมูลเอง ทุกปุ่มที่ต้องบันทึกจะส่งคำสั่งมาที่นี่
  1) handle(op, args)  รับคำสั่ง (เช่น "createRole") -> เรียกฟังก์ชันใน queries.py
                       ซึ่งรัน SQL จริง + ตรวจกฎธุรกิจทั้งหมด (คิวชน ทักษะครบ กันจ่ายซ้ำ ฯลฯ) ที่ฝั่งเซิร์ฟเวอร์
  2) snapshot()        อ่านทุกตารางจาก MySQL แล้วส่งกลับไปให้หน้าเว็บวาดใหม่
                       (ทุกคนในกลุ่มจึงเห็นข้อมูลชุดเดียวกัน)
กฎใน queries.py คือกฎจริง ถ้าหน้าเว็บตรวจพลาด ฝั่งนี้จะปฏิเสธอีกชั้น
"""
from datetime import date, time

import mysql.connector

import db
import queries as q


def _d(s):
    return date.fromisoformat(s) if s else None


def _t(s):
    return time.fromisoformat(s) if s else None


def _num(v):
    return None if v in ("", None) else v


# ---------------------------------------------------------------------
# อ่านข้อมูลทั้งหมด -> dict ที่หน้าเว็บเอาไปวาด
# ---------------------------------------------------------------------
def snapshot():
    Q = lambda sql: db.query(sql, log=False)          # noqa: E731  (ไม่จดลง SQL log เพราะเป็นการอ่านเพื่อวาดหน้า)
    f = lambda x: None if x is None else float(x)     # noqa: E731
    skills = [{"id": r["skill_id"], "name": r["skill_name"], "type": r["skill_type"]}
              for r in Q("SELECT skill_id, skill_name, skill_type FROM SKILL ORDER BY skill_id")]
    aks, works = {}, {}
    for r in Q("SELECT actor_id, skill_id FROM ACTOR_SKILL ORDER BY skill_id"):
        aks.setdefault(r["actor_id"], []).append(r["skill_id"])
    for r in Q("SELECT * FROM PORTFOLIO ORDER BY work_id"):
        works.setdefault(r["actor_id"], []).append({
            "id": r["work_id"], "title": r["title"], "type": r["work_type"], "role": r["role_played"] or "",
            "year": r["work_year"], "desc": r["description"] or "", "url": r["link_url"] or ""})
    actors = [{
        "id": r["actor_id"], "name": r["full_name"], "gender": r["gender"], "status": r["actor_status"],
        "look": r["appearance_detail"] or "", "bio": r["bio"] or "", "pub": bool(r["is_public"]),
        "birth": r["birth_date"].isoformat() if r["birth_date"] else None,
        "h": r["height_cm"], "w": f(r["weight_kg"]), "bust": r["bust_chest_cm"], "waist": r["waist_cm"], "hip": r["hip_cm"],
        "shoe": f(r["shoe_size_eu"]), "size": r["clothing_size"], "body": r["body_type"], "skin": r["skin_tone"],
        "hairC": r["hair_color"], "hairL": r["hair_length"], "hairT": r["hair_texture"], "eye": r["eye_color"],
        "tattoo": bool(r["has_tattoo"]), "pierce": bool(r["has_piercing"]), "exp": r["experience_level"],
        "prov": r["province"], "travel": bool(r["can_travel"]),
        "skills": aks.get(r["actor_id"], []), "works": works.get(r["actor_id"], []),
    } for r in Q("SELECT * FROM ACTOR ORDER BY actor_id")]
    projects = [{"id": r["project_id"], "name": r["project_name"], "type": r["project_type"],
                 "status": r["project_status"], "client": r["client_name"]}
                for r in Q("SELECT * FROM PROJECT ORDER BY project_id")]
    rs, sched, pay = {}, {}, {}
    for r in Q("SELECT * FROM ROLE_SKILL"):
        rs.setdefault(r["role_id"], []).append(r["skill_id"])
    for r in Q("SELECT * FROM SCHEDULE ORDER BY event_date, start_time"):
        sched.setdefault(r["role_id"], []).append({
            "type": r["event_type"], "date": r["event_date"].isoformat(),
            "start": q._hhmm(_as_time(r["start_time"])), "end": q._hhmm(_as_time(r["end_time"]))})
    for r in Q("SELECT * FROM PAYMENT_INSTALLMENT ORDER BY due_date, payment_id"):
        pay.setdefault(r["role_id"], []).append({
            "id": r["payment_id"], "amount": float(r["amount"]), "status": r["payment_status"], "due": r["due_date"].isoformat()})
    roles = [{"id": r["role_id"], "name": r["role_name"], "fee": float(r["agreed_fee"]), "status": r["role_status"],
              "actor": r["actor_id"], "project": r["project_id"], "skills": rs.get(r["role_id"], []),
              "sched": sched.get(r["role_id"], []), "pay": pay.get(r["role_id"], [])}
             for r in Q("SELECT * FROM `ROLE` ORDER BY role_id")]
    return {"skills": skills, "actors": actors, "projects": projects, "roles": roles}


def _as_time(v):
    """MySQL คืน TIME เป็น timedelta (บางเวอร์ชันเป็น time) -> time"""
    if isinstance(v, time):
        return v
    secs = int(v.total_seconds())
    return time(secs // 3600 % 24, secs // 60 % 60)


# ---------------------------------------------------------------------
# คำสั่งจากหน้าเว็บ -> queries.py
# ---------------------------------------------------------------------
def _profile(f):
    """ชื่อช่องในหน้าเว็บ -> ชื่อคอลัมน์ในตาราง ACTOR"""
    return {
        "birth_date": _d(f.get("birth")), "height_cm": _num(f.get("h")), "weight_kg": _num(f.get("w")),
        "bust_chest_cm": _num(f.get("bust")), "waist_cm": _num(f.get("waist")), "hip_cm": _num(f.get("hip")),
        "shoe_size_eu": _num(f.get("shoe")), "clothing_size": f.get("size"), "body_type": f.get("body"),
        "skin_tone": f.get("skin"), "hair_color": f.get("hairC"), "hair_length": f.get("hairL"),
        "hair_texture": f.get("hairT"), "eye_color": f.get("eye"), "has_tattoo": bool(f.get("tattoo")),
        "has_piercing": bool(f.get("pierce")), "experience_level": f.get("exp"), "province": f.get("prov"),
        "can_travel": bool(f.get("travel")),
    }


def _work(w):
    return (w.get("title"), w.get("type"), w.get("role"), w.get("year"), w.get("desc"), w.get("url"))


def _register(a):
    f = a["f"]
    return q.register_actor(f.get("name"), f.get("gender") or "Female", f.get("look"), a["skills"],
                            profile=_profile(f), bio=f.get("bio"), publish=bool(a.get("publish")))


def _update(a):
    f = a["f"]
    return q.update_actor(a["id"], f.get("name"), f.get("gender"), f.get("status") or "Active", f.get("look"),
                          a["skills"], profile=_profile(f), bio=f.get("bio"))


def _create_role(a):
    m = a["m"]
    slots = [{"event_type": s["type"], "event_date": _d(s["date"]), "start_time": _t(s["start"]), "end_time": _t(s["end"])}
             for s in m["slots"]]
    inst = [{"amount": i["amount"], "due_date": _d(i["due"])} for i in m["inst"]]
    return q.create_role(m["project"], m["roleName"], m["fee"], a["actor"], m["skills"], slots, inst)


OPS = {
    "refresh": lambda a: None,
    "registerActor": _register,
    "updateActor": _update,
    "setPublic": lambda a: q.set_profile_public(a["id"], bool(a["pub"])),
    "addWork": lambda a: q.add_work(a["aid"], *_work(a["w"])),
    "updateWork": lambda a: q.update_work(a["aid"], a["wid"], *_work(a["w"])),
    "deleteWork": lambda a: q.delete_work(a["aid"], a["wid"]),
    "createProject": lambda a: q.create_project(a["name"], a["type"], a["client"]),
    "setProjectStatus": lambda a: q.update_project_status(a["id"], a["status"]),
    "createRole": _create_role,
    "respondRole": lambda a: q.respond_to_role(a["rid"], a["actor"], bool(a["accept"])),
    "cancelRole": lambda a: q.cancel_role(a["rid"]),
    "markPaid": lambda a: q.mark_paid(a["pid"]),
}
# ชื่อตารางที่แต่ละคำสั่งแตะ (โชว์ใต้หน้าเว็บให้อาจารย์ดู)
TOUCH = {
    "registerActor": "ACTOR, ACTOR_SKILL", "updateActor": "ACTOR, ACTOR_SKILL", "setPublic": "ACTOR",
    "addWork": "PORTFOLIO", "updateWork": "PORTFOLIO", "deleteWork": "PORTFOLIO, ACTOR",
    "createProject": "PROJECT", "setProjectStatus": "PROJECT",
    "createRole": "ROLE, ROLE_SKILL, SCHEDULE, PAYMENT_INSTALLMENT", "respondRole": "ROLE, PAYMENT_INSTALLMENT",
    "cancelRole": "ROLE, PAYMENT_INSTALLMENT", "markPaid": "PAYMENT_INSTALLMENT",
}


def handle(op, args):
    """รันคำสั่งหนึ่งอัน -> dict {ok, result, error, sql, touch}"""
    db.clear_sql_log()
    out = {"op": op, "ok": True, "result": None, "error": None}
    try:
        fn = OPS.get(op)
        if fn is None:
            raise q.BusinessError("ไม่รู้จักคำสั่ง " + str(op))
        res = fn(args or {})
        out["result"] = res if isinstance(res, (int, bool, str, type(None))) else None
    except q.BusinessError as e:
        out.update(ok=False, error=str(e))
    except mysql.connector.Error as e:
        out.update(ok=False, error=f"ฐานข้อมูลขัดข้อง: {e}")
    except Exception as e:      # noqa: BLE001  (ข้อมูลจากหน้าเว็บผิดรูปแบบ ฯลฯ)
        out.update(ok=False, error=f"ข้อมูลไม่ถูกต้อง: {e}")
    out["sql"] = [{"sql": s, "params": [str(x) for x in (p or [])] if not isinstance(p, dict) else []} for s, p in db.get_sql_log()][-14:]
    out["touch"] = TOUCH.get(op, "")
    db.clear_sql_log()
    return out
