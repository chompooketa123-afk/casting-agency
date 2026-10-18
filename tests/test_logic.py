"""
tests/test_logic.py : ทดสอบกฎธุรกิจทั้งหมดกับฐานข้อมูลจริง (ไม่ต้องเปิดเว็บ)

วิธีรัน (ที่โฟลเดอร์ casting-app):
    python tests/test_logic.py

ข้อควรรู้: ไฟล์นี้จะรัน setup_db.py ก่อน = รีเซ็ตข้อมูลกลับเป็นข้อมูลตัวอย่างทุกครั้ง
แต่ละ test() ตรงกับกรณีที่อาจารย์น่าจะถามว่า "ระบบกันเรื่องนี้ยังไง"
"""
import subprocess
import threading
import sys

# ให้พิมพ์ภาษาไทยในหน้าต่าง Terminal ของ Windows ได้ไม่เพี้ยน
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from datetime import date, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import queries as q                      # noqa: E402
from db import query                     # noqa: E402

PASSED, FAILED = [], []


def test(name):
    def deco(fn):
        try:
            fn()
            PASSED.append(name)
            print(f"  ผ่าน  {name}")
        except Exception as e:           # noqa: BLE001
            FAILED.append(name)
            print(f"  ไม่ผ่าน  {name}\n        -> {type(e).__name__}: {e}")
        return fn
    return deco


def expect_error(fn, contains):
    try:
        fn()
    except q.BusinessError as e:
        assert contains in str(e), f"ข้อความ error ไม่ตรง: {e}"
        return
    raise AssertionError(f"ควรเกิด BusinessError ('{contains}') แต่ไม่เกิด")


def d(days):
    return date.today() + timedelta(days=days)


def slot(days, start, end, kind="Shoot"):
    return {"event_type": kind, "event_date": d(days), "start_time": time(*start), "end_time": time(*end)}


def names(rows):
    return {r["full_name"] for r in rows}


# ---------------------------------------------------------------------
print("รีเซ็ตฐานข้อมูลเป็นข้อมูลตัวอย่าง ...")
subprocess.run([sys.executable, str(ROOT / "setup_db.py")], check=True, stdout=subprocess.DEVNULL)
print("เริ่มทดสอบ\n")

DRAMA, ENGLISH, DANCE = 6, 1, 5


@test("1) คิวชน: คนที่ติดงานช่วงเวลาเดียวกันต้องไม่อยู่ในรายชื่อ และบอกเหตุผลได้")
def _():
    slots = [slot(7, (15, 0), (17, 0))]               # สมหญิงติด 09-17, สมชายติด 14-16
    ok = q.find_matching_actors([DRAMA, ENGLISH], slots)
    assert {"ลลิตา วงศ์ทอง", "ธีรภัทร เก่งรอบด้าน"} <= names(ok), names(ok)
    assert not names(ok) & {"สมหญิง ใจดี", "สมชาย รักงาน", "พิมพ์ใจ พักงาน", "มาลี สุขสันต์"}
    ex = {r["full_name"]: r["reasons"] for r in
          q.explain_excluded([DRAMA, ENGLISH], slots, [r["actor_id"] for r in ok])}
    assert any("คิวชน" in t for t in ex["สมหญิง ใจดี"])
    assert any("คิวชน" in t for t in ex["สมชาย รักงาน"])
    assert any("Inactive" in t for t in ex["พิมพ์ใจ พักงาน"])


@test("2) ช่วงเวลาที่ 'ติดกันพอดี' (14:00 เลิก / 16:00 เริ่ม) ไม่นับว่าชน")
def _():
    ok = q.find_matching_actors([DRAMA, ENGLISH], [slot(7, (16, 0), (18, 0))])   # สมชายเลิก 16:00
    assert "สมชาย รักงาน" in names(ok)
    ok = q.find_matching_actors([DRAMA, ENGLISH], [slot(7, (12, 0), (14, 0))])
    assert "สมชาย รักงาน" in names(ok)


