"""
tests/test_pages.py : เปิดทุกหน้าเว็บแล้ว "กดปุ่มจริง" ด้วย Streamlit AppTest (ไม่ต้องเปิดเบราว์เซอร์)
แล้วเช็กผลในฐานข้อมูลว่าเปลี่ยนตามที่ควรเป็น

วิธีรัน (ที่โฟลเดอร์ casting-app):
    python tests/test_pages.py
ไฟล์นี้รีเซ็ตข้อมูลเป็นข้อมูลตัวอย่างก่อนเริ่มทุกครั้ง
"""
import subprocess
from datetime import date, timedelta
import sys

# ให้พิมพ์ภาษาไทยในหน้าต่าง Terminal ของ Windows ได้ไม่เพี้ยน
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest   # noqa: E402

from db import query   # noqa: E402

PASSED, FAILED = [], []


def page(name):
    return AppTest.from_file(str(ROOT / "classic_pages" / name), default_timeout=30)


def as_actor(at, actor_id):
    """จำลองการเลือกชื่อใน dropdown ที่แถบด้านข้าง"""
    at.session_state["current_actor_id"] = actor_id
    return at.run()


def no_exception(at):
    errs = [e.value for e in at.exception]
    assert not errs, errs


def test(name):
    def deco(fn):
        try:
            fn()
            PASSED.append(name)
            print(f"  ผ่าน  {name}")
        except Exception as e:   # noqa: BLE001
            FAILED.append(name)
            print(f"  ไม่ผ่าน  {name}\n        -> {type(e).__name__}: {e}")
        return fn
    return deco


def role_status(role_id):
    return query("SELECT role_status s FROM `ROLE` WHERE role_id=%s", (role_id,))[0]["s"]


print("รีเซ็ตฐานข้อมูล ...")
subprocess.run([sys.executable, str(ROOT / "setup_db.py")], check=True, stdout=subprocess.DEVNULL)
print("เริ่มทดสอบหน้าเว็บ\n")


@test("เปิดทุกหน้าได้โดยไม่มี error (ในฐานะนักแสดงหลายคน)")
def _():
    for name in ["talent.py", "dashboard.py", "org_projects.py", "org_casting.py", "org_roles.py",
                 "org_payments.py", "org_search.py", "actor_register.py"]:
        no_exception(page(name).run())
    for actor_id in (1, 2, 3, 5, 8, 14, 37):
        for name in ["actor_jobs.py", "actor_schedule.py", "actor_payments.py", "actor_profile.py"]:
            no_exception(as_actor(page(name), actor_id))


@test("นักแสดงกด 'ยอมรับงาน' -> role_status เป็น Confirmed ใน DB")
def _():
    assert role_status(3) == "Selected"
    at = as_actor(page("actor_jobs.py"), 3)
    at.button(key="acc_3").click().run()
    no_exception(at)
    assert role_status(3) == "Confirmed"


@test("นักแสดงกด 'ปฏิเสธงาน' -> Rejected_by_Actor และงวดที่ค้างถูกยกเลิก")
def _():
    # สร้างบทใหม่ให้นักแสดงคนที่ 15 ผ่านหน้าสร้างบท (ทดสอบทางอ้อม) -> ใช้ query ตรง
    import queries as q
    from datetime import time
    rid = q.create_role(2, "บททดสอบปฏิเสธ", 1000, 15, [], [], [{"due_date": date.today() + timedelta(days=9), "amount": 1000}])
    at = as_actor(page("actor_jobs.py"), 15)
    at.button(key=f"rej_{rid}").click().run()
    no_exception(at)
    assert role_status(rid) == "Rejected_by_Actor"
    st = {r["payment_status"] for r in query("SELECT payment_status FROM PAYMENT_INSTALLMENT WHERE role_id=%s", (rid,))}
    assert st == {"Cancelled"}


