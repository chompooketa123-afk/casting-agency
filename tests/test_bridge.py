"""
tests/test_bridge.py : ทดสอบตัวกลางหน้าเว็บ <-> MySQL (bridge.py) กับ DB จริง
วิธีรัน:  python tests/test_bridge.py   (ต้องรัน python setup_db.py ก่อน และจะรีเซ็ตข้อมูลตัวอย่างให้เอง)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
subprocess.run([sys.executable, str(ROOT / "setup_db.py")], check=True, capture_output=True)

import bridge  # noqa: E402

ok = 0


def check(name, cond):
    global ok
    print(("  ผ่าน  " if cond else "  ไม่ผ่าน  ") + name)
    ok += bool(cond)


snap = bridge.snapshot()
check("snapshot อ่านครบทุกตาราง", all(snap[k] for k in ("skills", "actors", "projects", "roles")))
check("snapshot มีวันที่แบบ ISO และเวลา HH:MM", snap["roles"][0]["sched"][0]["date"][4] == "-" and snap["roles"][0]["sched"][0]["start"][2] == ":")

pid = bridge.handle("createProject", {"name": "ทดสอบ", "type": "Series", "client": "ลูกค้า"})
check("createProject สำเร็จและบอก id", pid["ok"] and isinstance(pid["result"], int))
check("สถานะโปรเจกต์เปลี่ยนได้", bridge.handle("setProjectStatus", {"id": pid["result"], "status": "In_Progress"})["ok"])

r = bridge.handle("registerActor", {"f": {"name": "เด็ก", "gender": "Female", "birth": "2015-01-01"}, "skills": [], "publish": False})
check("ผู้สมัครอายุต่ำกว่า 18 ถูกปฏิเสธที่ฝั่งเซิร์ฟเวอร์", (not r["ok"]) and "18" in r["error"])
r = bridge.handle("registerActor", {"f": {"name": "ทดสอบ", "gender": "Female", "birth": "2000-01-01", "h": "170"}, "skills": [1], "publish": True})
aid = r["result"]
check("สมัครนักแสดง + เปิดโปรไฟล์ได้เมื่อมีทักษะ", r["ok"] and next(a for a in bridge.snapshot()["actors"] if a["id"] == aid)["pub"])
r = bridge.handle("deleteWork", {"aid": aid, "wid": 99999})
check("ลบผลงานที่ไม่ใช่ของตัวเองไม่ได้", not r["ok"])

slots = [{"type": "Shoot", "date": "2030-01-05", "start": "09:00", "end": "17:00"}]
inst = [{"due": "2030-01-10", "amount": 1000}]
m = {"project": pid["result"], "roleName": "บทแรก", "fee": 1000, "skills": [1], "slots": slots, "inst": inst}
r1 = bridge.handle("createRole", {"m": m, "actor": aid})
check("createRole เขียน ROLE + งวด + นัด และคืนรหัสบท", r1["ok"] and "ROLE" in r1["touch"] and len(r1["sql"]) >= 4)
r2 = bridge.handle("createRole", {"m": {**m, "roleName": "บทชน"}, "actor": aid})
check("จองซ้อนเวลาเดิมถูกปฏิเสธ (คิวชน)", (not r2["ok"]) and "คิวชน" in r2["error"])
r = bridge.handle("createRole", {"m": {**m, "inst": [{"due": "2030-01-10", "amount": 5}]}, "actor": aid})
check("ยอดงวดไม่เท่าค่าตัวถูกปฏิเสธ", not r["ok"])
check("ยอมรับงานได้", bridge.handle("respondRole", {"rid": r1["result"], "actor": aid, "accept": True})["ok"])
pay_id = next(p["id"] for ro in bridge.snapshot()["roles"] if ro["id"] == r1["result"] for p in ro["pay"])
check("จ่ายงวดได้ครั้งแรก", bridge.handle("markPaid", {"pid": pay_id})["ok"])
r = bridge.handle("markPaid", {"pid": pay_id})
check("กดจ่ายซ้ำถูกปฏิเสธ", (not r["ok"]) and "จ่ายซ้ำ" in r["error"])
r = bridge.handle("hackIt", {})
check("คำสั่งที่ไม่รู้จักถูกปฏิเสธ", not r["ok"])

print(f"\nผ่าน {ok} / 14 ข้อ")
sys.exit(0 if ok == 14 else 1)