@test("3) ทักษะไม่ครบ: ต้องมีครบทุกข้อ และบอกว่าขาดอะไร")
def _():
    ok = q.find_matching_actors([DRAMA, ENGLISH], [slot(30, (9, 0), (10, 0))])
    assert "มาลี สุขสันต์" not in names(ok)           # มาลีมีดราม่า แต่ไม่มีภาษาอังกฤษ
    ex = {r["full_name"]: r["reasons"] for r in
          q.explain_excluded([DRAMA, ENGLISH], [slot(30, (9, 0), (10, 0))], [r["actor_id"] for r in ok])}
    assert any("ขาด ภาษาอังกฤษ" in t for t in ex["มาลี สุขสันต์"])


@test("4) บทที่ไม่ระบุทักษะ (ตัวประกอบ): ข้ามเงื่อนไขทักษะ แต่ยังเช็กคิวชน/Active")
def _():
    ok = q.find_matching_actors([], [slot(7, (9, 0), (17, 0))])
    assert "สมหญิง ใจดี" not in names(ok) and "พิมพ์ใจ พักงาน" not in names(ok)
    assert "ศุภกร หน้าใหม่" in names(ok)


@test("5) บทที่ถูกปฏิเสธ/ยกเลิก ไม่กินเวลาในปฏิทิน (นักแสดงกลับมาว่าง)")
def _():
    # กานต์(5) ปฏิเสธบทนักร้องนำ วันที่ +12 ตอน 09-18  / ปวีณา(6) ถูกยกเลิกบทนักเต้น +11 ตอน 10-13
    ok = q.find_matching_actors([], [slot(12, (9, 0), (18, 0))])
    assert "กานต์ มีสุข" in names(ok)
    ok = q.find_matching_actors([], [slot(11, (10, 0), (13, 0))])
    assert "ปวีณา ศรีงาม" in names(ok)


@test("6) ยอดรวมงวดไม่เท่าค่าตัว / ไม่มีงวด / เวลาเลิกก่อนเริ่ม ต้องถูกปฏิเสธ")
def _():
    base = dict(project_id=2, role_name="ทดสอบ", agreed_fee=1000, actor_id=13,
                skill_ids=[], slots=[slot(40, (9, 0), (10, 0))])
    expect_error(lambda: q.create_role(**base, installments=[{"due_date": d(50), "amount": 400}]),
                 "ไม่เท่ากับค่าตัว")
    expect_error(lambda: q.create_role(**base, installments=[]), "อย่างน้อย 1 งวด")
    bad = dict(base, slots=[slot(40, (10, 0), (9, 0))])
    expect_error(lambda: q.create_role(**bad, installments=[{"due_date": d(50), "amount": 1000}]),
                 "เวลาเลิกต้องหลังเวลาเริ่ม")


@test("7) เลือกนักแสดงที่คิวชนโดยตรง -> ถูกปฏิเสธซ้ำใน transaction (ไม่ไว้ใจรายชื่อเก่า)")
def _():
    expect_error(lambda: q.create_role(
        project_id=2, role_name="ชนแน่", agreed_fee=1000, actor_id=2, skill_ids=[],
        slots=[slot(7, (15, 0), (17, 0))], installments=[{"due_date": d(50), "amount": 1000}]),
        "คิวชน")


