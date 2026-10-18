
/* core.js : กฎธุรกิจฝั่งหน้าเว็บ (ตรวจให้ผู้ใช้เห็นผลทันที) + ภาพวาดนักแสดง
   ข้อมูลจริงอยู่ใน MySQL: ทุกครั้งที่บันทึก ฝั่งเซิร์ฟเวอร์ (bridge.py > queries.py) ตรวจกฎอีกรอบแล้วรัน SQL จริง */

/* ====================== ป้ายภาษาไทย (ตรงกับ config.py) ====================== */
const L = {
  roleSt: { Selected: 'รอนักแสดงตอบรับ', Confirmed: 'ยืนยันแล้ว', Rejected_by_Actor: 'นักแสดงปฏิเสธ', Cancelled_by_Organizer: 'ผู้จัดงานยกเลิก' },
  paySt: { Pending: 'รอจ่าย', Paid: 'จ่ายแล้ว', Cancelled: 'ยกเลิก' },
  event: { Shoot: 'ถ่ายทำ', Fitting: 'ฟิตติ้ง', Rehearsal: 'ซ้อม' },
  gender: { Male: 'ชาย', Female: 'หญิง', Other: 'อื่นๆ' },
  actorSt: { Active: 'พร้อมรับงาน', Inactive: 'พักงาน' },
  skillType: { Modeling: 'งานโมเดลลิ่ง', Performance: 'การแสดง', Language: 'ภาษา', Physical: 'ร่างกายและกีฬา', Other: 'ทักษะอื่นๆ' },
  projType: { Series: 'ซีรีส์', Movie: 'ภาพยนตร์', Commercial: 'โฆษณา', Music_Video: 'มิวสิกวิดีโอ', Fashion_Show: 'โชว์แฟชั่น', Other: 'อื่นๆ' },
  projSt: { Open: 'เปิดรับ', In_Progress: 'กำลังดำเนินการ', Completed: 'เสร็จสิ้น', Cancelled: 'ยกเลิก' },
  work: { Film: 'ภาพยนตร์', Series: 'ซีรีส์/ละคร', Commercial: 'โฆษณา', Runway: 'รันเวย์/แฟชั่นโชว์', Photoshoot: 'ถ่ายแบบ/แคมเปญ', Music_Video: 'มิวสิกวิดีโอ', Stage: 'เวที/ละครเวที', Online: 'ออนไลน์/คอนเทนต์', Other: 'อื่นๆ' },
  body: { Slim: 'เพรียว', Athletic: 'ฟิต/นักกีฬา', Average: 'สมส่วน', Curvy: 'เว้าโค้ง', Plus_Size: 'พลัสไซซ์', Muscular: 'กล้ามเนื้อ' },
  skin: { Fair: 'ขาวอมชมพู', Light: 'ขาวเหลือง', Medium: 'ผิวสองสี', Tan: 'ผิวแทน', Deep: 'ผิวเข้ม' },
  hairC: { Black: 'ดำ', Dark_Brown: 'น้ำตาลเข้ม', Brown: 'น้ำตาล', Light_Brown: 'น้ำตาลอ่อน', Blonde: 'บลอนด์/ทอง', Red: 'แดง/น้ำตาลแดง', Gray: 'เทา/เงิน/ขาว', Dyed: 'ทำสีแฟชั่น' },
  hairL: { Shaved: 'โกน/เกรียน', Short: 'สั้น', Medium: 'ประบ่า', Long: 'ยาว' },
  hairT: { Straight: 'ตรง', Wavy: 'ลอน', Curly: 'หยิก' },
  eye: { Black: 'ดำ', Dark_Brown: 'น้ำตาลเข้ม', Brown: 'น้ำตาล', Hazel: 'เฮเซล', Green: 'เขียว', Blue: 'ฟ้า', Gray: 'เทา' },
  exp: { Beginner: 'มือใหม่', Intermediate: 'มีประสบการณ์', Professional: 'มืออาชีพ' },
};
const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
const SKILL_TYPES = Object.keys(L.skillType);
const MAX_WORKS = 20;
const PROVINCES = ["กรุงเทพมหานคร","กระบี่","กาญจนบุรี","กาฬสินธุ์","กำแพงเพชร","ขอนแก่น","จันทบุรี","ฉะเชิงเทรา","ชลบุรี","ชัยนาท","ชัยภูมิ","ชุมพร","เชียงราย","เชียงใหม่","ตรัง","ตราด","ตาก","นครนายก","นครปฐม","นครพนม","นครราชสีมา","นครศรีธรรมราช","นครสวรรค์","นนทบุรี","นราธิวาส","น่าน","บึงกาฬ","บุรีรัมย์","ปทุมธานี","ประจวบคีรีขันธ์","ปราจีนบุรี","ปัตตานี","พระนครศรีอยุธยา","พะเยา","พังงา","พัทลุง","พิจิตร","พิษณุโลก","เพชรบุรี","เพชรบูรณ์","แพร่","ภูเก็ต","มหาสารคาม","มุกดาหาร","แม่ฮ่องสอน","ยโสธร","ยะลา","ร้อยเอ็ด","ระนอง","ระยอง","ราชบุรี","ลพบุรี","ลำปาง","ลำพูน","เลย","ศรีสะเกษ","สกลนคร","สงขลา","สตูล","สมุทรปราการ","สมุทรสงคราม","สมุทรสาคร","สระแก้ว","สระบุรี","สิงห์บุรี","สุโขทัย","สุพรรณบุรี","สุราษฎร์ธานี","สุรินทร์","หนองคาย","หนองบัวลำภู","อ่างทอง","อำนาจเจริญ","อุดรธานี","อุตรดิตถ์","อุทัยธานี","อุบลราชธานี"];