@test("ผู้จัดงานกด 'บันทึกว่าจ่ายแล้ว' -> Paid ใน DB และงวดนั้นไม่มีปุ่มจ่ายอีก")
def _():
    pid = query("SELECT payment_id FROM PAYMENT_INSTALLMENT WHERE role_id=4 AND payment_status='Pending'")[0]["payment_id"]
    at = page("org_payments.py").run()
    at.button(key=f"pay_{pid}").click().run()
    no_exception(at)
    assert query("SELECT payment_status s FROM PAYMENT_INSTALLMENT WHERE payment_id=%s", (pid,))[0]["s"] == "Paid"
    at = page("org_payments.py").run()
    assert not [b for b in at.button if b.key == f"pay_{pid}"], "ยังมีปุ่มจ่ายของงวดที่จ่ายแล้ว"


@test("ผู้จัดงานยกเลิกการจ้างหลังยืนยัน (ต้องติ๊กยืนยันก่อนปุ่มถึงกดได้)")
def _():
    at = page("org_roles.py").run()
    assert at.button(key="cancel_2").disabled is True
    at.checkbox(key="sure_2").check().run()
    assert at.button(key="cancel_2").disabled is False
    at.button(key="cancel_2").click().run()
    no_exception(at)
    assert role_status(2) == "Cancelled_by_Organizer"


@test("หน้าจับคู่: กรอกบท -> ค้นหา -> เลือกคนนี้ -> ROLE ถูกสร้างและ 'ไม่' มีคนคิวชนในรายชื่อ")
def _():
    # เตรียมสถานการณ์เดียวกับ demo: สมหญิงติด 09-17 ใน +7 วัน (บท 1 ยังยืนยันอยู่)
    at = page("org_casting.py").run()
    no_exception(at)
    at.text_input[0].set_value("เพื่อนสนิท").run()
    at.multiselect(key="need_sk_Performance").set_value([6])        # ดราม่า
    at.multiselect(key="need_sk_Language").set_value([1]).run()   # อังกฤษ
    search = [b for b in at.button if "ค้นหา" in b.label][0]
    search.click().run()
    no_exception(at)
    match = at.session_state["match"]
    names = {a["full_name"] for a in match["eligible"]}
    assert "สมหญิง ใจดี" not in names, "สมหญิงติดถ่ายทำ 09-17 ควรถูกตัดออก"
    assert names, "ควรมีนักแสดงที่ผ่านเกณฑ์"
    pick = [b for b in at.button if b.key and b.key.startswith("pick_")][0]
    actor_id = int(pick.key.split("_")[1])
    before = query("SELECT COUNT(*) n FROM `ROLE`")[0]["n"]
    pick.click().run()
    no_exception(at)
    assert query("SELECT COUNT(*) n FROM `ROLE`")[0]["n"] == before + 1
    new = query("SELECT * FROM `ROLE` WHERE role_name='เพื่อนสนิท'")[0]
    assert new["actor_id"] == actor_id and new["role_status"] == "Selected"
    assert query("SELECT COUNT(*) n FROM PAYMENT_INSTALLMENT WHERE role_id=%s", (new["role_id"],))[0]["n"] == 2


@test("หน้าจับคู่: ยอดงวดไม่เท่าค่าตัว -> ขึ้น error และไม่มีผลค้นหา")
def _():
    at = page("org_casting.py").run()
    at.text_input[0].set_value("ทดสอบยอด").run()
    at.number_input[0].set_value(77777.0).run()                  # ค่าตัวไม่เท่ายอดงวด (50,000)
    [b for b in at.button if "ค้นหา" in b.label][0].click().run()
    assert any("ไม่เท่ากับค่าตัว" in e.value for e in at.error)
    assert "match" not in at.session_state


@test("หน้าสมัครนักแสดง: กรอกฟอร์มแล้ว INSERT ACTOR + ACTOR_SKILL")
def _():
    at = page("actor_register.py").run()
    at.text_input(key="reg0_name").set_value("ผู้สมัคร ทดสอบ")
    at.selectbox(key="reg0_hc").set_value("Red")
    at.number_input(key="reg0_h").set_value(171)
    at.multiselect(key="reg0_sk_Language").set_value([1])
    at.multiselect(key="reg0_sk_Performance").set_value([5]).run()
    [b for b in at.button if b.label == "สมัครเป็นนักแสดง"][0].click().run()
    no_exception(at)
    row = query("SELECT actor_id FROM ACTOR WHERE full_name='ผู้สมัคร ทดสอบ'")
    assert len(row) == 1
    n = query("SELECT COUNT(*) n FROM ACTOR_SKILL WHERE actor_id=%s", (row[0]["actor_id"],))[0]["n"]
    assert n == 2
    saved = query("SELECT hair_color, height_cm, is_public, TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) age FROM ACTOR WHERE actor_id=%s",
                  (row[0]["actor_id"],))[0]
    assert saved["hair_color"] == "Red" and saved["height_cm"] == 171 and saved["age"] >= 18
    assert saved["is_public"] == 1          # ติ๊กเผยแพร่ไว้ (ค่าเริ่มต้น) และมีทักษะ -> คนอื่นเห็น