@test("8) สร้างบทสำเร็จ: เขียน 4 ตารางครบ และคนนั้นไม่ว่างในช่วงนั้นอีก")
def _():
    rid = q.create_role(
        project_id=2, role_name="ผู้ช่วยเชฟ", agreed_fee=3000, actor_id=8, skill_ids=[ENGLISH],
        slots=[slot(7, (15, 0), (17, 0)), slot(9, (9, 0), (12, 0), "Fitting")],
        installments=[{"due_date": d(20), "amount": 1000}, {"due_date": d(40), "amount": 2000}])
    assert query("SELECT role_status FROM `ROLE` WHERE role_id=%s", (rid,))[0]["role_status"] == "Selected"
    assert query("SELECT COUNT(*) n FROM ROLE_SKILL WHERE role_id=%s", (rid,))[0]["n"] == 1
    assert query("SELECT COUNT(*) n FROM SCHEDULE WHERE role_id=%s", (rid,))[0]["n"] == 2
    assert query("SELECT COUNT(*) n FROM PAYMENT_INSTALLMENT WHERE role_id=%s", (rid,))[0]["n"] == 2
    ok = q.find_matching_actors([ENGLISH], [slot(7, (16, 0), (18, 0))])
    assert "ลลิตา วงศ์ทอง" not in names(ok)
    # ลลิตายังไม่ได้ตอบรับ (Selected) ก็กินเวลาในปฏิทินแล้ว


@test("9) Transaction rollback: ถ้าเขียนพังกลางทาง ต้องไม่เหลือข้อมูลครึ่งๆ กลางๆ")
def _():
    before = query("SELECT COUNT(*) n FROM `ROLE`")[0]["n"]
    try:
        q.create_role(project_id=2, role_name="พังกลางทาง", agreed_fee=1000, actor_id=13, skill_ids=[],
                      slots=[slot(60, (9, 0), (10, 0))],
                      installments=[{"due_date": None, "amount": 1000}])   # due_date NOT NULL -> พังตอน INSERT งวด
    except Exception:                                                      # noqa: BLE001
        pass
    after = query("SELECT COUNT(*) n FROM `ROLE`")[0]["n"]
    assert before == after, "ROLE ถูกเขียนค้างไว้ ทั้งที่ transaction พัง"
    assert query("SELECT COUNT(*) n FROM SCHEDULE s LEFT JOIN `ROLE` r ON r.role_id=s.role_id "
                 "WHERE r.role_id IS NULL")[0]["n"] == 0


@test("10) นักแสดงตอบรับ/ปฏิเสธ: ตอบได้ครั้งเดียว, ตอบแทนคนอื่นไม่ได้, ปฏิเสธแล้วงวดถูกยกเลิก")
def _():
    expect_error(lambda: q.respond_to_role(3, actor_id=99, accept=True), "ตอบรับไปแล้ว")   # ไม่ใช่บทของ 99
    q.respond_to_role(3, actor_id=3, accept=True)
    assert query("SELECT role_status s FROM `ROLE` WHERE role_id=3")[0]["s"] == "Confirmed"
    expect_error(lambda: q.respond_to_role(3, actor_id=3, accept=False), "ตอบรับไปแล้ว")
    # ปฏิเสธ: ใช้บทที่เพิ่งสร้างของลลิตา
    rid = query("SELECT role_id FROM `ROLE` WHERE role_name='ผู้ช่วยเชฟ'")[0]["role_id"]
    q.respond_to_role(rid, actor_id=8, accept=False)
    st = {r["payment_status"] for r in query(
        "SELECT payment_status FROM PAYMENT_INSTALLMENT WHERE role_id=%s", (rid,))}
    assert st == {"Cancelled"}, st
    ok = q.find_matching_actors([ENGLISH], [slot(7, (16, 0), (18, 0))])
    assert "ลลิตา วงศ์ทอง" in names(ok)              # ปฏิเสธแล้ว กลับมาว่าง


