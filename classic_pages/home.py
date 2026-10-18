"""
หน้าแรก : หน้า "ชวนให้ใช้งาน" -- ไม่ได้ลอกสไลด์ แต่โชว์ของจริงจากฐานข้อมูล

ส่วนต่างๆ ดึงข้อมูลสดจาก MySQL ทุกครั้งที่เปิดหน้า
  ภาพนักแสดงในหน้าปก + แถบเลื่อน   featured_actors   ACTOR + ACTOR_SKILL (เฉพาะคนที่เปิดโปรไฟล์)
  ตัวเลขสถิติ                      talent_counts      ACTOR / SKILL / PROJECT / ROLE
  ทักษะยอดนิยม                     dashboard_numbers  SKILL + ACTOR_SKILL
"""
import streamlit as st

import art
import queries as q
import ui

feat = q.featured_actors(10)
fem = [a for a in feat if a["gender"] == "Female"]
male = [a for a in feat if a["gender"] == "Male"]
trio = [x for x in (fem[:1] + male[:1] + fem[1:2]) if x] or feat[:3]
nums = q.talent_counts()

# ---------------------------------------------------------------------
# หน้าปก
# ---------------------------------------------------------------------
left, right = st.columns([1.12, .88], gap="large", vertical_alignment="center")
with left:
    st.html(f"""
<div class="hero2">
  <div class="eyebrow">{art.sparkle_svg(12)}CASTING &amp; MODELING AGENCY</div>
  <h1>Find the <em>face</em><br>for every story.</h1>
  <p class="th">ที่เดียวจบ ทั้งหานักแสดง นายแบบ นางแบบ ที่ <b>ตรงทั้งทักษะและรูปลักษณ์</b>
  ตรวจคิวงานไม่ให้ชน และจ่ายค่าตัวเป็นงวดอย่างโปร่งใส สำหรับคนอยากเข้าวงการและทีมที่กำลังหาคนมาเล่นบท</p>
</div>""")
    with st.container(key="cta"):
        c1, c2 = st.columns(2)
        c1.page_link("classic_pages/actor_register.py", label="ฉันเป็นนักแสดง / โมเดล  สมัครเลย", icon=":material/person_add:")
        c2.page_link("classic_pages/org_casting.py", label="ฉันเป็นผู้จัดงาน  หานักแสดง", icon=":material/person_search:")
with right:
    arches = "".join(f'<div class="arch a{i}">{art.avatar_svg(a, label=False)}</div>' for i, a in enumerate(trio, 1))
    st.html(f"""
<div class="arches">{arches}
  <div class="float-badge b1">{art.sparkle_svg(14)}{nums['skills']} ทักษะให้เลือก</div>
  <div class="float-badge b2">{art.sparkle_svg(14)}จับคู่อัตโนมัติ คิวไม่ชน</div>
</div>""")

st.html(f"""
<div class="strip">
  <div><b>{nums['actors']}</b><span>นักแสดงและโมเดลพร้อมรับงาน</span></div>
  <div><b>{nums['skills']}</b><span>ทักษะ ภาษา และสายงานโมเดลลิ่ง</span></div>
  <div><b>{nums['projects']}</b><span>โปรเจกต์ที่เปิดรับคัดเลือก</span></div>
  <div><b>{nums['roles']}</b><span>บทที่จับคู่นักแสดงแล้ว</span></div>
</div>
<p class="hint">ตัวเลขทั้งหมดนับสดจากฐานข้อมูล MySQL ทุกครั้งที่เปิดหน้านี้</p>""")

# ---------------------------------------------------------------------
# จุดเด่น
# ---------------------------------------------------------------------
ui.section("ทำไมต้องที่นี่", "สามอย่างที่ทำให้หาคนเร็วกว่าทักแชตทีละคน")
st.html(f"""
<div class="tiles">
  <div class="tile rose"><span class="num">01</span><h3>หาให้ตรงถึงรูปลักษณ์</h3>
    <p>กรองพร้อมกันได้ทั้งอายุ ส่วนสูง รูปร่าง สีผิว สีผม สีตา และทักษะอีก {nums['skills']} อย่าง ตั้งแต่เดินแบบรันเวย์ยันภาษามือไทย</p>
    <div class="ex">{ui.chips_soft(["ผมบลอนด์", "สูง 175+", "เดินแบบ", "ภาษาอังกฤษ"])}</div></div>
  <div class="tile powder"><span class="num">02</span><h3>คิวไม่ชน ไม่ต้องโทรเช็ก</h3>
    <p>ทุกครั้งที่เลือกนักแสดง ระบบตรวจตารางนัดให้เอง คนที่ติดงานช่วงเวลาเดียวกันจะไม่โผล่ในรายชื่อ และบอกเหตุผลได้ว่าถูกตัดเพราะอะไร</p>
    <div class="ex">{ui.chips_soft(["ตรวจคิวอัตโนมัติ", "บอกเหตุผล"])}</div></div>
  <div class="tile champ"><span class="num">03</span><h3>จ่ายเป็นงวด ชัดเจน</h3>
    <p>แบ่งค่าตัวเป็นงวด มีสถานะรอจ่าย/จ่ายแล้ว เตือนงวดที่เลยกำหนด และกันการกดจ่ายซ้ำ ทั้งฝั่งนักแสดงและผู้จัดงานเห็นตรงกัน</p>
    <div class="ex">{ui.chips_soft(["แบ่งงวด", "กันจ่ายซ้ำ"])}</div></div>
</div>""")

