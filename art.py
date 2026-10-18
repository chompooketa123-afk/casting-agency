"""
art.py : วาดภาพประกอบเป็น SVG จากข้อมูลในฐานข้อมูลโดยตรง (ไม่ต้องมีไฟล์รูป ไม่ต้องต่ออินเทอร์เน็ต)

ทำไมไม่ใช้รูปถ่ายจริง
  - ไฟล์ ACTOR ใน ER ไม่มีคอลัมน์รูป และรูปคนจริงมีเรื่องสิทธิ์ภาพ
  - ภาพนี้วาดจากคอลัมน์ในตาราง ACTOR (สีผิว สีผม ความยาว/ลักษณะผม สีตา รูปร่าง เจาะหู)
    ถ้าแก้ข้อมูลในฐานข้อมูล ภาพก็เปลี่ยนตามเอง = เป็นหลักฐานว่าข้อมูลรูปลักษณ์ที่เก็บไว้ใช้งานได้จริง
"""
import base64
from html import escape as esc


def _img(svg, cls, alt=""):
    """st.html ลบ <svg> ทิ้ง (DOMPurify) จึงส่งเป็น <img> แบบ data URI แทน"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img class="{cls}" alt="{esc(alt)}" src="data:image/svg+xml;base64,{b64}">'

SKIN = {"Fair": "#F6DDCB", "Light": "#EDC9A9", "Medium": "#D8A67E", "Tan": "#BC8854", "Deep": "#7B4B30"}
HAIR = {"Black": "#1D1618", "Dark_Brown": "#3B261D", "Brown": "#5E3C2A", "Light_Brown": "#8E6644",
        "Blonde": "#DDBF72", "Red": "#9D3C26", "Gray": "#C4C2C6", "Dyed": "#E8A4BE"}
EYE = {"Black": "#1B1517", "Dark_Brown": "#3A2418", "Brown": "#6B4228", "Hazel": "#8A6B2F",
       "Green": "#4C7A58", "Blue": "#4B78A8", "Gray": "#7C8794"}
CLOTHES = ["#5E1A2E", "#1E2A3F", "#F1E9E1", "#1F1A1D", "#B8955A", "#7F93A8", "#8B5A66"]
TILES = ["rose", "powder", "champ", "mauve", "sage"]     # ชื่อคลาสสีพื้นการ์ด (กำหนดสีใน theme.css)
SHOULDER = {"Slim": 60, "Athletic": 70, "Average": 66, "Curvy": 74, "Plus_Size": 84, "Muscular": 86}


def tile_of(a):
    """สีพื้นการ์ดของนักแสดงคนนี้ (วนตามรหัส ให้สีคงที่ทุกครั้งที่เปิด)"""
    return TILES[(int(a.get("actor_id") or 0)) % len(TILES)]


def _shade(hex_color, k):
    """ทำสีให้เข้มขึ้น (k<1) หรืออ่อนลง (k>1)"""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if k <= 1:
        r, g, b = (int(c * k) for c in (r, g, b))
    else:
        r, g, b = (int(c + (255 - c) * (k - 1)) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def _scallop(x0, x1, y, n, depth):
    """ขอบล่างหยักเป็นคลื่น (ผมลอน) จากขวาไปซ้าย"""
    step = (x1 - x0) / n
    d, x = "", x1
    for _ in range(n):
        d += f" Q{x - step / 2:.1f} {y + depth} {x - step:.1f} {y}"
        x -= step
    return d


def avatar_svg(a, label=True, raw=False):
    """วาดภาพครึ่งตัวสไตล์ fashion illustration จากข้อมูลรูปลักษณ์ของนักแสดง (dict แถวจาก ACTOR)"""
    skin = SKIN.get(a.get("skin_tone"), SKIN["Medium"])
    hair_c = HAIR.get(a.get("hair_color"), HAIR["Dark_Brown"])
    eye_c = EYE.get(a.get("eye_color"), EYE["Dark_Brown"])
    length = a.get("hair_length") or "Short"
    texture = a.get("hair_texture") or "Straight"
    body = a.get("body_type") or "Average"
    gender = a.get("gender")
    detail = a.get("appearance_detail") or ""
    aid = int(a.get("actor_id") or 0)
    cloth = CLOTHES[(aid * 3 + 1) % len(CLOTHES)]
    sw = SHOULDER.get(body, 66)
    fw = 36 if gender == "Male" else 33           # ครึ่งความกว้างใบหน้า
    skin_d = _shade(skin, 0.86)
    hair_d = _shade(hair_c, 0.72)
    lip = "#8F3A4A" if a.get("skin_tone") in ("Tan", "Deep") else "#B85B70"
    parts = []

    # ---- ผมด้านหลัง (วาดก่อนตัวและหน้า) ----
    if length in ("Long", "Medium") and texture != "Curly":
        bottom = 212 if length == "Long" else 160
        side = 50 if length == "Long" else 58
        edge = _scallop(100 - side - 2, 100 + side + 2, bottom, 6, 8) if texture == "Wavy" else \
            f" L{100 - side - 2} {bottom}"
        if texture == "Wavy":
            path = (f"M{100 - fw - 8} 104 C{100 - fw - 14} 44 {100 - 24} 30 100 30 C{100 + 24} 30 {100 + fw + 14} 44 "
                    f"{100 + fw + 8} 104 L{100 + side + 2} {bottom}{edge} Z")
        else:
            path = (f"M{100 - fw - 8} 104 C{100 - fw - 14} 44 {100 - 24} 30 100 30 C{100 + 24} 30 {100 + fw + 14} 44 "
                    f"{100 + fw + 8} 104 L{100 + side + 2} {bottom} Q100 {bottom + 10} {100 - side - 2} {bottom} Z")
        parts.append(f'<path d="{path}" fill="{hair_c}"/>')
    if texture == "Curly" and length != "Shaved":
        ys = [88, 110] + ([134, 158] if length == "Long" else [134] if length == "Medium" else [])
        for y in ys:
            parts.append(f'<circle cx="{100 - fw - 10}" cy="{y}" r="13" fill="{hair_c}"/>')
            parts.append(f'<circle cx="{100 + fw + 10}" cy="{y}" r="13" fill="{hair_c}"/>')

    # ---- ตัว + คอ ----
    parts.append(f'<path d="M{100 - sw} 240 C{100 - sw} 206 {100 - sw + 8} 190 66 182 L134 182 '
                 f'C{100 + sw - 8} 190 {100 + sw} 206 {100 + sw} 240 Z" fill="{cloth}"/>')
    parts.append(f'<rect x="87" y="136" width="26" height="52" rx="10" fill="{skin_d}"/>')
    parts.append(f'<path d="M80 184 Q100 214 120 184 Z" fill="{skin_d}"/>')
    parts.append(f'<path d="M86 184 Q100 206 114 184" fill="none" stroke="{_shade(cloth, 0.7)}" stroke-width="1.2" opacity=".5"/>')

    # ---- หู + หน้า ----
    parts.append(f'<circle cx="{100 - fw}" cy="106" r="6" fill="{skin_d}"/><circle cx="{100 + fw}" cy="106" r="6" fill="{skin_d}"/>')
    parts.append(f'<ellipse cx="100" cy="100" rx="{fw}" ry="42" fill="{skin}"/>')
    if a.get("has_piercing"):
        parts.append(f'<circle cx="{100 - fw}" cy="115" r="2.6" fill="#D4B06A"/><circle cx="{100 + fw}" cy="115" r="2.6" fill="#D4B06A"/>')

    # ---- หนวดเครา (อ่านจากรายละเอียดรูปลักษณ์) ----
    if "เครา" in detail or "หนวด" in detail:
        parts.append(f'<path d="M{100 - fw + 1} 108 C{100 - fw + 2} 140 86 148 100 148 C114 148 {100 + fw - 2} 140 '
                     f'{100 + fw - 1} 108 C{100 + fw - 8} 124 116 124 100 124 C84 124 {100 - fw + 8} 124 {100 - fw + 1} 108 Z" '
                     f'fill="{hair_d}" opacity=".88"/>')

    # ---- ผมด้านหน้า ----
    if length == "Shaved":
        parts.append(f'<path d="M{100 - fw + 1} 92 C{100 - fw} 56 80 56 100 56 C120 56 {100 + fw} 56 {100 + fw - 1} 92 '
                     f'C{100 + fw - 6} 76 116 70 100 70 C84 70 {100 - fw + 6} 76 {100 - fw + 1} 92 Z" fill="{hair_d}" opacity=".35"/>')
    else:
        top = 34 if texture != "Curly" else 30
        parts.append(
            f'<path d="M{100 - fw - 4} 102 C{100 - fw - 8} 52 {100 - 22} {top} 100 {top} C{100 + 22} {top} {100 + fw + 8} 52 '
            f'{100 + fw + 4} 102 C{100 + fw - 1} 84 {100 + fw - 8} 70 {100 + 12} 64 C{100 - 8} 74 {100 - fw + 8} 74 '
            f'{100 - fw + 2} 98 C{100 - fw - 1} 94 {100 - fw - 3} 98 {100 - fw - 4} 102 Z" fill="{hair_c}"/>')
        if texture == "Curly":
            for x, y in ((66, 62), (80, 46), (100, 40), (120, 46), (134, 62)):
                parts.append(f'<circle cx="{x}" cy="{y}" r="12" fill="{hair_c}"/>')
        if length == "Short" and texture == "Wavy":
            parts.append(f'<path d="M64 76 Q80 56 100 60" stroke="{_shade(hair_c, 1.35)}" stroke-width="2" fill="none" opacity=".5"/>')

    # ---- หน้าตา ----
    brow = hair_d if a.get("hair_color") not in ("Blonde", "Gray", "Dyed") else _shade(hair_c, 0.6)
    parts.append(f'<path d="M80 94 Q87 90 94 93" stroke="{brow}" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
                 f'<path d="M106 93 Q113 90 120 94" stroke="{brow}" stroke-width="2.2" fill="none" stroke-linecap="round"/>')
    for cx in (87, 113):
        parts.append(f'<ellipse cx="{cx}" cy="104" rx="5" ry="3" fill="#FFFFFF" opacity=".95"/>'
                     f'<circle cx="{cx}" cy="104" r="2.5" fill="{eye_c}"/>'
                     f'<path d="M{cx - 5.5} 103 Q{cx} 99 {cx + 5.5} 103" stroke="#2A1F22" stroke-width="1.5" fill="none" stroke-linecap="round"/>')
    if "แว่น" in detail:
        parts.append('<g fill="none" stroke="#2A2326" stroke-width="1.8"><circle cx="87" cy="104" r="10"/>'
                     '<circle cx="113" cy="104" r="10"/><path d="M97 103 H103"/></g>')
    parts.append(f'<path d="M100 108 q-3.5 10 0 13" stroke="{skin_d}" stroke-width="1.6" fill="none" stroke-linecap="round"/>')
    parts.append(f'<path d="M91.5 129 Q100 124.5 108.5 129 Q100 138 91.5 129 Z" fill="{lip}"/>')

    svg = ('<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg" '
           f'preserveAspectRatio="xMidYMax slice">{"".join(parts)}</svg>')
    if raw:
        return svg
    return _img(svg, "avatar", a.get("full_name") if label else "")


def bow_svg():
    """โบว์ทองสไตล์ของขวัญ ใช้บนแบนเนอร์ชวนสมัคร"""
    return _img('<svg viewBox="0 0 120 90" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M60 52 C30 6 4 14 8 40 C12 66 44 62 60 52 Z" fill="#D8BF8C"/>'
            '<path d="M60 52 C90 6 116 14 112 40 C108 66 76 62 60 52 Z" fill="#C7A468"/>'
            '<path d="M60 52 C46 60 30 80 22 88 L40 84 L56 62 Z" fill="#B8955A"/>'
            '<path d="M60 52 C74 60 90 80 98 88 L80 84 L64 62 Z" fill="#A98445"/>'
            '<circle cx="60" cy="50" r="11" fill="#E6D2A3"/></svg>', "bow")


def sparkle_svg(size=22):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
           '<path d="M12 0 C13 8 16 11 24 12 C16 13 13 16 12 24 C11 16 8 13 0 12 C8 11 11 8 12 0Z" fill="#B8955A"/></svg>')
    return _img(svg, "sparkle").replace("<img ", f'<img width="{size}" height="{size}" ', 1)


def eye_svg(off=False, color="#2F6F57", size=26):
    """ไอคอนรูปตา (off=True มีเส้นขีดฆ่า) ใช้ในแผงสถานะโปรไฟล์ ต้องระบุสีตรงๆ เพราะเป็นรูป data URI"""
    slash = '<path d="M3 3l18 18"/>' if off else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.6" '
           'stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/>'
           f'<circle cx="12" cy="12" r="3"/>{slash}</svg>')
    return _img(svg, "eye").replace("<img ", f'<img width="{size}" height="{size}" ', 1)