@test("11) จ่ายเงิน: จ่ายครั้งแรกได้, กดซ้ำถูกปฏิเสธ, บทที่ยังไม่ Confirmed จ่ายไม่ได้")
def _():
    pid = query("SELECT payment_id FROM PAYMENT_INSTALLMENT WHERE role_id=2 AND payment_status='Pending' "
                "ORDER BY due_date LIMIT 1")[0]["payment_id"]
    q.mark_paid(pid)
    expect_error(lambda: q.mark_paid(pid), "จ่ายซ้ำไม่ได้")
    # บท 5 ถูกปฏิเสธ -> งวดเป็น Cancelled
    pid5 = query("SELECT payment_id FROM PAYMENT_INSTALLMENT WHERE role_id=5")[0]["payment_id"]
    expect_error(lambda: q.mark_paid(pid5), "ยกเลิกแล้ว")
    # บทใหม่ที่ยัง Selected -> จ่ายไม่ได้
    rid = q.create_role(project_id=3, role_name="รอตอบ", agreed_fee=500, actor_id=15, skill_ids=[],
                        slots=[], installments=[{"due_date": d(5), "amount": 500}])
    pid_sel = query("SELECT payment_id FROM PAYMENT_INSTALLMENT WHERE role_id=%s", (rid,))[0]["payment_id"]
    expect_error(lambda: q.mark_paid(pid_sel), "Confirmed")


@test("12) ยกเลิกหลังยืนยัน: งวด Pending ถูกยกเลิก งวด Paid คงไว้ และคนนั้นกลับมาว่าง")
def _():
    paid_before = query("SELECT COUNT(*) n FROM PAYMENT_INSTALLMENT WHERE role_id=1 AND payment_status='Paid'")[0]["n"]
    q.cancel_role(1)
    assert query("SELECT role_status s FROM `ROLE` WHERE role_id=1")[0]["s"] == "Cancelled_by_Organizer"
    rows = query("SELECT payment_status s FROM PAYMENT_INSTALLMENT WHERE role_id=1")
    assert sum(r["s"] == "Paid" for r in rows) == paid_before and not any(r["s"] == "Pending" for r in rows)
    expect_error(lambda: q.cancel_role(1), "ยกเลิกไปแล้ว")
    ok = q.find_matching_actors([], [slot(7, (9, 0), (17, 0))])
    assert "สมหญิง ใจดี" in names(ok)


