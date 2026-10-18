"""
config.py : ที่เดียวที่ต้องแก้ ถ้าการเชื่อมต่อ MySQL ของเครื่องคุณไม่ตรงค่าเริ่มต้น

ค่าเริ่มต้นตรงกับ XAMPP ที่เพิ่งติดตั้ง:
    host = 127.0.0.1, port = 3306, user = root, password = (ว่าง)

อยากเปลี่ยนโดยไม่แก้ไฟล์ ก็ตั้ง environment variable ชื่อ DB_HOST, DB_PORT,
DB_USER, DB_PASSWORD, DB_NAME ได้ (ไม่จำเป็นสำหรับการใช้งานปกติ)
"""
import os

def _secret():
    """อ่านค่าจาก .streamlit/secrets.toml หัวข้อ [mysql] (ใช้ตอนขึ้นเว็บจริงบน Streamlit Community Cloud)"""
    try:
        import streamlit as st
        return dict(st.secrets["mysql"])
    except Exception:
        return {}


_S = _secret()


def _get(key, env, default):
    """ลำดับความสำคัญ: environment variable > secrets.toml > ค่าเริ่มต้น (XAMPP)"""
    return os.getenv(env) or _S.get(key) or default


DB_CONFIG = {
    "host": _get("host", "DB_HOST", "127.0.0.1"),
    "port": int(_get("port", "DB_PORT", 3306)),
    "user": _get("user", "DB_USER", "root"),
    "password": _get("password", "DB_PASSWORD", ""),
    "database": _get("database", "DB_NAME", "casting_agency"),
    "charset": "utf8mb4",
}
# ฐานข้อมูลบนคลาวด์ส่วนใหญ่บังคับต่อแบบเข้ารหัส (TLS) ตั้ง ssl = true ใน secrets หรือ DB_SSL=1
if str(_get("ssl", "DB_SSL", "")).lower() in ("1", "true", "yes"):
    DB_CONFIG["ssl_disabled"] = False
# ผู้ให้บริการคลาวด์มักไม่ให้สร้าง/ลบ "ฐานข้อมูล" เอง (มีมาให้แล้ว 1 อัน) ตั้ง skip_create = true
# แล้ว setup_db.py จะลบ/สร้างเฉพาะตารางในฐานข้อมูลที่ให้มา
SKIP_CREATE_DB = str(_get("skip_create", "DB_SKIP_CREATE", "")).lower() in ("1", "true", "yes")

# ค่าสถานะต่างๆ รวมไว้ที่เดียว ต้องตรงกับ CHECK ใน sql/schema.sql
ROLE_STATUS_LABEL = {
    "Selected": "รอนักแสดงตอบรับ",
    "Confirmed": "ยืนยันแล้ว",
    "Rejected_by_Actor": "นักแสดงปฏิเสธ",
    "Cancelled_by_Organizer": "ผู้จัดงานยกเลิก",
}
PAYMENT_STATUS_LABEL = {
    "Pending": "รอจ่าย",
    "Paid": "จ่ายแล้ว",
    "Cancelled": "ยกเลิก",
}
EVENT_TYPE_LABEL = {
    "Shoot": "ถ่ายทำ",
    "Fitting": "ฟิตติ้ง",
    "Rehearsal": "ซ้อม",
}
GENDER_LABEL = {"Male": "ชาย", "Female": "หญิง", "Other": "อื่นๆ"}
ACTOR_STATUS_LABEL = {"Active": "พร้อมรับงาน", "Inactive": "พักงาน"}
SKILL_TYPE_LABEL = {
    "Modeling": "งานโมเดลลิ่ง", "Performance": "การแสดง", "Language": "ภาษา",
    "Physical": "ร่างกายและกีฬา", "Other": "ทักษะอื่นๆ",
}
SKILL_TYPES = list(SKILL_TYPE_LABEL)          # ลำดับที่แสดงในฟอร์ม (ต้องตรงกับ CHECK ใน schema.sql)
PROJECT_TYPE_LABEL = {
    "Series": "ซีรีส์", "Movie": "ภาพยนตร์", "Commercial": "โฆษณา",
    "Music_Video": "มิวสิกวิดีโอ", "Fashion_Show": "โชว์แฟชั่น", "Other": "อื่นๆ",
}
# ประเภทผลงานใน PORTFOLIO (ต้องตรงกับ CHECK ck_work_type ใน sql/schema.sql)
WORK_TYPE_LABEL = {
    "Film": "ภาพยนตร์", "Series": "ซีรีส์/ละคร", "Commercial": "โฆษณา", "Runway": "รันเวย์/แฟชั่นโชว์",
    "Photoshoot": "ถ่ายแบบ/แคมเปญ", "Music_Video": "มิวสิกวิดีโอ", "Stage": "เวที/ละครเวที",
    "Online": "ออนไลน์/คอนเทนต์", "Other": "อื่นๆ",
}
MAX_WORKS = 20          # ผลงานต่อคน (กันข้อมูลบวม)
PROJECT_STATUS_LABEL = {
    "Open": "เปิดรับ", "In_Progress": "กำลังดำเนินการ", "Completed": "เสร็จสิ้น", "Cancelled": "ยกเลิก",
}
PROJECT_TYPES = list(PROJECT_TYPE_LABEL)
PROJECT_STATUSES = list(PROJECT_STATUS_LABEL)