/* ====================== ตัวช่วยทั่วไป ====================== */
const $ = (s, r = ROOT) => r.querySelector(s);
const $$ = (s, r = ROOT) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pad = n => String(n).padStart(2, '0');
const isoOf = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const TODAY = () => isoOf(new Date());
const addDays = (iso, n) => { const d = new Date(iso + 'T00:00:00'); d.setDate(d.getDate() + n); return isoOf(d); };
const money = n => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
const ageOf = iso => {
  if (!iso) return null;
  const b = new Date(iso + 'T00:00:00'), t = new Date();
  let a = t.getFullYear() - b.getFullYear();
  if (t.getMonth() < b.getMonth() || (t.getMonth() === b.getMonth() && t.getDate() < b.getDate())) a--;
  return a;
};
const thDate = iso => iso ? new Date(iso + 'T00:00:00').toLocaleDateString('th-TH', { day: 'numeric', month: 'short', year: 'numeric' }) : '-';
const byName = (a, b) => a.name.localeCompare(b.name, 'th');
class BizErr extends Error {}
const fail = m => { throw new BizErr(m); };

/* ====================== ข้อมูลที่ได้จาก MySQL (snapshot ล่าสุด) ====================== */
let DB = null;
const ME_KEY = 'casting-me';
function fromSnap(s) {
  const mx = a => a.reduce((m, x) => Math.max(m, x), 0);
  const db = {
    skills: s.skills, actors: s.actors, projects: s.projects, roles: s.roles, me: null,
    nid: { actor: mx(s.actors.map(a => a.id)) + 1, project: mx(s.projects.map(p => p.id)) + 1, role: mx(s.roles.map(r => r.id)) + 1,
      pay: mx(s.roles.flatMap(r => r.pay.map(p => p.id))) + 1, work: mx(s.actors.flatMap(a => a.works.map(w => w.id))) + 1 },
  };
  return db;
}
function pickMe(db, prefer) {
  let id = prefer;
  if (!db.actors.some(a => a.id === id)) { try { id = Number(localStorage.getItem(ME_KEY)); } catch (e) { id = null; } }
  if (!db.actors.some(a => a.id === id)) { const sel = db.roles.find(r => r.status === 'Selected'); id = sel ? sel.actor : (db.actors[0] || {}).id; }
  db.me = id;
}
function setMe(id) { DB.me = id; try { localStorage.setItem(ME_KEY, String(id)); } catch (e) {} }
function applySnap(s) { const prev = DB ? DB.me : null; DB = fromSnap(s); pickMe(DB, prev); }
function save() { /* ไม่ต้องบันทึกในเบราว์เซอร์ ข้อมูลจริงอยู่ใน MySQL */ }

/* ---------- ตัวค้นหาพื้นฐาน ---------- */
const actorOf = id => DB.actors.find(a => a.id === id);
const skillName = id => (DB.skills.find(s => s.id === id) || {}).name || '?';
const projOf = id => DB.projects.find(p => p.id === id);
const BUSY = ['Selected', 'Confirmed'];
const isOverdue = p => p.status === 'Pending' && p.due < TODAY();