@test("หน้าสร้างโปรเจกต์ และหน้าค้นหานักแสดง ทำงานได้")
def _():
    at = page("org_projects.py").run()
    at.text_input[0].set_value("โปรเจกต์ผ่านหน้าเว็บ")
    at.text_input[1].set_value("ลูกค้า ก.")
    [b for b in at.button if b.label == "สร้างโปรเจกต์"][0].click().run()
    no_exception(at)
    assert query("SELECT COUNT(*) n FROM PROJECT WHERE project_name='โปรเจกต์ผ่านหน้าเว็บ'")[0]["n"] == 1
    at = page("org_search.py").run()
    at.multiselect(key="srch_sk_Performance").set_value([5])
    [b for b in at.button if b.label == "ค้นหา"][0].click().run()
    no_exception(at)
    assert any("พบ" in s.value for s in at.success)


@test("หน้าแคตตาล็อก: แสดงการ์ด, กรองสีผมแล้วเหลือเฉพาะที่ตรง, เปิดโปรไฟล์ได้")
def _():
    at = page("talent.py").run()
    no_exception(at)
    all_cards = [b for b in at.button if b.key and b.key.startswith("view_")]
    assert len(all_cards) == 12                                   # แสดงทีละ 12 ใบ
    at.multiselect(key="cat_hair_colors").set_value(["Blonde"]).run()
    no_exception(at)
    cards = [b for b in at.button if b.key and b.key.startswith("view_")]
    ids = {int(b.key.split("_")[1]) for b in cards}
    assert ids and ids == {r["actor_id"] for r in query("SELECT actor_id FROM ACTOR WHERE hair_color='Blonde' AND actor_status='Active'")}
    cards[0].click().run()                                        # เปิด st.dialog โปรไฟล์
    no_exception(at)


@test("หน้าแรกและ Dashboard โหลดได้ (มีข้อมูลสดจาก DB)")
def _():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app_classic.py"), default_timeout=60).run()    # หน้าแรกต้องรันผ่าน app.py (มี st.navigation)
    no_exception(at)
    no_exception(page("dashboard.py").run())


def btn(at, label):
    return [b for b in at.button if b.label == label][0]


def in_catalog(name):
    """ค้นชื่อในหน้าแคตตาล็อก (เหมือนที่ผู้จัดงานทำ) แล้วบอกว่าเจอการ์ดไหม"""
    at = page("talent.py").run()
    no_exception(at)
    at.text_input(key="cat_text").set_value(name).run()
    no_exception(at)
    return any(b.key and b.key.startswith("view_") for b in at.button)


@test("หน้าแคตตาล็อก: คนที่ยังไม่ได้ใส่อะไร (ซ่อนอยู่) ไม่โผล่ ส่วนคนที่เผยแพร่แล้วโผล่")
def _():
    assert not in_catalog("นภัส") and not in_catalog("ธีรพล")
    assert in_catalog("สมหญิง")