# ---------------------------------------------------------------------
# แถบเลื่อน: นักแสดงแนะนำ
# ---------------------------------------------------------------------
ui.section("นักแสดงและโมเดลแนะนำ", "เลื่อนดูได้ทางขวา  ภาพวาดจากข้อมูลรูปลักษณ์ในฐานข้อมูล")
st.html('<div class="rail">' + "".join(ui.talent_card(a) for a in feat) + "</div>")
st.page_link("classic_pages/talent.py", label="ดูนักแสดงทั้งหมดในแคตตาล็อก", icon=":material/arrow_forward:")

# ---------------------------------------------------------------------
# ทักษะยอดนิยม
# ---------------------------------------------------------------------
pop = [r for r in q.dashboard_numbers()["skill_popularity"] if r["actors"] > 0][:16]
ui.section("ทักษะที่คนมีมากที่สุด")
st.html('<div>' + "".join(f'<span class="chip">{ui.esc(r["skill_name"])} · {r["actors"]}</span>' for r in pop) + "</div>")

# ---------------------------------------------------------------------
# คำถามที่พบบ่อย (กดเพื่อขยาย)
# ---------------------------------------------------------------------
ui.section("เริ่มใช้ยังไง")
st.html("""
<div class="accs">
  <details class="acc" open><summary>ฉันเป็นนักแสดง / โมเดล ต้องทำอะไรบ้าง<span class="plus"></span></summary>
    <div class="ans">1) ไปที่ <b>สมัคร / แก้โปรไฟล์</b> กรอกรูปร่าง สีผม ทักษะ ให้ตรงตามจริง
    2) เปิด <b>โปรไฟล์และผลงานของฉัน</b> ใส่ชื่อ แท็ก ผลงาน แล้วกด <b>เผยแพร่</b> ถ้ายังไม่ใส่อะไร ผู้จัดงานจะไม่เห็นคุณ
    3) เมื่อมีผู้จัดงานเลือกคุณ จะเห็นที่ <b>งานของฉัน</b> กด <b>ยอมรับ</b> หรือ <b>ปฏิเสธ</b>
    4) ดูตารางนัดและสถานะการจ่ายเงินได้ในเมนูฝั่งนักแสดง</div></details>
  <details class="acc"><summary>ฉันเป็นผู้จัดงาน หานักแสดงยังไง<span class="plus"></span></summary>
    <div class="ans">สร้าง <b>โปรเจกต์</b> แล้วไปที่ <b>สร้างบท + จับคู่นักแสดง</b> กรอกบท ทักษะที่ต้องการ ตารางนัด งวดจ่าย
    และตัวกรองรูปลักษณ์ ระบบจะคัดเฉพาะคนที่ <b>ทักษะครบ ไม่คิวชน และพร้อมรับงาน</b> แล้วคุณเลือกได้ 1 คน</div></details>
  <details class="acc"><summary>เดิมหานักแสดงทางโซเชียลมีปัญหาอะไร<span class="plus"></span></summary>
    <div class="ans">ข้อมูลกระจัดกระจายค้นหาแบบเจาะจงไม่ได้, คิวงานทับซ้อนเพราะไม่มีระบบตรวจ, และจ่ายค่าตัวซ้ำหรือตกหล่น
    เว็บนี้เก็บทุกอย่างไว้ในฐานข้อมูลเดียวแล้วให้ระบบตรวจกฎแทนคน</div></details>
  <details class="acc"><summary>ต้องล็อกอินไหม<span class="plus"></span></summary>
    <div class="ans">เวอร์ชันโปรเจกต์นี้ <b>ยังไม่มีระบบล็อกอิน</b> (ER ไม่มีตารางผู้ใช้) จึงให้เลือกชื่อตัวเองจาก dropdown
    ข้อมูลทุกคนในเว็บเป็นข้อมูลสมมติเพื่อสาธิต ปุ่มทุกปุ่มใช้งานได้จริงและเขียนลงฐานข้อมูลจริง</div></details>
</div>""")

# ---------------------------------------------------------------------
# แบนเนอร์ชวนสมัคร
# ---------------------------------------------------------------------
with st.container(key="gift"):
    st.html(f"""<div class="gift-in">{art.bow_svg()}
      <h2>พร้อมขึ้นเวทีหรือยัง</h2>
      <p>สมัครเป็นนักแสดงใช้เวลาไม่ถึงห้านาที หรือเริ่มสร้างโปรเจกต์แล้วให้ระบบหาคนที่ใช่ให้คุณ</p></div>""")
    c1, c2 = st.columns(2)
    c1.page_link("classic_pages/actor_register.py", label="สมัครเป็นนักแสดง", icon=":material/person_add:")
    c2.page_link("classic_pages/org_projects.py", label="สร้างโปรเจกต์", icon=":material/movie:")