/* ====================== กฎธุรกิจ (พอร์ตจาก queries.py) ====================== */
function num(v) { return v === '' || v == null ? null : Number(v); }
function cleanProfile(p) {
  const out = {};
  if (p.birth) {
    const age = ageOf(p.birth);
    if (age == null || isNaN(age)) fail('วันเกิดไม่ถูกต้อง');
    if (age < 18) fail('ระบบรับเฉพาะผู้ที่อายุ 18 ปีขึ้นไป');
    if (age > 90) fail('วันเกิดไม่สมเหตุสมผล');
    out.birth = p.birth;
  } else out.birth = null;
  const rng = [['h', 'ส่วนสูง', 100, 230], ['w', 'น้ำหนัก', 25, 250], ['bust', 'รอบอก', 40, 200], ['waist', 'รอบเอว', 40, 200], ['hip', 'รอบสะโพก', 40, 200], ['shoe', 'เบอร์รองเท้า', 30, 50]];
  for (const [k, th, lo, hi] of rng) {
    const v = p[k];
    if (v === '' || v == null) { out[k] = null; continue; }
    const n = Number(v);
    if (isNaN(n)) fail(`${th} ต้องเป็นตัวเลข`);
    if (n < lo || n > hi) fail(`${th} ต้องอยู่ระหว่าง ${lo}-${hi}`);
    out[k] = (k === 'w' || k === 'shoe') ? n : Math.round(n);
  }
  for (const k of ['size', 'body', 'skin', 'hairC', 'hairL', 'hairT', 'eye', 'prov']) out[k] = p[k] || null;
  out.exp = p.exp || 'Beginner';
  for (const k of ['tattoo', 'pierce', 'travel']) out[k] = !!p[k];
  return out;
}
const cleanBio = b => { b = (b || '').trim(); if (b.length > 500) fail('แนะนำตัวยาวเกิน 500 ตัวอักษร'); return b; };
function syncVis(a) { if (a.pub && !a.skills.length && !a.works.length) a.pub = false; return a.pub; }

