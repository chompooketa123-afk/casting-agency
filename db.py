"""
db.py : ชั้นเชื่อมต่อฐานข้อมูล (ทุกหน้าเว็บคุยกับ MySQL ผ่านไฟล์นี้เท่านั้น)

มี 3 อย่างหลัก
  1) query()        อ่านข้อมูล (SELECT)  -> คืน list ของ dict
  2) execute()      เขียนข้อมูลคำสั่งเดียว (INSERT/UPDATE/DELETE) -> คืน (จำนวนแถวที่ถูกแก้, id ล่าสุด)
  3) transaction()  เขียนหลายคำสั่งเป็นชุดเดียว สำเร็จทั้งหมดหรือยกเลิกทั้งหมด

ทุกคำสั่ง SQL จะถูกจดไว้ใน SQL log เพื่อโชว์ที่แถบด้านข้าง (ปุ่ม "ดู SQL")
"""
from contextlib import contextmanager

import mysql.connector
from mysql.connector import pooling
import streamlit as st

from config import DB_CONFIG


# ---------------------------------------------------------------------
# connection pool : เปิด connection ไว้ 5 เส้นแล้วหยิบมาใช้ซ้ำ
# (ไม่ต้องเปิด-ปิดใหม่ทุกครั้งที่กดปุ่ม) @st.cache_resource = สร้างครั้งเดียวทั้งแอป
# ---------------------------------------------------------------------
@st.cache_resource
def _get_pool():
    # autocommit=True : คำสั่งเดี่ยวๆ (INSERT/UPDATE) บันทึกลง DB ทันที
    # ต้องตั้งตรงนี้ตอนเปิด connection (เคยลองตั้ง conn.autocommit = True ทีหลังกับ connection
    # จาก pool แล้วไม่มีผลจริงที่ฝั่ง server ข้อมูลเลยไม่ถูกบันทึก -- เทสจับได้)
    return pooling.MySQLConnectionPool(
        pool_name="casting_pool", pool_size=5, autocommit=True, **DB_CONFIG
    )


def _get_conn():
    return _get_pool().get_connection()


# ---------------------------------------------------------------------
# SQL log : เก็บคำสั่งล่าสุดไว้โชว์ (เก็บใน session ของผู้ใช้แต่ละคน)
# ---------------------------------------------------------------------
def _short(v):
    """ค่าที่ยาวมาก (เช่นรูปแบบ base64) ย่อก่อนจดลง log ไม่ให้ log บวมและไม่ส่งรูปเต็มกลับไปโชว์ในหน้า 'SQL ที่เพิ่งรัน'"""
    if isinstance(v, str) and len(v) > 120:
        return v[:30] + f"… (ยาว {len(v):,} ตัวอักษร)"
    return v


def _log(sql, params):
    try:
        log = st.session_state.setdefault("sql_log", [])
        if isinstance(params, (list, tuple)):
            params = tuple(_short(x) for x in params)
        log.append((" ".join(sql.split()), params))
        del log[:-40]           # เก็บแค่ 40 คำสั่งล่าสุด
    except Exception:
        pass                    # ถ้าเรียกนอก Streamlit (ตอนเทส) ก็ข้ามไป


def get_sql_log():
    try:
        return list(st.session_state.get("sql_log", []))
    except Exception:
        return []


def clear_sql_log():
    try:
        st.session_state["sql_log"] = []
    except Exception:
        pass


# ---------------------------------------------------------------------
# 1) อ่านข้อมูล
# ---------------------------------------------------------------------
def query(sql, params=None, log=True):
    """รัน SELECT แล้วคืนผลเป็น list ของ dict เช่น [{'actor_id': 1, 'full_name': '...'}, ...]"""
    if log:
        _log(sql, params)
    conn = _get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()            # คืน connection กลับเข้า pool


# ---------------------------------------------------------------------
# 2) เขียนข้อมูลคำสั่งเดียว
# ---------------------------------------------------------------------
def execute(sql, params=None):
    """รัน INSERT/UPDATE/DELETE คืน (rowcount, lastrowid)
    rowcount = จำนวนแถวที่ถูกแก้จริง ใช้เช็กว่าคำสั่ง "ได้ผลไหม" เช่นกันจ่ายซ้ำ"""
    _log(sql, params)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()           # ย้ำอีกชั้น: ให้แน่ใจว่าบันทึกแล้วจริง
        result = (cur.rowcount, cur.lastrowid)
        cur.close()
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------
# 3) transaction : หลายคำสั่งเป็นชุดเดียว
# ---------------------------------------------------------------------
class _Tx:
    """ตัวช่วยที่ใช้ภายใน with transaction() as tx: ... """

    def __init__(self, conn):
        self._conn = conn
        self._cur = conn.cursor(dictionary=True)

    def query(self, sql, params=None):
        _log(sql, params)
        self._cur.execute(sql, params or ())
        return self._cur.fetchall()

    def execute(self, sql, params=None):
        _log(sql, params)
        self._cur.execute(sql, params or ())
        return self._cur.rowcount, self._cur.lastrowid


@contextmanager
def transaction():
    """ใช้แบบ
        with transaction() as tx:
            tx.execute("INSERT ...")
            tx.execute("INSERT ...")
    ถ้าจบบล็อกปกติ -> COMMIT ถ้ามี error ตรงไหน -> ROLLBACK ทั้งชุด
    """
    conn = _get_conn()
    try:
        conn.start_transaction()
        tx = _Tx(conn)
        yield tx
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_schema():
    """อัปเกรดฐานข้อมูลที่สร้างไว้ก่อนหน้าให้มีส่วนรูปโปรไฟล์ (คอลัมน์ ACTOR.photo_ver + ตาราง ACTOR_PHOTO)
    รันซ้ำกี่ครั้งก็ได้ ไม่แตะข้อมูลเดิม ไม่ต้องรัน setup_db.py ใหม่ (setup_db.py จะลบข้อมูลทั้งหมด)
    คืน None ถ้าเรียบร้อย หรือข้อความ error ถ้าอัปเกรดไม่ได้"""
    try:
        cols = query("SELECT COLUMN_NAME AS c FROM information_schema.COLUMNS "
                     "WHERE TABLE_SCHEMA = DATABASE() AND LOWER(TABLE_NAME) = 'actor'", log=False)
        if "photo_ver" not in {r["c"].lower() for r in cols}:
            execute("ALTER TABLE ACTOR ADD COLUMN photo_ver BIGINT NOT NULL DEFAULT 0")
        execute("CREATE TABLE IF NOT EXISTS ACTOR_PHOTO ("
                "actor_id INT PRIMARY KEY, photo MEDIUMTEXT NOT NULL, "
                "updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                "CONSTRAINT fk_photo_actor FOREIGN KEY (actor_id) REFERENCES ACTOR(actor_id) ON DELETE CASCADE)")
        return None
    except mysql.connector.Error as e:
        return str(e)


def check_connection():
    """ใช้ตอนเปิดแอป: ต่อ DB ได้ไหม ถ้าไม่ได้คืนข้อความ error ภาษาคน"""
    try:
        query("SELECT 1 AS ok", log=False)
        return None
    except mysql.connector.Error as e:
        return str(e)