# บทที่ "กินเวลาในปฏิทิน" ของนักแสดง (ใช้ตรวจคิวชน)
# Rejected/Cancelled ถือว่าว่างแล้ว
BUSY_ROLE_STATUSES = ("Selected", "Confirmed")


# ---------------------------------------------------------------------
# คุณลักษณะภายนอกของนักแสดง (คอลัมน์เพิ่มในตาราง ACTOR) ค่า key ต้องตรงกับ CHECK ใน sql/schema.sql
# ---------------------------------------------------------------------
BODY_TYPE_LABEL = {"Slim": "เพรียว", "Athletic": "ฟิต/นักกีฬา", "Average": "สมส่วน",
                   "Curvy": "เว้าโค้ง", "Plus_Size": "พลัสไซซ์", "Muscular": "กล้ามเนื้อ"}
SKIN_TONE_LABEL = {"Fair": "ขาวอมชมพู", "Light": "ขาวเหลือง", "Medium": "ผิวสองสี",
                   "Tan": "ผิวแทน", "Deep": "ผิวเข้ม"}
HAIR_COLOR_LABEL = {"Black": "ดำ", "Dark_Brown": "น้ำตาลเข้ม", "Brown": "น้ำตาล", "Light_Brown": "น้ำตาลอ่อน",
                    "Blonde": "บลอนด์/ทอง", "Red": "แดง/น้ำตาลแดง", "Gray": "เทา/เงิน/ขาว", "Dyed": "ทำสีแฟชั่น"}
HAIR_LENGTH_LABEL = {"Shaved": "โกน/เกรียน", "Short": "สั้น", "Medium": "ประบ่า", "Long": "ยาว"}
HAIR_TEXTURE_LABEL = {"Straight": "ตรง", "Wavy": "ลอน", "Curly": "หยิก"}
EYE_COLOR_LABEL = {"Black": "ดำ", "Dark_Brown": "น้ำตาลเข้ม", "Brown": "น้ำตาล", "Hazel": "เฮเซล",
                   "Green": "เขียว", "Blue": "ฟ้า", "Gray": "เทา"}
CLOTHING_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
EXPERIENCE_LABEL = {"Beginner": "มือใหม่", "Intermediate": "มีประสบการณ์", "Professional": "มืออาชีพ"}
PROVINCES = [
    "กรุงเทพมหานคร", "กระบี่", "กาญจนบุรี", "กาฬสินธุ์", "กำแพงเพชร", "ขอนแก่น", "จันทบุรี", "ฉะเชิงเทรา",
    "ชลบุรี", "ชัยนาท", "ชัยภูมิ", "ชุมพร", "เชียงราย", "เชียงใหม่", "ตรัง", "ตราด", "ตาก", "นครนายก",
    "นครปฐม", "นครพนม", "นครราชสีมา", "นครศรีธรรมราช", "นครสวรรค์", "นนทบุรี", "นราธิวาส", "น่าน",
    "บึงกาฬ", "บุรีรัมย์", "ปทุมธานี", "ประจวบคีรีขันธ์", "ปราจีนบุรี", "ปัตตานี", "พระนครศรีอยุธยา", "พะเยา",
    "พังงา", "พัทลุง", "พิจิตร", "พิษณุโลก", "เพชรบุรี", "เพชรบูรณ์", "แพร่", "ภูเก็ต", "มหาสารคาม",
    "มุกดาหาร", "แม่ฮ่องสอน", "ยโสธร", "ยะลา", "ร้อยเอ็ด", "ระนอง", "ระยอง", "ราชบุรี", "ลพบุรี", "ลำปาง",
    "ลำพูน", "เลย", "ศรีสะเกษ", "สกลนคร", "สงขลา", "สตูล", "สมุทรปราการ", "สมุทรสงคราม", "สมุทรสาคร",
    "สระแก้ว", "สระบุรี", "สิงห์บุรี", "สุโขทัย", "สุพรรณบุรี", "สุราษฎร์ธานี", "สุรินทร์", "หนองคาย",
    "หนองบัวลำภู", "อ่างทอง", "อำนาจเจริญ", "อุดรธานี", "อุตรดิตถ์", "อุทัยธานี", "อุบลราชธานี",
]