function registerActor(f, skillIds, publish) {
  const name = (f.name || '').trim();
  if (!name) fail('กรุณากรอกชื่อ-นามสกุล');
  const prof = cleanProfile(f), bio = cleanBio(f.bio);
  const ids = [...new Set(skillIds)];
  const a = { id: DB.nid.actor++, name, gender: f.gender || 'Female', status: 'Active', look: (f.look || '').trim(), bio, pub: !!(publish && ids.length), works: [], skills: ids.sort((x, y) => x - y), ...prof };
  DB.actors.push(a); save(); return a.id;
}
function updateActor(id, f, skillIds) {
  const a = actorOf(id); if (!a) fail('ไม่พบนักแสดงคนนี้');
  const name = (f.name || '').trim(); if (!name) fail('ชื่อห้ามว่าง');
  const prof = cleanProfile(f), bio = cleanBio(f.bio);
  Object.assign(a, prof, { name, gender: f.gender || a.gender, status: f.status || a.status, look: (f.look || '').trim(), bio, skills: [...new Set(skillIds)].sort((x, y) => x - y) });
  const v = syncVis(a); save(); return v;
}
function readiness(a) {
  const r = { hasName: !!(a.name || '').trim(), hasBio: !!a.bio, nSkills: a.skills.length, nWorks: a.works.length, pub: a.pub };
  r.ready = r.hasName && (r.nSkills > 0 || r.nWorks > 0); return r;
}
function setPublic(id, pub) {
  const a = actorOf(id);
  if (pub && !readiness(a).ready) fail('ยังเผยแพร่ไม่ได้ ต้องเลือกแท็กทักษะหรือเพิ่มผลงานอย่างน้อย 1 อย่างก่อน');
  a.pub = !!pub; save();
}
function cleanWork(w) {
  const title = (w.title || '').trim();
  if (!title) fail('กรุณากรอกชื่อผลงาน');
  if (title.length > 150) fail('ชื่อผลงานยาวเกิน 150 ตัวอักษร');
  if (!L.work[w.type]) fail('ประเภทผลงานไม่ถูกต้อง');
  const y = Number(w.year);
  if (!Number.isInteger(y)) fail('ปีของผลงานต้องเป็นตัวเลข');
  const cy = new Date().getFullYear();
  if (y < 1980 || y > cy + 1) fail(`ปีของผลงานต้องอยู่ระหว่าง 1980-${cy + 1}`);
  const role = (w.role || '').trim(); if (role.length > 100) fail('ชื่อบทยาวเกิน 100 ตัวอักษร');
  const desc = (w.desc || '').trim(); if (desc.length > 500) fail('รายละเอียดผลงานยาวเกิน 500 ตัวอักษร');
  const url = (w.url || '').trim();
  if (url && (!/^https?:\/\//i.test(url) || url.length > 300)) fail('ลิงก์ต้องขึ้นต้นด้วย http:// หรือ https:// (ยาวไม่เกิน 300 ตัวอักษร)');
  return { title, type: w.type, role, year: y, desc, url };
}
function addWork(aid, w) {
  const a = actorOf(aid); if (!a) fail('ไม่พบนักแสดงคนนี้');
  const c = cleanWork(w);
  if (a.works.length >= MAX_WORKS) fail(`เพิ่มผลงานได้สูงสุด ${MAX_WORKS} ชิ้น ลบอันเก่าก่อนจึงจะเพิ่มได้`);
  a.works.push({ id: DB.nid.work++, ...c }); save();
}
function updateWork(aid, wid, w) {
  const a = actorOf(aid), x = a && a.works.find(k => k.id === wid);
  if (!x) fail('ไม่พบผลงานนี้ในโปรไฟล์ของคุณ');
  Object.assign(x, cleanWork(w)); save();
}
function deleteWork(aid, wid) {
  const a = actorOf(aid), i = a ? a.works.findIndex(k => k.id === wid) : -1;
  if (i < 0) fail('ไม่พบผลงานนี้ในโปรไฟล์ของคุณ');
  a.works.splice(i, 1); const v = syncVis(a); save(); return v;
}
function createProject(name, type, client) {
  name = (name || '').trim(); client = (client || '').trim();
  if (!name || !client) fail('กรุณากรอกชื่อโปรเจกต์และชื่อลูกค้า');
  const p = { id: DB.nid.project++, name, type, status: 'Open', client }; DB.projects.push(p); save(); return p.id;
}

/* ---------- ตัวกรองรูปลักษณ์ ---------- */
const TRAIT_LISTS = {
  body: ['รูปร่าง', L.body, 'body'], skin: ['สีผิว', L.skin, 'skin'], eye: ['สีตา', L.eye, 'eye'],
  hairC: ['สีผม', L.hairC, 'hairC'], hairL: ['ความยาวผม', L.hairL, 'hairL'], hairT: ['ลักษณะผม', L.hairT, 'hairT'], exp: ['ระดับประสบการณ์', L.exp, 'exp'],
};
function traitFails(a, t) {
  const why = [], age = ageOf(a.birth);
  if (t.ageMin != null && (age == null || age < t.ageMin)) why.push(age != null ? `อายุต่ำกว่า ${t.ageMin} ปี` : 'ไม่ระบุอายุ');
  if (t.ageMax != null && (age == null || age > t.ageMax)) why.push(age != null ? `อายุเกิน ${t.ageMax} ปี` : 'ไม่ระบุอายุ');
  if (t.hMin != null && (a.h == null || a.h < t.hMin)) why.push(a.h ? `ส่วนสูง ${a.h} ซม. ต่ำกว่า ${t.hMin}` : 'ไม่ระบุส่วนสูง');
  if (t.hMax != null && (a.h == null || a.h > t.hMax)) why.push(a.h ? `ส่วนสูง ${a.h} ซม. เกิน ${t.hMax}` : 'ไม่ระบุส่วนสูง');
  for (const [k, [th, labels, col]] of Object.entries(TRAIT_LISTS)) {
    const vals = t[k] || [];
    if (vals.length && !vals.includes(a[col])) why.push(`${th}ไม่ตรง (เป็น ${labels[a[col]] || a[col] || 'ไม่ระบุ'} ต้องการ ${vals.map(v => labels[v] || v).join('/')})`);
  }
  if (t.prov && a.prov !== t.prov) why.push(`จังหวัดไม่ตรง (เป็น ${a.prov || 'ไม่ระบุ'} ต้องการ ${t.prov})`);
  for (const [k, col, th] of [['tattoo', 'tattoo', 'รอยสัก'], ['pierce', 'pierce', 'เจาะ'], ['travel', 'travel', 'เดินทางต่างจังหวัด']])
    if (t[k] != null && !!a[col] !== t[k]) why.push(`${th}ไม่ตรง (${t[k] ? 'ต้องมี' : 'ต้องไม่มี'})`);
  return why;
}
function hasSkills(a, ids) { return ids.every(i => a.skills.includes(i)); }
function conflictsOf(actorId, slot) {
  const out = [];
  for (const r of DB.roles) if (r.actor === actorId && BUSY.includes(r.status))
    for (const s of r.sched) if (s.date === slot.date && s.start < slot.end && s.end > slot.start) out.push({ role: r, s });
  return out;
}
function validateSlots(slots) {
  slots.forEach((s, i) => { if (!s.date) fail(`ตารางนัดแถวที่ ${i + 1}: กรุณาเลือกวันที่`); if (!s.start || !s.end) fail(`ตารางนัดแถวที่ ${i + 1}: กรุณาใส่เวลา`); if (s.end <= s.start) fail(`ตารางนัดแถวที่ ${i + 1}: เวลาเลิกต้องหลังเวลาเริ่ม`); });
  for (let i = 0; i < slots.length; i++) for (let j = i + 1; j < slots.length; j++) {
    const a = slots[i], b = slots[j];
    if (a.date === b.date && a.start < b.end && a.end > b.start) fail(`ตารางนัดแถวที่ ${i + 1} และ ${j + 1} ซ้อนเวลากันเอง`);
  }
}
const cents = n => Math.round(Number(n) * 100);
function validateInst(inst, fee) {
  if (!inst.length) fail('ต้องมีงวดจ่ายเงินอย่างน้อย 1 งวด');
  let total = 0;
  inst.forEach((i, n) => { if (!i.due) fail(`งวดที่ ${n + 1}: กรุณาเลือกวันครบกำหนด`); if (!(cents(i.amount) > 0)) fail(`งวดที่ ${n + 1}: จำนวนเงินต้องมากกว่า 0`); total += cents(i.amount); });
  if (total !== cents(fee)) fail(`ยอดรวมทุกงวด (${money(total / 100)}) ไม่เท่ากับค่าตัวที่ตกลง (${money(cents(fee) / 100)})`);
}
function findMatching(skillIds, slots, gender, traits) {
  validateSlots(slots);
  return DB.actors.filter(a => a.pub && a.status === 'Active' && !traitFails(a, traits).length && (!gender || a.gender === gender)
    && hasSkills(a, skillIds) && slots.every(s => !conflictsOf(a.id, s).length)).sort(byName);
}
function explainExcluded(skillIds, slots, eligibleIds, gender, traits) {
  const out = [];
  for (const a of DB.actors.filter(a => a.pub && !eligibleIds.includes(a.id)).sort(byName)) {
    const rs = [];
    if (a.status !== 'Active') rs.push('สถานะ Inactive (พักงาน)');
    if (gender && a.gender !== gender) rs.push('เพศไม่ตรงตัวกรอง');
    const miss = skillIds.filter(i => !a.skills.includes(i)).map(skillName);
    if (miss.length) rs.push('ทักษะไม่ครบ: ขาด ' + miss.join(', '));
    rs.push(...traitFails(a, traits));
    for (const s of slots) for (const c of conflictsOf(a.id, s)) rs.push(`คิวชน: ติดงาน '${projOf(c.role.project).name}' (${c.role.name}) ${s.date} ${c.s.start}-${c.s.end}`);
    if (rs.length) out.push({ id: a.id, name: a.name, reasons: rs });
  }
  return out;
}
function searchActors(o) {
  if (o.avail && o.avail.end <= o.avail.start) fail('เวลาสิ้นสุดต้องหลังเวลาเริ่ม');
  const text = (o.text || '').trim().toLowerCase();
  return DB.actors.filter(a => a.pub && (!o.onlyActive || a.status === 'Active') && !traitFails(a, o.traits).length
    && (!o.gender || a.gender === o.gender)
    && (!text || (a.look || '').toLowerCase().includes(text) || a.name.toLowerCase().includes(text))
    && hasSkills(a, o.skills) && (!o.avail || !conflictsOf(a.id, o.avail).length)).sort(byName);
}
function createRole(m, actorId) {
  const name = (m.roleName || '').trim();
  if (!name) fail('กรุณากรอกชื่อบท');
  if (!(cents(m.fee) > 0)) fail('ค่าตัวต้องมากกว่า 0');
  validateSlots(m.slots); validateInst(m.inst, m.fee);
  const a = actorOf(actorId);
  if (a && !a.pub) fail('นักแสดงคนนี้ปิดโปรไฟล์อยู่ เลือกเข้าบทไม่ได้');
  if (!a || a.status !== 'Active') fail('นักแสดงคนนี้ไม่ได้อยู่ในสถานะ Active');
  const p = projOf(m.project);
  if (!p || ['Completed', 'Cancelled'].includes(p.status)) fail('โปรเจกต์นี้ปิดแล้วหรือถูกยกเลิก เพิ่มบทไม่ได้');
  if (!hasSkills(a, m.skills)) fail('นักแสดงมีทักษะไม่ครบตามที่บทต้องการ');
  for (const s of m.slots) {
    const hit = conflictsOf(actorId, s)[0];
    if (hit) fail(`คิวชน! นักแสดงติดงาน '${projOf(hit.role.project).name}' (${hit.role.name}) ในวันที่ ${s.date} ช่วง ${s.start}-${s.end}`);
  }
  const r = {
    id: DB.nid.role++, name, fee: Number(m.fee), status: 'Selected', actor: actorId, project: m.project, skills: m.skills.slice().sort((x, y) => x - y),
    sched: m.slots.map(s => ({ ...s })), pay: m.inst.map(i => ({ id: DB.nid.pay++, amount: Number(i.amount), status: 'Pending', due: i.due })),
  };
  DB.roles.push(r); save(); return r.id;
}
function respondRole(rid, actorId, accept) {
  const r = DB.roles.find(x => x.id === rid);
  if (!r || r.actor !== actorId || r.status !== 'Selected') fail('ตอบรับไปแล้ว หรือบทนี้ถูกยกเลิกแล้ว');
  r.status = accept ? 'Confirmed' : 'Rejected_by_Actor';
  if (!accept) r.pay.forEach(p => { if (p.status === 'Pending') p.status = 'Cancelled'; });
  save();
}
function cancelRole(rid) {
  const r = DB.roles.find(x => x.id === rid);
  if (!r || !BUSY.includes(r.status)) fail('บทนี้ถูกปฏิเสธหรือยกเลิกไปแล้ว');
  r.status = 'Cancelled_by_Organizer';
  r.pay.forEach(p => { if (p.status === 'Pending') p.status = 'Cancelled'; });
  save();
}
function markPaid(pid) {
  for (const r of DB.roles) for (const p of r.pay) if (p.id === pid) {
    if (p.status === 'Pending' && r.status === 'Confirmed') { p.status = 'Paid'; save(); return; }
    if (p.status === 'Paid') fail('งวดนี้จ่ายไปแล้ว จ่ายซ้ำไม่ได้');
    if (p.status === 'Cancelled') fail('งวดนี้ถูกยกเลิกแล้ว');
    fail('จ่ายได้เฉพาะบทที่นักแสดงยืนยันแล้ว (Confirmed)');
  }
  fail('ไม่พบงวดนี้');
}
const allPayments = () => DB.roles.flatMap(r => r.pay.map(p => ({ ...p, role: r, project: projOf(r.project), actor: actorOf(r.actor) })));

/* ====================== ภาพวาดตัวแทนนักแสดง (พอร์ตจาก art.py) ====================== */
const SKIN = { Fair: '#F6DDCB', Light: '#EDC9A9', Medium: '#D8A67E', Tan: '#BC8854', Deep: '#7B4B30' };
const HAIR = { Black: '#1D1618', Dark_Brown: '#3B261D', Brown: '#5E3C2A', Light_Brown: '#8E6644', Blonde: '#DDBF72', Red: '#9D3C26', Gray: '#C4C2C6', Dyed: '#E8A4BE' };
const EYEC = { Black: '#1B1517', Dark_Brown: '#3A2418', Brown: '#6B4228', Hazel: '#8A6B2F', Green: '#4C7A58', Blue: '#4B78A8', Gray: '#7C8794' };
const CLOTHES = ['#5E1A2E', '#1E2A3F', '#F1E9E1', '#1F1A1D', '#B8955A', '#7F93A8', '#8B5A66'];
const TILES = ['rose', 'powder', 'champ', 'mauve', 'sage'];
const SHOULDER = { Slim: 60, Athletic: 70, Average: 66, Curvy: 74, Plus_Size: 84, Muscular: 86 };
const tileOf = a => TILES[a.id % TILES.length];
function shade(hex, k) {
  const h = hex.replace('#', ''); let c = [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16));
  c = k <= 1 ? c.map(v => Math.floor(v * k)) : c.map(v => Math.floor(v + (255 - v) * (k - 1)));
  return '#' + c.map(v => v.toString(16).padStart(2, '0')).join('').toUpperCase();
}
function scallop(x0, x1, y, n, depth) {
  const step = (x1 - x0) / n; let d = '', x = x1;
  for (let i = 0; i < n; i++) { d += ` Q${(x - step / 2).toFixed(1)} ${y + depth} ${(x - step).toFixed(1)} ${y}`; x -= step; }
  return d;
}
function avatar(a) {
  const skin = SKIN[a.skin] || SKIN.Medium, hairC = HAIR[a.hairC] || HAIR.Dark_Brown, eyeC = EYEC[a.eye] || EYEC.Dark_Brown;
  const length = a.hairL || 'Short', texture = a.hairT || 'Straight', body = a.body || 'Average', detail = a.look || '';
  const cloth = CLOTHES[(a.id * 3 + 1) % CLOTHES.length], sw = SHOULDER[body] || 66, fw = a.gender === 'Male' ? 36 : 33;
  const skinD = shade(skin, .86), hairD = shade(hairC, .72), lip = (a.skin === 'Tan' || a.skin === 'Deep') ? '#8F3A4A' : '#B85B70';
  const P = [];
  if ((length === 'Long' || length === 'Medium') && texture !== 'Curly') {
    const bottom = length === 'Long' ? 212 : 160, side = length === 'Long' ? 50 : 58;
    const head = `M${100 - fw - 8} 104 C${100 - fw - 14} 44 ${100 - 24} 30 100 30 C${100 + 24} 30 ${100 + fw + 14} 44 ${100 + fw + 8} 104 L${100 + side + 2} ${bottom}`;
    const path = texture === 'Wavy' ? head + scallop(100 - side - 2, 100 + side + 2, bottom, 6, 8) + ' Z' : head + ` Q100 ${bottom + 10} ${100 - side - 2} ${bottom} Z`;
    P.push(`<path d="${path}" fill="${hairC}"/>`);
  }
  if (texture === 'Curly' && length !== 'Shaved') {
    const ys = [88, 110].concat(length === 'Long' ? [134, 158] : length === 'Medium' ? [134] : []);
    for (const y of ys) { P.push(`<circle cx="${100 - fw - 10}" cy="${y}" r="13" fill="${hairC}"/>`); P.push(`<circle cx="${100 + fw + 10}" cy="${y}" r="13" fill="${hairC}"/>`); }
  }
  P.push(`<path d="M${100 - sw} 240 C${100 - sw} 206 ${100 - sw + 8} 190 66 182 L134 182 C${100 + sw - 8} 190 ${100 + sw} 206 ${100 + sw} 240 Z" fill="${cloth}"/>`);
  P.push(`<rect x="87" y="136" width="26" height="52" rx="10" fill="${skinD}"/>`);
  P.push(`<path d="M80 184 Q100 214 120 184 Z" fill="${skinD}"/>`);
  P.push(`<path d="M86 184 Q100 206 114 184" fill="none" stroke="${shade(cloth, .7)}" stroke-width="1.2" opacity=".5"/>`);
  P.push(`<circle cx="${100 - fw}" cy="106" r="6" fill="${skinD}"/><circle cx="${100 + fw}" cy="106" r="6" fill="${skinD}"/>`);
  P.push(`<ellipse cx="100" cy="100" rx="${fw}" ry="42" fill="${skin}"/>`);
  if (a.pierce) P.push(`<circle cx="${100 - fw}" cy="115" r="2.6" fill="#D4B06A"/><circle cx="${100 + fw}" cy="115" r="2.6" fill="#D4B06A"/>`);
  if (detail.includes('เครา') || detail.includes('หนวด'))
    P.push(`<path d="M${100 - fw + 1} 108 C${100 - fw + 2} 140 86 148 100 148 C114 148 ${100 + fw - 2} 140 ${100 + fw - 1} 108 C${100 + fw - 8} 124 116 124 100 124 C84 124 ${100 - fw + 8} 124 ${100 - fw + 1} 108 Z" fill="${hairD}" opacity=".88"/>`);
  if (length === 'Shaved')
    P.push(`<path d="M${100 - fw + 1} 92 C${100 - fw} 56 80 56 100 56 C120 56 ${100 + fw} 56 ${100 + fw - 1} 92 C${100 + fw - 6} 76 116 70 100 70 C84 70 ${100 - fw + 6} 76 ${100 - fw + 1} 92 Z" fill="${hairD}" opacity=".35"/>`);
  else {
    const top = texture !== 'Curly' ? 34 : 30;
    P.push(`<path d="M${100 - fw - 4} 102 C${100 - fw - 8} 52 ${100 - 22} ${top} 100 ${top} C${100 + 22} ${top} ${100 + fw + 8} 52 ${100 + fw + 4} 102 C${100 + fw - 1} 84 ${100 + fw - 8} 70 ${100 + 12} 64 C${100 - 8} 74 ${100 - fw + 8} 74 ${100 - fw + 2} 98 C${100 - fw - 1} 94 ${100 - fw - 3} 98 ${100 - fw - 4} 102 Z" fill="${hairC}"/>`);
    if (texture === 'Curly') for (const [x, y] of [[66, 62], [80, 46], [100, 40], [120, 46], [134, 62]]) P.push(`<circle cx="${x}" cy="${y}" r="12" fill="${hairC}"/>`);
    if (length === 'Short' && texture === 'Wavy') P.push(`<path d="M64 76 Q80 56 100 60" stroke="${shade(hairC, 1.35)}" stroke-width="2" fill="none" opacity=".5"/>`);
  }
  const brow = !['Blonde', 'Gray', 'Dyed'].includes(a.hairC) ? hairD : shade(hairC, .6);
  P.push(`<path d="M80 94 Q87 90 94 93" stroke="${brow}" stroke-width="2.2" fill="none" stroke-linecap="round"/><path d="M106 93 Q113 90 120 94" stroke="${brow}" stroke-width="2.2" fill="none" stroke-linecap="round"/>`);
  for (const cx of [87, 113])
    P.push(`<ellipse cx="${cx}" cy="104" rx="5" ry="3" fill="#FFFFFF" opacity=".95"/><circle cx="${cx}" cy="104" r="2.5" fill="${eyeC}"/><path d="M${cx - 5.5} 103 Q${cx} 99 ${cx + 5.5} 103" stroke="#2A1F22" stroke-width="1.5" fill="none" stroke-linecap="round"/>`);
  if (detail.includes('แว่น')) P.push('<g fill="none" stroke="#2A2326" stroke-width="1.8"><circle cx="87" cy="104" r="10"/><circle cx="113" cy="104" r="10"/><path d="M97 103 H103"/></g>');
  P.push(`<path d="M100 108 q-3.5 10 0 13" stroke="${skinD}" stroke-width="1.6" fill="none" stroke-linecap="round"/>`);
  P.push(`<path d="M91.5 129 Q100 124.5 108.5 129 Q100 138 91.5 129 Z" fill="${lip}"/>`);
  return `<svg class="avatar" viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMax slice" role="img" aria-label="${esc(a.name)}">${P.join('')}</svg>`;
}
const SPARK = (s = 12) => `<svg class="spark" width="${s}" height="${s}" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 0 C13 8 16 11 24 12 C16 13 13 16 12 24 C11 16 8 13 0 12 C8 11 11 8 12 0Z" fill="#B8955A"/></svg>`;
const BOW = `<svg class="bow" viewBox="0 0 120 90" aria-hidden="true"><path d="M60 52 C30 6 4 14 8 40 C12 66 44 62 60 52 Z" fill="#D8BF8C"/><path d="M60 52 C90 6 116 14 112 40 C108 66 76 62 60 52 Z" fill="#C7A468"/><path d="M60 52 C46 60 30 80 22 88 L40 84 L56 62 Z" fill="#B8955A"/><path d="M60 52 C74 60 90 80 98 88 L80 84 L64 62 Z" fill="#A98445"/><circle cx="60" cy="50" r="11" fill="#E6D2A3"/></svg>`;
const eyeIcon = (off, c) => `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="${c}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>${off ? '<path d="M3 3l18 18"/>' : ''}</svg>`;