@test("13) Race condition: สองคนเลือกนักแสดงคนเดียวกันพร้อมกัน -> สำเร็จได้แค่คนเดียว")
def _():
    results, barrier = [], threading.Barrier(2)

    def worker(n):
        barrier.wait()
        try:
            q.create_role(project_id=2, role_name=f"แย่งกัน{n}", agreed_fee=1000, actor_id=13, skill_ids=[],
                          slots=[slot(45, (10, 0), (12, 0))],
                          installments=[{"due_date": d(60), "amount": 1000}])
            results.append("ok")
        except q.BusinessError:
            results.append("conflict")

    ts = [threading.Thread(target=worker, args=(i,)) for i in (1, 2)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sorted(results) == ["conflict", "ok"], results


@test("14) ค้นหานักแสดงหลายเงื่อนไขพร้อมกัน (เพศ + ทักษะ + ว่างในช่วงเวลา + คำในรูปลักษณ์)")
def _():
    rows = q.search_actors(gender="Female", skill_ids=[DANCE])
    assert {"ปวีณา ศรีงาม", "นภา ฟ้าใส", "ชนิดา ดาวเด่น"} <= names(rows), names(rows)
    assert all(r["gender"] == "Female" for r in rows)
    rows = q.search_actors(gender="Male", text="กล้าม")
    assert "ภาณุ แข็งแรง" in names(rows), names(rows)
    assert all(r["gender"] == "Male" for r in rows)
    busy = {"event_date": d(21), "start_time": time(9, 0), "end_time": time(10, 0)}   # ชนกับ: สมชาย ไม่ได้ (ติด 14-16) -> ว่าง
    rows = q.search_actors(skill_ids=[DRAMA], avail={"event_date": d(7), "start_time": time(14, 30), "end_time": time(15, 30)})
    assert "สมชาย รักงาน" not in names(rows)
    del busy


@test("15) สมัครนักแสดง / แก้โปรไฟล์ / สร้างโปรเจกต์ บันทึกลง DB จริง (อ่านกลับมาเห็น)")
def _():
    aid = q.register_actor("ทดสอบ ระบบ", "Female", "สูง 160", [DRAMA, ENGLISH])
    assert q.get_actor(aid)["actor_status"] == "Active"
    assert sorted(q.get_actor_skill_ids(aid)) == sorted([DRAMA, ENGLISH])
    q.update_actor(aid, "ทดสอบ แก้ชื่อ", "Female", "Inactive", "สูง 161", [DANCE])
    a = q.get_actor(aid)
    assert a["full_name"] == "ทดสอบ แก้ชื่อ" and a["actor_status"] == "Inactive"
    assert q.get_actor_skill_ids(aid) == [DANCE]
    expect_error(lambda: q.register_actor("  ", "Male", "", []), "ชื่อ")
    pid = q.create_project("โปรเจกต์ทดสอบ", "Movie", "ลูกค้าทดสอบ")
    q.update_project_status(pid, "Cancelled")
    p = [x for x in q.list_projects() if x["project_id"] == pid][0]
    assert p["project_status"] == "Cancelled" and p["role_count"] == 0
    expect_error(lambda: q.create_role(pid, "บท", 100, 13, [], [], [{"due_date": d(5), "amount": 100}]),
                 "ปิดแล้ว")


@test("16) Dashboard query ทำงานได้และตัวเลขสมเหตุสมผล")
def _():
    n = q.dashboard_numbers()
    assert n["overdue"]["n"] >= 0 and len(n["skill_popularity"]) == q.query("SELECT COUNT(*) AS c FROM SKILL")[0]["c"]
    assert {r["status"] for r in n["roles_by_status"]} <= {
        "Selected", "Confirmed", "Rejected_by_Actor", "Cancelled_by_Organizer"}


@test("17) แปลงข้อมูลจากตารางที่ผู้ใช้แก้ในหน้าเว็บ (data_editor) ได้ทุกรูปแบบค่าที่ Streamlit อาจส่งกลับมา")
def _():
    import pandas as pd
    import ui
    from datetime import datetime
    df = pd.DataFrame([
        {"ประเภท": "ถ่ายทำ", "วันที่": d(7), "เริ่ม": time(9, 0), "เลิก": time(17, 0)},                       # date + time ปกติ
        {"ประเภท": "ซ้อม", "วันที่": pd.Timestamp(d(8)), "เริ่ม": "10:30", "เลิก": pd.Timestamp("2026-01-01 12:00")},  # Timestamp / ข้อความ
        {"ประเภท": None, "วันที่": None, "เริ่ม": None, "เลิก": None},                                         # แถวว่าง -> ข้าม
    ])
    slots = ui.parse_slots(df)
    assert len(slots) == 2 and slots[1]["event_type"] == "Rehearsal"
    assert slots[1]["start_time"] == time(10, 30) and slots[1]["end_time"] == time(12, 0)
    assert slots[1]["event_date"] == d(8)
    bad = pd.DataFrame([{"ประเภท": "ถ่ายทำ", "วันที่": d(7), "เริ่ม": time(9, 0), "เลิก": None}])
    expect_error(lambda: ui.parse_slots(bad), "กรอกไม่ครบ")
    pay = pd.DataFrame([{"ครบกำหนดจ่าย": d(10), "จำนวนเงิน": 100.5}, {"ครบกำหนดจ่าย": None, "จำนวนเงิน": None}])
    items = ui.parse_installments(pay)
    assert len(items) == 1 and items[0]["amount"] == 100.5 and items[0]["due_date"] == d(10)


@test("18) ตัวกรองรูปลักษณ์: ส่วนสูง/อายุ/สีผม/รอยสัก กรองใน SQL และทุกคนที่ถูกตัดออกมีเหตุผล")
def _():
    rows = q.search_actors(traits={"height_min": 175, "hair_colors": ["Black"], "tattoo": True})
    assert rows and all(r["height_cm"] >= 175 and r["hair_color"] == "Black" and r["has_tattoo"] for r in rows)
    assert "อนันต์ ไม่กลัว" in names(rows)
    rows = q.search_actors(traits={"age_min": 45})
    assert rows and all(r["age"] >= 45 for r in rows)
    # จับคู่ + traits: ทุกคนที่ไม่ผ่านต้องมีเหตุผลอย่างน้อย 1 ข้อ
    slots = [slot(40, (9, 0), (10, 0))]
    traits = {"height_min": 178, "body_types": ["Slim", "Athletic"]}
    ok = q.find_matching_actors([], slots, None, traits)
    assert ok and all(r["height_cm"] >= 178 and r["body_type"] in ("Slim", "Athletic") for r in ok)
    ex = q.explain_excluded([], slots, [r["actor_id"] for r in ok], None, traits)
    assert len(ex) + len(ok) == len(q.list_actors(public_only=True))
    assert all(r["reasons"] for r in ex)
    assert any("ส่วนสูง" in t for r in ex for t in r["reasons"])


@test("19) สมัครพร้อมรูปลักษณ์: บันทึกครบ, อายุ < 18 / ค่าเกินช่วง / enum ผิด ถูกปฏิเสธ")
def _():
    from datetime import date
    prof = {"birth_date": date(date.today().year - 25, 1, 1), "height_cm": 170, "weight_kg": 55.5,
            "hair_color": "Red", "hair_length": "Long", "has_tattoo": True, "province": "เชียงใหม่",
            "experience_level": "Intermediate"}
    aid = q.register_actor("ทดสอบ รูปลักษณ์", "Female", "ทดสอบ", [q.list_skills()[0]["skill_id"]], prof)
    a = q.get_actor(aid)
    assert a["height_cm"] == 170 and a["hair_color"] == "Red" and a["has_tattoo"] and a["age"] == 25
    assert q.get_actor_skills(aid)
    expect_error(lambda: q.register_actor("เด็ก", "Male", "", [], {"birth_date": date(date.today().year - 10, 1, 1)}), "18 ปี")
    expect_error(lambda: q.register_actor("สูงเกิน", "Male", "", [], {"height_cm": 400}), "ส่วนสูง")
    expect_error(lambda: q.register_actor("ผิด", "Male", "", [], {"hair_color": "Purple"}), "ไม่ถูกต้อง")
    # แก้โปรไฟล์โดยไม่ส่ง profile -> ค่าเดิมต้องไม่หาย
    q.update_actor(aid, "ทดสอบ รูปลักษณ์", "Female", "Active", "แก้แล้ว", [])
    assert q.get_actor(aid)["hair_color"] == "Red"


@test("20) หน้าแรก: featured_actors / talent_counts ใช้ได้")
def _():
    f = q.featured_actors(5)
    assert len(f) == 5 and all(r["actor_status"] == "Active" for r in f)
    assert f[0]["n_skills"] >= f[-1]["n_skills"]
    c = q.talent_counts()
    assert c["skills"] == 89 and c["actors"] == 35      # 36 คน - พักงาน 1 คน (ผู้สมัครใหม่ที่ซ่อนอยู่ไม่นับ)


HIDDEN = (37, 38)        # ผู้สมัครใหม่ที่ยังไม่ได้ใส่อะไร (seed ตั้ง is_public = 0)


@test("21) ไม่ได้ใส่อะไร = คนอื่นไม่เห็น: คนที่ซ่อนอยู่ไม่โผล่ในค้นหา/จับคู่/หน้าแรก/รายชื่อที่ถูกตัดออก")
def _():
    def ids(rows):
        return {r["actor_id"] for r in rows}
    assert not ids(q.search_actors()) & set(HIDDEN)
    assert not ids(q.search_actors(text="นภัส")) and not ids(q.search_actors(text="ธีรพล"))
    assert not ids(q.featured_actors(100)) & set(HIDDEN)
    ok = q.find_matching_actors([], [slot(50, (9, 0), (10, 0))])
    assert not ids(ok) & set(HIDDEN)
    ex = q.explain_excluded([], [slot(50, (9, 0), (10, 0))], ids(ok))
    assert not ids(ex) & set(HIDDEN)                              # ผู้จัดงานต้องไม่รู้ว่ามีใครซ่อนอยู่
    assert set(HIDDEN) <= ids(q.list_actors())                    # แต่ dropdown 'ฉันคือใคร' ต้องเห็น (ไม่งั้นแก้โปรไฟล์ตัวเองไม่ได้)
    assert not set(HIDDEN) & ids(q.list_actors(public_only=True))
    assert q.talent_counts()["actors"] == 35
    # เลือกคนที่ซ่อนอยู่เข้าบทโดยตรง (ข้ามหน้าเว็บ) ก็ต้องถูกปฏิเสธ
    pid = q.query("SELECT project_id FROM PROJECT LIMIT 1")[0]["project_id"]
    expect_error(lambda: q.create_role(pid, "ทดสอบ", 1000, HIDDEN[0], [], [slot(51, (9, 0), (10, 0))],
                                       [{"amount": 1000, "due_date": d(60)}]), "ปิดโปรไฟล์")


@test("22) เผยแพร่/ซ่อนโปรไฟล์: ไม่มีทักษะและผลงานเลย = เผยแพร่ไม่ได้, พอใส่แล้วเผยแพร่ได้และคนอื่นเห็นทันที")
def _():
    a = HIDDEN[1]
    r = q.profile_readiness(a)
    assert not r["ready"] and r["n_skills"] == 0 and r["n_works"] == 0 and not r["is_public"]
    expect_error(lambda: q.set_profile_public(a, True), "ยังเผยแพร่ไม่ได้")
    q.update_actor(a, "ธีรพล เพิ่งสมัคร", "Male", "Active", None, [1])       # ใส่แท็ก 1 อย่าง
    assert q.profile_readiness(a)["ready"] and not q.get_actor(a)["is_public"]    # พร้อมแล้ว แต่ยังไม่กดเผยแพร่ = ยังซ่อน
    assert a not in {r["actor_id"] for r in q.search_actors()}
    q.set_profile_public(a, True)
    assert a in {r["actor_id"] for r in q.search_actors(skill_ids=[1])}
    q.set_profile_public(a, False)
    assert a not in {r["actor_id"] for r in q.search_actors(skill_ids=[1])}
    # ใส่แค่ผลงาน (ไม่มีทักษะ) ก็เผยแพร่ได้
    b = HIDDEN[0]
    q.add_work(b, "ผลงานแรก", "Film", "นำหญิง", date.today().year)
    q.set_profile_public(b, True)
    assert b in {r["actor_id"] for r in q.search_actors(text="นภัส")}


@test("23) สมัครใหม่: ไม่มีทักษะ/ไม่ติ๊กเผยแพร่ = ซ่อน, มีทักษะและติ๊กเผยแพร่ = เห็น; แก้โปรไฟล์ไม่แตะคำแนะนำตัว")
def _():
    s1 = q.list_skills()[0]["skill_id"]
    a = q.register_actor("ไม่มีแท็ก", "Female", "", [], bio="สวัสดี")
    assert not q.get_actor(a)["is_public"]
    b = q.register_actor("มีแท็กแต่ไม่เผยแพร่", "Female", "", [s1], publish=False)
    assert not q.get_actor(b)["is_public"]
    c = q.register_actor("มีแท็กและเผยแพร่", "Female", "", [s1], bio="ถนัดเดินแบบ")
    assert q.get_actor(c)["is_public"] and q.get_actor(c)["bio"] == "ถนัดเดินแบบ"
    q.update_actor(c, "มีแท็กและเผยแพร่", "Female", "Active", "", [s1])           # ไม่ส่ง bio = ไม่แตะ
    assert q.get_actor(c)["bio"] == "ถนัดเดินแบบ"
    q.update_actor(c, "มีแท็กและเผยแพร่", "Female", "Active", "", [s1], bio="")    # ส่งว่าง = ล้าง
    assert q.get_actor(c)["bio"] is None
    expect_error(lambda: q.register_actor("ยาว", "Male", "", [], bio="ก" * 501), "500")


@test("24) ผลงาน: เพิ่ม/แก้/ลบ ได้เฉพาะของตัวเอง, ตรวจปี-ลิงก์-ความยาว, จำกัดจำนวน, ลบจนหมดแล้วโปรไฟล์ปิดเอง")
def _():
    from config import MAX_WORKS
    s1 = q.list_skills()[0]["skill_id"]
    a = q.register_actor("ทดสอบผลงาน", "Male", "", [s1])
    other = 1
    y = date.today().year
    w1 = q.add_work(a, "ผลงานเก่า", "Film", "นำชาย", y - 3, "รายละเอียด", "https://example.com/x")
    w2 = q.add_work(a, "ผลงานใหม่", "Runway", None, y)
    ws = q.list_works(a)
    assert [w["title"] for w in ws] == ["ผลงานใหม่", "ผลงานเก่า"] and ws[1]["link_url"] == "https://example.com/x"
    assert q.get_actor(a)["n_works"] == 2
    expect_error(lambda: q.add_work(a, "", "Film", None, y), "ชื่อผลงาน")
    expect_error(lambda: q.add_work(a, "x", "Hologram", None, y), "ประเภท")
    expect_error(lambda: q.add_work(a, "x", "Film", None, 1900), "ปี")
    expect_error(lambda: q.add_work(a, "x", "Film", None, y + 5), "ปี")
    expect_error(lambda: q.add_work(a, "x", "Film", None, "abc"), "ตัวเลข")
    expect_error(lambda: q.add_work(a, "x", "Film", None, y, None, "javascript:alert(1)"), "ลิงก์")
    expect_error(lambda: q.add_work(a, "x" * 151, "Film", None, y), "150")
    # แก้/ลบผลงานของคนอื่นไม่ได้
    expect_error(lambda: q.update_work(other, w1, "แอบแก้", "Film", None, y), "ไม่พบผลงาน")
    expect_error(lambda: q.delete_work(other, w1), "ไม่พบผลงาน")
    q.update_work(a, w1, "ผลงานเก่า (แก้)", "Series", "ตัวร้าย", y - 2)
    assert {w["title"] for w in q.list_works(a)} == {"ผลงานใหม่", "ผลงานเก่า (แก้)"}
    q.update_work(a, w1, "ผลงานเก่า (แก้)", "Series", "ตัวร้าย", y - 2)               # ค่าเดิมเป๊ะ ต้องไม่ error
    # ลบทักษะหมด แต่ยังมีผลงาน -> ยังเผยแพร่อยู่ ; ลบผลงานหมดด้วย -> ปิดเอง
    assert q.update_actor(a, "ทดสอบผลงาน", "Male", "Active", "", []) is True
    assert q.delete_work(a, w1) is True
    assert q.delete_work(a, w2) is False and not q.get_actor(a)["is_public"]
    # จำกัดจำนวน
    for i in range(MAX_WORKS):
        q.add_work(a, f"งาน {i}", "Other", None, y)
    expect_error(lambda: q.add_work(a, "เกิน", "Other", None, y), str(MAX_WORKS))
    # ลบนักแสดงแล้วผลงานหายตาม (ON DELETE CASCADE)
    from db import execute
    execute("DELETE FROM ACTOR WHERE actor_id=%s", (a,))
    assert q.query("SELECT COUNT(*) n FROM PORTFOLIO WHERE actor_id=%s", (a,))[0]["n"] == 0


# ---------------------------------------------------------------------
print(f"\nผ่าน {len(PASSED)} / {len(PASSED) + len(FAILED)} ข้อ")
if FAILED:
    sys.exit(1)
