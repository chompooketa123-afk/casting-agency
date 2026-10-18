"""
setup_db.py : สร้างฐานข้อมูลให้เองด้วยคำสั่งเดียว (ไม่ต้องใช้ phpMyAdmin)

    python setup_db.py          -> สร้างตาราง + ใส่ข้อมูลตัวอย่าง (ลบของเก่าทิ้ง!)
    python setup_db.py --empty  -> สร้างเฉพาะตาราง ไม่ใส่ข้อมูลตัวอย่าง

ไฟล์นี้อ่าน sql/schema.sql และ sql/seed.sql แล้วสั่งรันทีละคำสั่ง
(ผลเหมือนการ import ไฟล์ทั้งสองใน phpMyAdmin)
"""
import sys

# ให้พิมพ์ภาษาไทยในหน้าต่าง Terminal ของ Windows ได้ไม่เพี้ยน
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from pathlib import Path

import mysql.connector

from config import DB_CONFIG, SKIP_CREATE_DB

SQL_DIR = Path(__file__).parent / "sql"


def split_statements(script: str):
    """แยกสคริปต์ SQL เป็นทีละคำสั่ง (ตัดคอมเมนต์ -- และไม่หลงเครื่องหมาย ; ที่อยู่ในข้อความ)"""
    cleaned = "\n".join(
        line for line in script.splitlines() if not line.strip().startswith("--"))
    statements, buf, quote = [], [], None
    for ch in cleaned:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"', "`"):
            quote = ch
            buf.append(ch)
        elif ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_file(cursor, filename):
    script = (SQL_DIR / filename).read_text(encoding="utf-8")
    stmts = split_statements(script)
    if SKIP_CREATE_DB:      # โหมดคลาวด์: ไม่แตะตัวฐานข้อมูล ใช้อันที่ผู้ให้บริการสร้างไว้ให้
        stmts = [x for x in stmts if not x.upper().startswith(("DROP DATABASE", "CREATE DATABASE", "USE "))]
    for stmt in stmts:
        cursor.execute(stmt)
    print(f"  รัน {filename} สำเร็จ ({len(stmts)} คำสั่ง)")


def main():
    # โหมดปกติ (XAMPP): ยังไม่มี DB ให้ต่อโดยไม่ระบุชื่อ / โหมดคลาวด์: ต่อเข้า DB ที่ให้มาเลย
    cfg = dict(DB_CONFIG) if SKIP_CREATE_DB else {k: v for k, v in DB_CONFIG.items() if k != "database"}
    try:
        conn = mysql.connector.connect(**cfg)
    except mysql.connector.Error as e:
        print("\nต่อ MySQL ไม่ได้:", e)
        print("เช็กว่าเปิด MySQL ใน XAMPP Control Panel แล้ว (กด Start ที่แถว MySQL)")
        print("และ user/password ใน config.py ถูกต้อง")
        sys.exit(1)

    cur = conn.cursor()
    print("กำลังสร้างฐานข้อมูล casting_agency ...")
    if SKIP_CREATE_DB:      # ลบตารางเก่าของเราทิ้งก่อน (ลำดับไม่สำคัญเพราะปิดการเช็ก FK ชั่วคราว)
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for t in ("PAYMENT_INSTALLMENT", "SCHEDULE", "ROLE_SKILL", "`ROLE`", "PORTFOLIO", "ACTOR_SKILL", "SKILL", "ACTOR", "PROJECT"):
            cur.execute(f"DROP TABLE IF EXISTS {t}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    run_file(cur, "schema.sql")
    if "--empty" not in sys.argv:
        run_file(cur, "seed.sql")
    conn.commit()
    cur.close()
    conn.close()
    print("เสร็จแล้ว! ต่อไปรัน:  streamlit run app.py")


if __name__ == "__main__":
    main()