@test("หน้าโปรไฟล์ของฉัน: ซ่อนอยู่ปุ่มเผยแพร่กดไม่ได้ -> เพิ่มผลงานแล้วเผยแพร่ได้ -> คนอื่นเห็น -> ลบผลงาน (ไม่มีทักษะ) โปรไฟล์ปิดเอง")
def _():
    aid = 37
    at = as_actor(page("actor_profile.py"), aid)
    no_exception(at)
    assert btn(at, "เผยแพร่โปรไฟล์").disabled                       # ยังไม่ได้ใส่อะไร = กดเผยแพร่ไม่ได้
    # เพิ่มผลงาน 1 ชิ้นผ่านฟอร์มจริง
    at.text_input(key="addw37_0_t").set_value("ภาพยนตร์ 'ทดสอบ'")
    at.selectbox(key="addw37_0_ty").set_value("Film")
    at.text_input(key="addw37_0_r").set_value("นำหญิง").run()
    btn(at, "เพิ่มผลงาน").click().run()
    no_exception(at)
    assert query("SELECT COUNT(*) n FROM PORTFOLIO WHERE actor_id=%s", (aid,))[0]["n"] == 1
    assert not btn(at, "เผยแพร่โปรไฟล์").disabled                    # มีผลงานแล้ว -> เผยแพร่ได้
    assert query("SELECT is_public FROM ACTOR WHERE actor_id=%s", (aid,))[0]["is_public"] == 0
    btn(at, "เผยแพร่โปรไฟล์").click().run()
    no_exception(at)
    assert query("SELECT is_public FROM ACTOR WHERE actor_id=%s", (aid,))[0]["is_public"] == 1
    assert in_catalog("นภัส")                       # คนอื่นเห็นแล้ว
    # ลบผลงาน (ไม่มีทักษะ) -> เหลือไม่มีอะไรเลย -> ระบบปิดโปรไฟล์เอง
    wid = query("SELECT work_id FROM PORTFOLIO WHERE actor_id=%s", (aid,))[0]["work_id"]
    btn(at, "ลบผลงานนี้").click().run()
    no_exception(at)
    assert query("SELECT COUNT(*) n FROM PORTFOLIO WHERE work_id=%s", (wid,))[0]["n"] == 0
    assert query("SELECT is_public FROM ACTOR WHERE actor_id=%s", (aid,))[0]["is_public"] == 0
    assert not in_catalog("นภัส")


@test("หน้าโปรไฟล์ของฉัน: กด 'ซ่อนโปรไฟล์' แล้วหายจากแคตตาล็อก, บันทึกชื่อ/แนะนำตัว/แท็กลง DB")
def _():
    aid = 3
    at = as_actor(page("actor_profile.py"), aid)
    btn(at, "ซ่อนโปรไฟล์ (ไม่ให้ใครเห็น)").click().run()
    assert query("SELECT is_public FROM ACTOR WHERE actor_id=%s", (aid,))[0]["is_public"] == 0
    assert not in_catalog("มาลี")
    at = as_actor(page("actor_profile.py"), aid)
    at.text_area(key=f"pf{aid}_bio").set_value("แนะนำตัวทดสอบ").run()
    btn(at, "บันทึกชื่อและแท็ก").click().run()
    no_exception(at)
    row = query("SELECT bio, is_public FROM ACTOR WHERE actor_id=%s", (aid,))[0]
    assert row["bio"] == "แนะนำตัวทดสอบ" and row["is_public"] == 0     # บันทึกข้อมูลไม่ได้เผยแพร่ให้เอง
    btn(at, "เผยแพร่โปรไฟล์").click().run()
    assert in_catalog("มาลี")


@test("ข้อความจากผู้ใช้ในผลงานถูก escape (กัน HTML/JS แทรก) และลิงก์ที่ไม่ใช่ http(s) ไม่ถูกทำเป็นลิงก์")
def _():
    sys.path.insert(0, str(ROOT))
    import ui
    h = ui.work_html({"work_id": 1, "title": "<script>alert(1)</script>", "work_type": "Film", "role_played": "<b>x</b>",
                      "work_year": 2025, "description": "<img src=x onerror=alert(1)>", "link_url": "javascript:alert(1)"})
    assert "<script>" not in h and "<img" not in h and "<b>x" not in h and "javascript:" not in h and "<a " not in h
    ok = ui.work_html({"work_id": 2, "title": "ปกติ", "work_type": "Film", "role_played": None, "work_year": 2025,
                       "description": None, "link_url": 'https://example.com/a?x="1"'})
    assert 'href="https://example.com/a?x=&quot;1&quot;"' in ok and 'rel="noopener noreferrer"' in ok


print(f"\nผ่าน {len(PASSED)} / {len(PASSED) + len(FAILED)} ข้อ")
if FAILED:
    sys.exit(1)
