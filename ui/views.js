/* ====================== สถานะหน้าจอ + ตัวช่วยสร้างฟอร์ม ====================== */
const S = { page: 'home', dlg: null, tab: {}, match: null, rgMode: 'new', rgLoaded: null, pfLoaded: null, wkEdit: null, srch: null, confirmReset: false, confirmCancel: {} };
const F = {};   // ค่าในช่องกรอกทั้งหมด (key เดียว = ช่องเดียว)
const R = {};   // แถวที่เพิ่ม/ลบได้ (ตารางนัด, งวดจ่าย)
const fv = (k, d = '') => (F[k] === undefined ? d : F[k]);
function resetCastForm() {
  const t = TODAY();
  R.cs = [{ type: 'Shoot', date: addDays(t, 7), start: '09:00', end: '17:00' }];
  R.cp = [{ due: addDays(t, 14), amount: 25000 }, { due: addDays(t, 30), amount: 25000 }];
}
resetCastForm();
F['cast.fee'] = 50000; F['srch.date'] = addDays(TODAY(), 7); F['srch.start'] = '09:00'; F['srch.end'] = '17:00';

const fld = (label, html, cls = '') => `<div class="field ${cls}"><label>${label}</label>${html}</div>`;
const inp = (k, o = {}) => `<input type="${o.type || 'text'}" data-f="${k}" value="${esc(fv(k, o.def ?? ''))}" placeholder="${esc(o.ph || '')}" ${o.attr || ''}>`;
const opt = (v, l, cur) => `<option value="${esc(v)}" ${String(v) === String(cur) ? 'selected' : ''}>${esc(l)}</option>`;
const sel = (k, opts, o = {}) => {
  const cur = fv(k, o.def ?? (opts[0] ? opts[0][0] : ''));
  return `<select data-f="${k}" ${o.chg ? `data-chg="${o.chg}"` : ''}>${opts.map(([v, l]) => opt(v, l, cur)).join('')}</select>`;
};
const chk = (k, label, def = false) => `<label class="toggle"><input type="checkbox" data-f="${k}" ${fv(k, def) ? 'checked' : ''}> ${label}</label>`;
const ta = (k, o = {}) => `<textarea data-f="${k}" placeholder="${esc(o.ph || '')}" maxlength="${o.max || 600}" rows="${o.rows || 3}">${esc(fv(k, ''))}</textarea>`;
const objOpts = (o, blank) => (blank ? [['', blank]] : []).concat(Object.entries(o));
const picked = k => fv(k, []);
function pick(k, options) {
  const cur = picked(k);
  return `<div class="chips-row">${options.map(([v, l]) => `<button type="button" class="tg" data-act="tg" data-k="${k}" data-v="${esc(v)}" aria-pressed="${cur.includes(v)}">${esc(l)}</button>`).join('')}</div>`;
}
function skillPicker(k) {
  const cur = picked(k);
  return SKILL_TYPES.map(t => {
    const items = DB.skills.filter(s => s.type === t), n = items.filter(s => cur.includes(s.id)).length;
    return `<details class="skillgrp" data-d="${k}.${t}" ${fv('d.' + k + '.' + t, n > 0) ? 'open' : ''}><summary>${L.skillType[t]} <span class="cnt">${n ? `เลือกแล้ว ${n}` : `(${items.length})`}</span></summary>
      <div class="chips-row">${items.map(s => `<button type="button" class="tg" data-act="tg" data-k="${k}" data-v="${s.id}" aria-pressed="${cur.includes(s.id)}">${esc(s.name)}</button>`).join('')}</div></details>`;
  }).join('');
}
const pickedSkills = k => picked(k).map(Number);

/* ---------- ป้ายและชิป ---------- */
const badge = (c, t) => `<span class="badge b-${c}">${esc(t)}</span>`;
const roleBadge = s => badge({ Selected: 'wait', Confirmed: 'ok', Rejected_by_Actor: 'bad', Cancelled_by_Organizer: 'off' }[s], L.roleSt[s]);
const payBadge = (p) => isOverdue(p) ? badge('bad', 'เลยกำหนด') : badge({ Pending: 'wait', Paid: 'ok', Cancelled: 'off' }[p.status], L.paySt[p.status]);
const actorBadge = a => a.status === 'Active' ? badge('ok', 'พร้อมรับงาน') : badge('off', 'พักงาน');
const chips = (arr, soft) => (arr || []).map(x => `<span class="chip ${soft ? 'soft' : ''}">${esc(x)}</span>`).join('');
const sec = (title, sub, no) => `<div class="sec">${no ? `<span class="no">${no}</span>` : ''}<h2>${esc(title)}</h2>${sub ? `<p>${esc(sub)}</p>` : ''}</div>`;
const pgHead = (eye, title, desc) => `<div class="pg-head">${eye ? `<span class="eyebrow">${SPARK(12)}${esc(eye)}</span>` : ''}<h1>${esc(title)}</h1>${desc ? `<p>${esc(desc)}</p>` : ''}</div>`;
const alertBox = (k, t) => `<div class="alert ${k}">${t}</div>`;
const stat = (l, v, n, k = '') => `<div class="stat ${k}"><div class="l">${esc(l)}</div><div class="v">${v}</div>${n ? `<div class="n">${esc(n)}</div>` : ''}</div>`;
const tableHtml = (cols, rows) => rows.length ? `<div class="tw"><table><thead><tr>${cols.map(c => `<th class="${c.num ? 'num' : ''}">${esc(c.h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${cols.map(c => `<td class="${c.num ? 'num' : ''}">${c.f(r)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>` : `<div class="empty">ไม่มีข้อมูล</div>`;

/* ---------- การ์ดนักแสดง ---------- */
function tcard(a) {
  const age = ageOf(a.birth), sk = a.skills.slice(0, 2).map(skillName);
  return `<article class="tcard ${tileOf(a)} ${a.status !== 'Active' ? 'off' : ''}" data-act="view" data-id="${a.id}" tabindex="0" role="button" aria-label="ดูโปรไฟล์ ${esc(a.name)}">
    <div class="frame">${avatar(a)}${a.works.length ? `<div class="tag"><span class="badge b-works">ผลงาน ${a.works.length}</span></div>` : ''}</div>
    <div class="body"><div class="nm">${esc(a.name)}</div>
    <div class="meta">${L.gender[a.gender] || ''}${age != null ? ` · ${age} ปี` : ''}${a.h ? ` · ${a.h} ซม.` : ''}</div>${chips(sk, true)}</div></article>`;
}
function compCard(a) {
  const age = ageOf(a.birth);
  return `<div class="comp"><div class="tcard ${tileOf(a)} ${a.status !== 'Active' ? 'off' : ''}"><div class="frame">${avatar(a)}</div></div>
    <div class="info"><div class="nm">${esc(a.name)}</div>
    <div class="meta"><b>#${a.id}</b> · ${L.gender[a.gender] || ''}${age != null ? ` · ${age} ปี` : ''}${a.exp ? ` · ${L.exp[a.exp]}` : ''}${a.prov ? ` · ${esc(a.prov)}` : ''}</div>
    ${a.look ? `<div class="look">${esc(a.look)}</div>` : ''}
    <div style="margin-top:.4rem">${chips(a.skills.slice(0, 8).map(skillName))}${a.skills.length > 8 ? `<span class="chip">+${a.skills.length - 8}</span>` : ''}</div></div></div>`;
}
function vitals(a) {
  const v = (l, x, u) => x == null || x === '' ? '' : `<div><span>${l}</span><b>${esc(x)}</b><small>${u}</small></div>`;
  return `<div class="vitals">${v('ส่วนสูง', a.h, 'ซม.')}${v('น้ำหนัก', a.w, 'กก.')}${v('รอบอก', a.bust, 'ซม.')}${v('รอบเอว', a.waist, 'ซม.')}${v('รอบสะโพก', a.hip, 'ซม.')}${v('รองเท้า', a.shoe, 'EU')}${v('ไซซ์', a.size, '')}</div>`;
}
function looksText(a) {
  const p = [];
  if (a.body) p.push('รูปร่าง' + L.body[a.body]); if (a.skin) p.push(L.skin[a.skin]);
  if (a.hairC) p.push(`ผม${L.hairC[a.hairC]}${a.hairL ? ' ' + L.hairL[a.hairL] : ''}${a.hairT ? ' ' + L.hairT[a.hairT] : ''}`);
  if (a.eye) p.push('ตา' + L.eye[a.eye]); if (a.tattoo) p.push('มีรอยสัก'); if (a.pierce) p.push('เจาะหู/เจาะอื่นๆ'); if (a.travel) p.push('เดินทางต่างจังหวัดได้');
  return p.join(' · ');
}
function workHtml(w) {
  return `<div class="work"><div class="yr">${w.year}</div><div><h4>${esc(w.title)}</h4><div class="wm">${L.work[w.type]}${w.role ? ` · รับบท ${esc(w.role)}` : ''}</div>${w.desc ? `<p>${esc(w.desc)}</p>` : ''}${w.url ? `<a class="wlink" href="${esc(w.url)}" target="_blank" rel="noopener noreferrer">ดูผลงาน ↗</a>` : ''}</div></div>`;
}
function profileHtml(a) {
  const groups = SKILL_TYPES.map(t => ({ t, items: a.skills.map(i => DB.skills.find(s => s.id === i)).filter(s => s && s.type === t) })).filter(g => g.items.length);
  const age = ageOf(a.birth);
  return `<div class="comp"><div class="tcard ${tileOf(a)}"><div class="frame">${avatar(a)}</div></div>
    <div class="info"><div class="nm">${esc(a.name)}</div>
    <div class="meta"><b>#${a.id}</b> · ${L.gender[a.gender]}${age != null ? ` · ${age} ปี` : ''}${a.exp ? ` · ${L.exp[a.exp]}` : ''}${a.prov ? ` · ${esc(a.prov)}` : ''} &nbsp;${actorBadge(a)}</div>
    ${a.bio ? `<div class="bio">“${esc(a.bio)}”</div>` : ''}${vitals(a)}<div class="look">${esc(looksText(a))}</div>${a.look ? `<div class="look" style="color:var(--muted)">${esc(a.look)}</div>` : ''}</div></div>
    ${sec('ทักษะ', `${a.skills.length} อย่าง`)}
    ${groups.length ? groups.map(g => `<div class="skillgroup"><h5>${L.skillType[g.t]}</h5>${chips(g.items.map(s => s.name))}</div>`).join('') : '<div class="empty">ยังไม่ได้เลือกทักษะ</div>'}
    ${sec('ผลงาน', `${a.works.length} ชิ้น`)}
    ${a.works.length ? `<div class="works">${a.works.slice().sort((x, y) => y.year - x.year || y.id - x.id).map(workHtml).join('')}</div>` : '<div class="empty">ยังไม่มีผลงาน</div>'}`;
}

/* ---------- ตัวกรองรูปลักษณ์ (ใช้ร่วมกันสองหน้า) ---------- */
function traitPanel(p) {
  const tri = k => sel(`${p}.${k}`, [['', 'ไม่กรอง'], ['y', 'ต้องมี'], ['n', 'ต้องไม่มี']]);
  const grp = (k, label, labels) => `<div class="field"><label>${label}</label>${pick(`${p}.${k}`, Object.entries(labels))}</div>`;
  return `<details class="fold" data-d="${p}.traits" ${fv('d.' + p + '.traits', false) ? 'open' : ''}><summary>ตัวกรองรูปลักษณ์ <span class="hint">อายุ ส่วนสูง รูปร่าง สีผม สีผิว สีตา ฯลฯ</span></summary><div class="in">
    <div class="grid g4">${fld('อายุตั้งแต่ (ปี)', inp(p + '.ageMin', { type: 'number', ph: '18', attr: 'min="18" max="90" inputmode="numeric"' }))}${fld('ถึง (ปี)', inp(p + '.ageMax', { type: 'number', ph: '70', attr: 'min="18" max="90" inputmode="numeric"' }))}
    ${fld('สูงตั้งแต่ (ซม.)', inp(p + '.hMin', { type: 'number', ph: '140', attr: 'inputmode="numeric"' }))}${fld('ถึง (ซม.)', inp(p + '.hMax', { type: 'number', ph: '200', attr: 'inputmode="numeric"' }))}</div>
    <div class="grid" style="margin-top:.9rem">${grp('body', 'รูปร่าง', L.body)}${grp('skin', 'สีผิว', L.skin)}${grp('hairC', 'สีผม', L.hairC)}${grp('hairL', 'ความยาวผม', L.hairL)}${grp('hairT', 'ลักษณะผม', L.hairT)}${grp('eye', 'สีตา', L.eye)}${grp('exp', 'ระดับประสบการณ์', L.exp)}</div>
    <div class="grid g4" style="margin-top:.9rem">${fld('จังหวัด', sel(p + '.prov', [['', 'ทั้งหมด'], ...PROVINCES.map(x => [x, x])]))}${fld('รอยสัก', tri('tattoo'))}${fld('เจาะหู/เจาะอื่นๆ', tri('pierce'))}${fld('เดินทางต่างจังหวัด', tri('travel'))}</div>
  </div></details>`;
}
function readTraits(p) {
  const t = {}, n = k => { const v = F[`${p}.${k}`]; return v === '' || v == null ? null : Number(v); };
  [['ageMin', 'ageMin'], ['ageMax', 'ageMax'], ['hMin', 'hMin'], ['hMax', 'hMax']].forEach(([k, o]) => { if (n(k) != null && !isNaN(n(k))) t[o] = n(k); });
  for (const k of Object.keys(TRAIT_LISTS)) { const v = F[`${p}.${k}`]; if (v && v.length) t[k] = v; }
  if (F[`${p}.prov`]) t.prov = F[`${p}.prov`];
  for (const k of ['tattoo', 'pierce', 'travel']) { const v = F[`${p}.${k}`]; if (v === 'y') t[k] = true; else if (v === 'n') t[k] = false; }
  return t;
}

/* ---------- แถบเลือก "คุณคือใคร" ของฝั่งนักแสดง ---------- */
function meActor() { return actorOf(DB.me) || DB.actors[0]; }
function actorBar() {
  const me = meActor();
  return `<div class="card" style="display:grid;grid-template-columns:minmax(0,1fr) auto;gap:1rem;align-items:end"><div class="field"><label>คุณคือใคร (เดโมนี้ไม่มีระบบล็อกอิน เลือกชื่อตัวเองจากรายการ)</label>
    <select data-chg="me_change">${DB.actors.slice().sort(byName).map(a => opt(a.id, `${a.name} (#${a.id})${a.pub ? '' : ' · ซ่อนอยู่'}`, me.id)).join('')}</select></div>
    <button class="btn sm" data-act="nav" data-p="actor_register" data-mode="new">+ สมัครเป็นนักแสดงใหม่</button></div>`;
}

/* ====================== หน้าต่างๆ ====================== */
function pgHome() {
  const pubA = DB.actors.filter(a => a.pub && a.status === 'Active');
  const feat = pubA.slice().sort((a, b) => b.skills.length - a.skills.length || a.id - b.id).slice(0, 10);
  const fem = feat.filter(a => a.gender === 'Female'), male = feat.filter(a => a.gender === 'Male');
  let trio = [fem[0], male[0], fem[1]].filter(Boolean); if (trio.length < 3) trio = feat.slice(0, 3);
  const pop = DB.skills.map(s => ({ n: s.name, c: DB.actors.filter(a => a.skills.includes(s.id)).length })).filter(x => x.c > 0).sort((a, b) => b.c - a.c || a.n.localeCompare(b.n, 'th')).slice(0, 16);
  return `
  <div class="note"><b>ข้อมูลในหน้านี้อยู่ในฐานข้อมูล MySQL ร่วมกันทั้งกลุ่ม</b> ใครกดหรือกรอกอะไร ทุกคนเห็นเหมือนกัน ข้อมูลทุกคนเป็นข้อมูลสมมติเพื่อสาธิต ดูคำสั่ง SQL ที่เพิ่งรันได้ท้ายหน้า</div>
  <div class="hero"><div><span class="eyebrow">${SPARK(12)}CASTING &amp; MODELING AGENCY</span>
    <h1>Find the <em>face</em><br>for every story.</h1>
    <p class="th">ที่เดียวจบ ทั้งหานักแสดง นายแบบ นางแบบ ที่ <b>ตรงทั้งทักษะและรูปลักษณ์</b> ตรวจคิวงานไม่ให้ชน และจ่ายค่าตัวเป็นงวดอย่างโปร่งใส สำหรับคนอยากเข้าวงการและทีมที่กำลังหาคนมาเล่นบท</p>
    <div class="btns"><button class="btn primary" data-act="nav" data-p="actor_register" data-mode="new">ฉันเป็นนักแสดง / โมเดล สมัครเลย</button><button class="btn" data-act="nav" data-p="org_casting">ฉันเป็นผู้จัดงาน หานักแสดง</button></div></div>
    <div class="arches">${trio.map((a, i) => `<div class="arch a${i + 1}">${avatar(a)}</div>`).join('')}
      <div class="float-badge b1">${SPARK(14)}${DB.skills.length} ทักษะให้เลือก</div><div class="float-badge b2">${SPARK(14)}จับคู่อัตโนมัติ คิวไม่ชน</div></div></div>
  <div class="strip"><div><b>${pubA.length}</b><span>นักแสดงและโมเดลพร้อมรับงาน</span></div><div><b>${DB.skills.length}</b><span>ทักษะ ภาษา และสายงานโมเดลลิ่ง</span></div>
    <div><b>${DB.projects.length}</b><span>โปรเจกต์ในระบบ</span></div><div><b>${DB.roles.length}</b><span>บทที่จับคู่นักแสดงแล้ว</span></div></div>
  ${sec('ทำไมต้องที่นี่', 'สามอย่างที่ทำให้หาคนเร็วกว่าทักแชตทีละคน')}
  <div class="tiles">
    <div class="tile rose"><span class="num">01</span><h3>หาให้ตรงถึงรูปลักษณ์</h3><p>กรองพร้อมกันได้ทั้งอายุ ส่วนสูง รูปร่าง สีผิว สีผม สีตา และทักษะอีก ${DB.skills.length} อย่าง ตั้งแต่เดินแบบรันเวย์ยันภาษามือไทย</p><div class="ex">${chips(['ผมบลอนด์', 'สูง 175+', 'เดินแบบ', 'ภาษาอังกฤษ'], true)}</div></div>
    <div class="tile powder"><span class="num">02</span><h3>คิวไม่ชน ไม่ต้องโทรเช็ก</h3><p>ทุกครั้งที่เลือกนักแสดง ระบบตรวจตารางนัดให้เอง คนที่ติดงานช่วงเวลาเดียวกันจะไม่โผล่ในรายชื่อ และบอกเหตุผลได้ว่าถูกตัดเพราะอะไร</p><div class="ex">${chips(['ตรวจคิวอัตโนมัติ', 'บอกเหตุผล'], true)}</div></div>
    <div class="tile champ"><span class="num">03</span><h3>จ่ายเป็นงวด ชัดเจน</h3><p>แบ่งค่าตัวเป็นงวด มีสถานะรอจ่าย/จ่ายแล้ว เตือนงวดที่เลยกำหนด และกันการกดจ่ายซ้ำ ทั้งฝั่งนักแสดงและผู้จัดงานเห็นตรงกัน</p><div class="ex">${chips(['แบ่งงวด', 'กันจ่ายซ้ำ'], true)}</div></div></div>
  ${sec('นักแสดงและโมเดลแนะนำ', 'เลื่อนดูได้ทางขวา กดที่การ์ดเพื่อดูโปรไฟล์และผลงาน')}
  <div class="rail">${feat.map(tcard).join('')}</div>
  <div class="btns" style="margin-top:0"><button class="btn" data-act="nav" data-p="talent">ดูนักแสดงทั้งหมดในแคตตาล็อก →</button></div>
  ${sec('ทักษะที่คนมีมากที่สุด')}<div>${pop.map(x => `<span class="chip">${esc(x.n)} · ${x.c}</span>`).join('')}</div>
  ${sec('เริ่มใช้ยังไง')}
  <div class="accs">
    <details class="acc" open><summary>ฉันเป็นนักแสดง / โมเดล ต้องทำอะไรบ้าง<span class="plus"></span></summary><div class="ans">1) ไปที่ <b>นักแสดง › สมัคร / แก้โปรไฟล์</b> กรอกรูปร่าง สีผม ทักษะ ให้ตรงตามจริง 2) เปิด <b>โปรไฟล์และผลงานของฉัน</b> ใส่ชื่อ แท็ก ผลงาน แล้วกด <b>เผยแพร่</b> ถ้ายังไม่ใส่อะไร ผู้จัดงานจะไม่เห็นคุณ 3) เมื่อมีผู้จัดงานเลือกคุณ จะเห็นที่ <b>งานของฉัน</b> กด <b>ยอมรับ</b> หรือ <b>ปฏิเสธ</b> 4) ดูตารางนัดและสถานะการจ่ายเงินได้ในเมนูฝั่งนักแสดง</div></details>
    <details class="acc"><summary>ฉันเป็นผู้จัดงาน หานักแสดงยังไง<span class="plus"></span></summary><div class="ans">สร้าง <b>โปรเจกต์</b> แล้วไปที่ <b>สร้างบท + จับคู่นักแสดง</b> กรอกบท ทักษะที่ต้องการ ตารางนัด งวดจ่าย และตัวกรองรูปลักษณ์ ระบบจะคัดเฉพาะคนที่ <b>ทักษะครบ ไม่คิวชน และพร้อมรับงาน</b> แล้วคุณเลือกได้ 1 คน</div></details>
    <details class="acc"><summary>เดิมหานักแสดงทางโซเชียลมีปัญหาอะไร<span class="plus"></span></summary><div class="ans">ข้อมูลกระจัดกระจายค้นหาแบบเจาะจงไม่ได้, คิวงานทับซ้อนเพราะไม่มีระบบตรวจ, และจ่ายค่าตัวซ้ำหรือตกหล่น เว็บนี้เก็บทุกอย่างไว้ในฐานข้อมูลเดียวแล้วให้ระบบตรวจกฎแทนคน</div></details>
    <details class="acc"><summary>ข้อมูลเก็บที่ไหน ใช้ล็อกอินไหม<span class="plus"></span></summary><div class="ans">ข้อมูลทั้งหมดเก็บในฐานข้อมูล <b>MySQL</b> ทุกปุ่มที่บันทึกจะเรียก Python (queries.py) ให้รัน SQL และตรวจกฎ (ทักษะต้องครบ คิวห้ามชน ยอดงวดต้องเท่าค่าตัว กดจ่ายซ้ำไม่ได้ ไม่เผยแพร่ = คนอื่นไม่เห็น) เวอร์ชันนี้ <b>ยังไม่มีระบบล็อกอิน</b> (ER ไม่มีตารางผู้ใช้) ฝั่งนักแสดงจึงให้เลือกชื่อตัวเองจากรายการ</div></details></div>
  <div class="gift">${BOW}<div class="in"><h2>พร้อมขึ้นเวทีหรือยัง</h2><p>สมัครเป็นนักแสดงใช้เวลาไม่ถึงห้านาที หรือเริ่มสร้างโปรเจกต์แล้วให้ระบบหาคนที่ใช่ให้คุณ</p></div>
    <div class="btns"><button class="btn gold" data-act="nav" data-p="actor_register" data-mode="new">สมัครเป็นนักแสดง</button><button class="btn" data-act="nav" data-p="org_projects">สร้างโปรเจกต์</button></div></div>`;
}

function filterTalent() {
  const text = (fv('cat.text') || '').trim().toLowerCase(), g = fv('cat.gender'), onlyAct = fv('cat.active', true);
  return DB.actors.filter(a => a.pub && (!onlyAct || a.status === 'Active') && (!g || a.gender === g) && (!text || a.name.toLowerCase().includes(text) || (a.look || '').toLowerCase().includes(text) || a.skills.some(i => skillName(i).toLowerCase().includes(text)))).sort(byName);
}
function pgTalent() {
  const rows = filterTalent();
  return pgHead('แคตตาล็อก', 'นักแสดงและโมเดล', 'กดที่การ์ดเพื่อดูโปรไฟล์ ทักษะ และผลงาน แสดงเฉพาะคนที่เปิดโปรไฟล์ให้คนอื่นเห็น') +
    `<div class="card"><div class="grid g3">${fld('ค้นหา ชื่อ / ทักษะ / รูปลักษณ์', inp('cat.text', { ph: 'เช่น เดินแบบ, ผมสั้น, ภาษาอังกฤษ' }).replace('<input', '<input data-live="1"'))}
    ${fld('เพศ', sel('cat.gender', objOpts(L.gender, 'ทุกเพศ')).replace('<select', '<select data-live="1"'))}
    <div class="field"><label>&nbsp;</label>${chk('cat.active', 'เฉพาะที่พร้อมรับงาน', true).replace('<input', '<input data-live="1"')}</div></div></div>
    <p class="hint" style="margin:1rem 0 .6rem">พบ ${rows.length} คน</p>
    ${rows.length ? `<div class="tgrid">${rows.map(tcard).join('')}</div>` : '<div class="empty">ไม่พบนักแสดงตามเงื่อนไข</div>'}`;
}

function pgSearch() {
  const res = S.srch;
  return pgHead('สำหรับผู้จัดงาน', 'ค้นหานักแสดง', 'ตัวกรองทุกข้อทำงานพร้อมกัน หาคนที่ตรงเงื่อนไขของงานจริงๆ ทั้งทักษะ รูปลักษณ์ และความว่าง') +
    traitPanel('srch') +
    `<div class="form-card" style="margin-top:.9rem"><div class="grid g2">${fld('เพศ', sel('srch.gender', objOpts(L.gender, 'ทุกเพศ')))}${fld('คำในรายละเอียดรูปลักษณ์ / ชื่อ', inp('srch.text', { ph: 'เช่น ผมสั้น, สูง 17' }))}</div>
    <div class="lab" style="margin:1rem 0 .2rem">ทักษะ / ภาษา <span class="hint">(ต้องมีครบทุกข้อที่เลือก)</span></div>${skillPicker('srch.sk')}
    <div style="margin-top:.8rem">${chk('srch.avail', 'ต้องว่างในช่วงเวลา')}</div>
    <div class="grid g3" style="margin-top:.6rem">${fld('วันที่', inp('srch.date', { type: 'date' }))}${fld('เริ่ม', inp('srch.start', { type: 'time' }))}${fld('เลิก', inp('srch.end', { type: 'time' }))}</div>
    <div style="margin-top:.8rem">${chk('srch.inactive', 'รวมนักแสดงที่พักงานด้วย')}</div>
    <div class="btns"><button class="btn primary" data-act="do_search">ค้นหา</button><button class="btn" data-act="clear_search">ล้างตัวกรอง</button></div></div>` +
    (res ? `${alertBox(res.length ? 'ok' : 'warn', `พบ ${res.length} คน`)}<div class="grid g2">${res.map(id => actorOf(id)).filter(Boolean).map(a => `<div class="card">${compCard(a)}<div class="btns">${actorBadge(a)}<button class="btn sm" data-act="view" data-id="${a.id}">ดูโปรไฟล์และผลงาน</button></div></div>`).join('')}</div>` : '');
}

function pgProjects() {
  const pr = DB.projects.slice().sort((a, b) => b.id - a.id);
  return pgHead('สำหรับผู้จัดงาน', 'โปรเจกต์', 'สร้างโปรเจกต์ก่อน แล้วค่อยเพิ่มบทและเลือกนักแสดง') +
    `<div class="form-card"><div class="grid g3">${fld('ชื่อโปรเจกต์', inp('pj.name', { ph: 'เช่น ซีรีส์ รักในเงา' }))}${fld('ชื่อลูกค้า / สตูดิโอ', inp('pj.client', { ph: 'เช่น ABC Studio' }))}${fld('ประเภท', sel('pj.type', objOpts(L.projType)))}</div>
    <div class="btns"><button class="btn primary" data-act="proj_create">สร้างโปรเจกต์</button></div></div>` +
    sec('โปรเจกต์ทั้งหมด', `${pr.length} รายการ`) +
    `<div class="cardlist">${pr.map(p => `<div class="card"><div class="rhead"><div><h3>${esc(p.name)}</h3><div class="sub">#${p.id} · ${L.projType[p.type]} · ลูกค้า ${esc(p.client)} · ${DB.roles.filter(r => r.project === p.id).length} บท</div></div>
      <div class="field" style="min-width:12rem"><label>สถานะ</label><select data-chg="proj_status" data-id="${p.id}">${objOpts(L.projSt).map(([v, l]) => opt(v, l, p.status)).join('')}</select></div></div></div>`).join('')}</div>`;
}

function buildSql(skills, slots, gender, traits) {
  let s = "SELECT a.* FROM ACTOR a\nWHERE a.actor_status = 'Active' AND a.is_public = 1";
  const tl = Object.keys(traitsToText(traits)); if (tl.length) s += '\n  AND <ตัวกรองรูปลักษณ์: ' + tl.join(', ') + '>';
  if (gender) s += `\n  AND a.gender = '${gender}'`;
  if (skills.length) s += `\n  AND (SELECT COUNT(DISTINCT ak.skill_id) FROM ACTOR_SKILL ak\n       WHERE ak.actor_id = a.actor_id AND ak.skill_id IN (${skills.join(', ')})) = ${skills.length}`;
  for (const x of slots) s += `\n  AND NOT EXISTS (SELECT 1 FROM ROLE r JOIN SCHEDULE s ON s.role_id = r.role_id\n       WHERE r.actor_id = a.actor_id AND r.role_status IN ('Selected','Confirmed')\n         AND s.event_date = '${x.date}' AND s.start_time < '${x.end}' AND s.end_time > '${x.start}')`;
  return s + '\nORDER BY a.full_name;';
}
const traitsToText = t => Object.fromEntries(Object.entries(t).filter(([, v]) => v != null && !(Array.isArray(v) && !v.length)));
const rowDel = (name, i) => `<button type="button" class="xbtn" data-act="row_del" data-n="${name}" data-i="${i}" aria-label="ลบแถว">×</button>`;
const rin = (name, i, k, type, extra = '') => `<input type="${type}" data-r="${name}" data-i="${i}" data-k="${k}" value="${esc(R[name][i][k])}" ${extra}>`;

function sumHtml() {
  const fee = Number(fv('cast.fee', 0)) || 0, sum = R.cp.reduce((s, p) => s + (Number(p.amount) || 0), 0);
  return Math.abs(sum - fee) < 0.005 ? alertBox('ok', `ยอดรวมงวด ${money(sum)} เท่ากับค่าตัว ${money(fee)}`) : alertBox('warn', `ยอดรวมงวด ${money(sum)} ยังไม่เท่ากับค่าตัว ${money(fee)}`);
}
function pgCasting() {
  const projects = DB.projects.filter(p => ['Open', 'In_Progress'].includes(p.status));
  if (!projects.length) return pgHead('สำหรับผู้จัดงาน', 'สร้างบท + จับคู่นักแสดง', '') + alertBox('warn', 'ยังไม่มีโปรเจกต์ที่เปิดอยู่ ไปสร้างที่หน้า “โปรเจกต์” ก่อน');
  const m = S.match;
  let out = pgHead('สำหรับผู้จัดงาน', 'สร้างบท + จับคู่นักแสดง', 'กรอกรายละเอียดบท ระบบคัดนักแสดงที่ทักษะครบและคิวไม่ชน แล้วคุณเลือกได้ 1 คน') +
    `<div class="form-card">${fld('โปรเจกต์', sel('cast.project', projects.map(p => [p.id, `#${p.id} ${p.name} (ลูกค้า: ${p.client})`])))}</div>` +
    sec('รายละเอียดบท', '', 1) +
    `<div class="form-card"><div class="grid g2">${fld('ชื่อบท', inp('cast.role', { ph: 'เช่น นางเอก, พรีเซนเตอร์' }))}${fld('ค่าตัวที่ตกลง (บาท)', inp('cast.fee', { type: 'number', attr: 'min="0" step="1000" inputmode="decimal"' }))}</div>
    <div class="lab" style="margin:1rem 0 .2rem">ทักษะที่บทนี้ต้องการ <span class="hint">(ต้องมีครบทุกข้อที่เลือก · ไม่เลือกเลย = ไม่ระบุทักษะ เช่น ตัวประกอบ)</span></div>${skillPicker('cast.sk')}
    <div style="margin-top:1rem;max-width:24rem">${fld('ตัวกรองเพิ่มเติม: เพศ (ไม่บังคับ)', sel('cast.gender', objOpts(L.gender, 'ไม่กรอง')))}</div></div>
    <div style="margin-top:.9rem">${traitPanel('ct')}</div>` +
    sec('ตารางนัดหมายของบทนี้', 'บทหนึ่งมีนัดกี่ช่วงก็ได้ หรือไม่มีเลยก็ได้', 2) +
    `<div class="form-card">${R.cs.map((s, i) => `<div class="rowline"><div class="field"><label>ประเภท</label><select data-r="cs" data-i="${i}" data-k="type">${objOpts(L.event).map(([v, l]) => opt(v, l, s.type)).join('')}</select></div>
      <div class="field"><label>วันที่</label>${rin('cs', i, 'date', 'date')}</div><div class="field"><label>เริ่ม</label>${rin('cs', i, 'start', 'time')}</div><div class="field"><label>เลิก</label>${rin('cs', i, 'end', 'time')}</div>${rowDel('cs', i)}</div>`).join('')}
      <button class="btn sm" data-act="row_add" data-n="cs">+ เพิ่มนัด</button></div>` +
    sec('งวดจ่ายเงิน', 'ยอดรวมทุกงวดต้องเท่ากับค่าตัว', 3) +
    `<div class="form-card">${R.cp.map((p, i) => `<div class="rowline pay"><div class="field"><label>ครบกำหนดจ่าย</label>${rin('cp', i, 'due', 'date')}</div><div class="field"><label>จำนวนเงิน (บาท)</label>${rin('cp', i, 'amount', 'number', 'min="0" step="1000" inputmode="decimal"')}</div>${rowDel('cp', i)}</div>`).join('')}
      <button class="btn sm" data-act="row_add" data-n="cp">+ เพิ่มงวด</button>
      <div id="sumchk">${sumHtml()}</div></div>` +
    sec('ค้นหานักแสดงที่เหมาะสม', '', 4) + `<div class="btns" style="margin-top:0"><button class="btn primary" data-act="cast_find">ค้นหานักแสดงที่เหมาะสม</button></div>`;
  if (m) {
    const tab = S.tab.cast || 'ok';
    out += `<hr style="border:0;border-top:1px solid var(--line);margin:2rem 0">` + sec(`ผลค้นหาสำหรับบท ${m.roleName}`, `โปรเจกต์ #${m.project}`) +
      `<div class="note"><b>ทักษะที่ต้องมี</b> ${esc(m.skills.map(skillName).join(', ') || 'ไม่ระบุ')}<br><b>ช่วงเวลา</b> ${esc(m.slots.map(s => `${L.event[s.type]} ${s.date} ${s.start}-${s.end}`).join(' | ') || 'ไม่มีนัด')}</div>
      <details class="fold"><summary>ดูเงื่อนไขที่ใช้จับคู่ (SQL)</summary><div class="in"><pre style="overflow-x:auto;font-size:.8rem;margin:0;white-space:pre">${esc(m.sql)}</pre></div></details>
      <div class="tabs" role="tablist"><button role="tab" aria-selected="${tab === 'ok'}" data-act="tab" data-k="cast" data-v="ok">ผ่านเกณฑ์ (${m.eligible.length})</button><button role="tab" aria-selected="${tab === 'no'}" data-act="tab" data-k="cast" data-v="no">ถูกตัดออก (${m.excluded.length})</button></div>`;
    if (tab === 'ok') {
      out += m.eligible.length ? `<div class="cardlist">${m.eligible.map(id => actorOf(id)).filter(Boolean).map(a => `<div class="card" style="display:grid;grid-template-columns:minmax(0,1fr) auto;gap:1rem;align-items:center">${compCard(a)}<button class="btn primary" data-act="cast_pick" data-id="${a.id}">เลือกคนนี้</button></div>`).join('')}</div>`
        : alertBox('warn', 'ไม่มีนักแสดงที่ผ่านทุกเงื่อนไข ลองลดทักษะที่ต้องการ หรือเปลี่ยนช่วงเวลา (ดูเหตุผลที่แท็บถัดไป)');
    } else out += tableHtml([{ h: 'รหัส', f: r => `<span class="idc">#${r.id}</span>` }, { h: 'ชื่อ', f: r => esc(r.name) }, { h: 'เหตุผลที่ถูกตัดออก', f: r => r.reasons.map(esc).join('<br>') }], m.excluded);
    out += `<div class="btns"><button class="btn" data-act="cast_clear">ล้างผลการค้นหา</button></div>`;
  }
  return out;
}

function roleDetail(r) {
  return `<details class="fold"><summary>รายละเอียด</summary><div class="in"><b>ทักษะที่ต้องการ</b><div>${r.skills.length ? chips(r.skills.map(skillName)) : 'ไม่ระบุ'}</div>
    <div style="margin-top:.8rem"><b>ตารางนัด</b></div>${tableHtml([{ h: 'ประเภท', f: s => L.event[s.type] }, { h: 'วันที่', f: s => thDate(s.date) }, { h: 'เริ่ม', f: s => s.start }, { h: 'เลิก', f: s => s.end }], r.sched.slice().sort((a, b) => a.date.localeCompare(b.date) || a.start.localeCompare(b.start)))}
    <div><b>งวดจ่าย</b></div>${tableHtml([{ h: 'ครบกำหนด', f: p => thDate(p.due) }, { h: 'จำนวนเงิน (บาท)', num: 1, f: p => money(p.amount) }, { h: 'สถานะ', f: p => payBadge(p) }], r.pay.slice().sort((a, b) => a.due.localeCompare(b.due)))}</div></details>`;
}
const roleHead = (r, sub) => `<div class="rhead"><div><h3>${esc(r.name)}</h3><div class="sub">${esc(sub)}</div><div class="rstate">${roleBadge(r.status)}</div></div><div class="fee"><span>ค่าตัว</span><b>฿${money(r.fee)}</b></div></div>`;

function pgRoles() {
  const pid = Number(fv('rl.proj', 0)) || 0;
  const roles = DB.roles.filter(r => !pid || r.project === pid).sort((a, b) => b.id - a.id);
  return pgHead('สำหรับผู้จัดงาน', 'จัดการบท / ยกเลิกการจ้าง', 'ดูทุกบทพร้อมนักแสดงที่ถูกเลือก และยกเลิกการจ้างได้ งวดที่ยังไม่จ่ายจะถูกยกเลิกให้ด้วย') +
    `<div class="card" style="max-width:30rem">${fld('กรองตามโปรเจกต์', sel('rl.proj', [[0, 'ทุกโปรเจกต์'], ...DB.projects.map(p => [p.id, `#${p.id} ${p.name}`])], { chg: 'rerender' }))}</div><div style="height:1rem"></div>` +
    (roles.length ? `<div class="cardlist">${roles.map(r => {
      const a = actorOf(r.actor), can = BUSY.includes(r.status), sure = !!S.confirmCancel[r.id];
      return `<div class="card">${roleHead(r, `โปรเจกต์ ${projOf(r.project).name} · นักแสดง ${a.name} (#${a.id})`)}${roleDetail(r)}
        ${can ? `<div class="btns"><label class="toggle"><input type="checkbox" data-act="sure" data-id="${r.id}" ${sure ? 'checked' : ''}> ยืนยันว่าต้องการยกเลิกการจ้างบทนี้</label><button class="btn danger sm" data-act="role_cancel" data-id="${r.id}" ${sure ? '' : 'disabled'}>ยกเลิกการจ้าง</button></div>` : ''}</div>`;
    }).join('')}</div>` : alertBox('info', 'ยังไม่มีบทในโปรเจกต์นี้'));
}

function pgOrgPay() {
  const st = fv('op.st', ''), od = fv('op.od', false), pid = Number(fv('op.proj', 0)) || 0;
  const rows = allPayments().filter(p => (!st || p.status === st) && (!od || isOverdue(p)) && (!pid || p.role.project === pid)).sort((a, b) => a.due.localeCompare(b.due));
  const all = allPayments(), ov = all.filter(isOverdue);
  return pgHead('สำหรับผู้จัดงาน', 'งวดจ่ายเงิน', 'บันทึกว่าจ่ายแล้วได้เฉพาะบทที่นักแสดงยืนยัน และกดซ้ำไม่ได้') +
    `<div class="stats">${stat('รอจ่าย', money(all.filter(p => p.status === 'Pending').reduce((s, p) => s + p.amount, 0)), 'บาท')}${stat('จ่ายแล้ว', money(all.filter(p => p.status === 'Paid').reduce((s, p) => s + p.amount, 0)), 'บาท', 'ok')}${stat('งวดเลยกำหนด', ov.length, ov.length ? `รวม ${money(ov.reduce((s, p) => s + p.amount, 0))} บาท` : 'ไม่มีงวดค้าง', ov.length ? 'bad' : 'ok')}</div>
    <div class="card"><div class="grid g3">${fld('สถานะงวด', sel('op.st', objOpts(L.paySt, 'ทุกสถานะ'), { chg: 'rerender' }))}${fld('โปรเจกต์', sel('op.proj', [[0, 'ทุกโปรเจกต์'], ...DB.projects.map(p => [p.id, `#${p.id} ${p.name}`])], { chg: 'rerender' }))}<div class="field"><label>&nbsp;</label>${chk('op.od', 'เฉพาะที่เลยกำหนด').replace('<input', '<input data-chg="rerender"')}</div></div></div><div style="height:1rem"></div>` +
    tableHtml([{ h: 'โปรเจกต์ / บท', f: p => `<b>${esc(p.project.name)}</b><br><span class="hint">${esc(p.role.name)}</span>` }, { h: 'นักแสดง', f: p => esc(p.actor.name) }, { h: 'บท', f: p => roleBadge(p.role.status) },
      { h: 'ครบกำหนด', f: p => thDate(p.due) }, { h: 'จำนวนเงิน (บาท)', num: 1, f: p => money(p.amount) }, { h: 'สถานะ', f: p => payBadge(p) },
      { h: '', f: p => p.status === 'Pending' ? `<button class="btn sm primary" data-act="pay_mark" data-id="${p.id}">บันทึกจ่าย</button>` : '' }], rows);
}

function bars(items, fmt = String, color = 'var(--wine)') {
  const mx = Math.max(1, ...items.map(i => i.v));
  return `<div class="bars">${items.map(i => `<div class="bar"><span>${esc(i.l)}</span><div class="tr"><div class="fl" style="width:${(i.v / mx * 100).toFixed(1)}%;background:${i.c || color}"></div></div><span class="val">${fmt(i.v)}</span></div>`).join('')}</div>`;
}
function pgDash() {
  const act = DB.actors.filter(a => a.status === 'Active').length, openP = DB.projects.filter(p => ['Open', 'In_Progress'].includes(p.status)).length;
  const ov = allPayments().filter(isOverdue), waiting = DB.roles.filter(r => r.status === 'Selected').length;
  const rc = { Selected: 'var(--gilt)', Confirmed: 'var(--ok)', Rejected_by_Actor: 'var(--bad)', Cancelled_by_Organizer: 'var(--off)' };
  const pc = { Pending: 'var(--gilt)', Paid: 'var(--ok)', Cancelled: 'var(--off)' };
  const pay = allPayments();
  const pop = DB.skills.map(s => ({ l: s.name, v: DB.actors.filter(a => a.skills.includes(s.id)).length })).sort((a, b) => b.v - a.v).slice(0, 10);
  const perProj = DB.projects.map(p => ({ l: p.name, paid: pay.filter(x => x.role.project === p.id && x.status === 'Paid').reduce((s, x) => s + x.amount, 0), pend: pay.filter(x => x.role.project === p.id && x.status === 'Pending').reduce((s, x) => s + x.amount, 0) }));
  const mxp = Math.max(1, ...perProj.map(p => p.paid + p.pend));
  return pgHead('ภาพรวม', 'Dashboard', 'สรุปภาพรวมของนักแสดง โปรเจกต์ บท และการเงิน') +
    `<div class="stats">${stat('นักแสดงพร้อมรับงาน', act, `พักงาน ${DB.actors.length - act} คน`)}${stat('โปรเจกต์ที่เปิดอยู่', openP)}${stat('งวดเลยกำหนดจ่าย', ov.length, ov.length ? `รวม ${money(ov.reduce((s, p) => s + p.amount, 0))} บาท` : 'ไม่มีงวดค้าง', ov.length ? 'bad' : 'ok')}${stat('บทที่รอนักแสดงตอบ', waiting)}</div>
    <div class="grid g2"><div class="card"><h3 style="font:500 1.1rem var(--serif);margin-bottom:.8rem">บทแยกตามสถานะ</h3>${bars(Object.keys(L.roleSt).map(k => ({ l: L.roleSt[k], v: DB.roles.filter(r => r.status === k).length, c: rc[k] })))}</div>
    <div class="card"><h3 style="font:500 1.1rem var(--serif);margin-bottom:.8rem">ยอดเงินแยกตามสถานะงวด <span class="hint">บาท</span></h3>${bars(Object.keys(L.paySt).map(k => ({ l: L.paySt[k], v: pay.filter(p => p.status === k).reduce((s, p) => s + p.amount, 0), c: pc[k] })), money)}</div></div>
    <div class="grid g2" style="margin-top:.9rem"><div class="card"><h3 style="font:500 1.1rem var(--serif);margin-bottom:.8rem">ทักษะที่นักแสดงมีมากที่สุด</h3>${bars(pop)}</div>
    <div class="card"><h3 style="font:500 1.1rem var(--serif);margin-bottom:.8rem">จ่ายแล้ว และรอจ่าย ต่อโปรเจกต์ <span class="hint">บาท</span></h3><div class="bars">${perProj.map(p => `<div class="bar" style="grid-template-columns:minmax(6rem,1fr) 3fr auto"><span>${esc(p.l)}</span><div class="tr" style="display:flex"><div class="fl" style="width:${p.paid / mxp * 100}%;background:var(--ok);border-radius:8px 0 0 8px"></div><div class="fl" style="width:${p.pend / mxp * 100}%;background:var(--gilt);border-radius:0 8px 8px 0"></div></div><span class="val">${money(p.paid + p.pend)}</span></div>`).join('')}</div>
    <p class="hint" style="margin-top:.7rem"><span style="color:var(--ok)">■</span> จ่ายแล้ว &nbsp; <span style="color:var(--gilt-ink)">■</span> รอจ่าย</p></div></div>`;
}

/* ---------- ฝั่งนักแสดง ---------- */
const RG = ['name', 'gender', 'status', 'birth', 'prov', 'exp', 'h', 'w', 'bust', 'waist', 'hip', 'shoe', 'size', 'body', 'skin', 'hairC', 'hairL', 'hairT', 'eye', 'look', 'bio'];
function loadRg(a) {
  RG.forEach(k => { F['rg.' + k] = a[k] ?? ''; });
  ['tattoo', 'pierce', 'travel'].forEach(k => { F['rg.' + k] = !!a[k]; });
  F['rg.sk'] = a.skills.slice(); S.rgLoaded = a.id;
}
function clearRg() {
  RG.forEach(k => { delete F['rg.' + k]; }); ['tattoo', 'pierce', 'travel', 'publish'].forEach(k => delete F['rg.' + k]); F['rg.sk'] = []; S.rgLoaded = null;
}
function gatherRg() { const o = {}; RG.forEach(k => { o[k] = F['rg.' + k]; }); ['tattoo', 'pierce', 'travel'].forEach(k => { o[k] = !!F['rg.' + k]; }); return o; }
function pgRegister() {
  const edit = S.rgMode === 'edit', me = meActor();
  if (edit && S.rgLoaded !== me.id) loadRg(me);
  const r = k => 'rg.' + k;
  const lbl = o => objOpts(o, 'ไม่ระบุ');
  return pgHead('สำหรับนักแสดง', edit ? 'แก้โปรไฟล์' : 'สมัครเป็นนักแสดง / โมเดล', 'กรอกให้ตรงตามจริง ข้อมูลรูปลักษณ์ใช้ให้ผู้จัดงานกรองหาคน (ระบบรับเฉพาะอายุ 18 ปีขึ้นไป)') +
    `<div class="tabs" role="tablist"><button role="tab" aria-selected="${!edit}" data-act="rg_mode" data-v="new">สมัครใหม่</button><button role="tab" aria-selected="${edit}" data-act="rg_mode" data-v="edit">แก้โปรไฟล์ของฉัน</button></div>` +
    (edit ? actorBar() + '<div style="height:1rem"></div>' : '') +
    sec('ข้อมูลหลัก') + `<div class="form-card"><div class="grid g3">${fld('ชื่อ-นามสกุล', inp(r('name'), { ph: 'เช่น สมหญิง ใจดี' }))}${fld('เพศ', sel(r('gender'), objOpts(L.gender), { def: 'Female' }))}${edit ? fld('สถานะ', sel(r('status'), objOpts(L.actorSt))) : fld('วันเกิด', inp(r('birth'), { type: 'date' }))}
      ${edit ? fld('วันเกิด', inp(r('birth'), { type: 'date' })) : ''}${fld('จังหวัด', sel(r('prov'), [['', 'ไม่ระบุ'], ...PROVINCES.map(x => [x, x])]))}${fld('ระดับประสบการณ์', sel(r('exp'), objOpts(L.exp), { def: 'Beginner' }))}</div>
      <div style="margin-top:.8rem">${chk(r('travel'), 'เดินทางต่างจังหวัดได้')}</div></div>` +
    sec('รูปร่าง') + `<div class="form-card"><div class="grid g4">${fld('ส่วนสูง (ซม.)', inp(r('h'), { type: 'number', attr: 'inputmode="numeric"' }))}${fld('น้ำหนัก (กก.)', inp(r('w'), { type: 'number', attr: 'inputmode="decimal" step="0.5"' }))}${fld('รอบอก (ซม.)', inp(r('bust'), { type: 'number' }))}${fld('รอบเอว (ซม.)', inp(r('waist'), { type: 'number' }))}
      ${fld('รอบสะโพก (ซม.)', inp(r('hip'), { type: 'number' }))}${fld('เบอร์รองเท้า (EU)', inp(r('shoe'), { type: 'number', attr: 'step="0.5"' }))}${fld('ไซซ์เสื้อ', sel(r('size'), [['', 'ไม่ระบุ'], ...SIZES.map(x => [x, x])]))}${fld('รูปร่าง', sel(r('body'), lbl(L.body)))}</div></div>` +
    sec('หน้าตาและลักษณะ', 'ภาพวาดตัวแทนของคุณจะเปลี่ยนตามค่าที่เลือก') + `<div class="form-card"><div class="grid g4">${fld('สีผิว', sel(r('skin'), lbl(L.skin)))}${fld('สีผม', sel(r('hairC'), lbl(L.hairC)))}${fld('ความยาวผม', sel(r('hairL'), lbl(L.hairL)))}${fld('ลักษณะผม', sel(r('hairT'), lbl(L.hairT)))}${fld('สีตา', sel(r('eye'), lbl(L.eye)))}</div>
      <div style="margin-top:.8rem;display:flex;gap:1.4rem;flex-wrap:wrap">${chk(r('tattoo'), 'มีรอยสัก')}${chk(r('pierce'), 'เจาะหู/เจาะอื่นๆ')}</div>
      <div style="margin-top:.9rem">${fld('รายละเอียดรูปลักษณ์เพิ่มเติม', inp(r('look'), { ph: 'เช่น สูง 165 ซม. ผมยาวดำ ใส่แว่น' }))}</div></div>` +
    sec('แนะนำตัว') + `<div class="form-card">${ta(r('bio'), { ph: 'เล่าสั้นๆ ว่าถนัดงานแบบไหน (ไม่เกิน 500 ตัวอักษร)', max: 500 })}</div>` +
    sec('ทักษะ', 'เลือกให้ตรงตามจริง ผู้จัดงานจะหาคุณจากทักษะเหล่านี้') + `<div class="form-card">${skillPicker(r('sk'))}
      ${edit ? '' : `<div style="margin-top:1rem">${chk(r('publish'), 'เปิดโปรไฟล์ให้ผู้จัดงานเห็นทันที (ต้องเลือกทักษะอย่างน้อย 1 อย่าง)', true)}</div>`}
      <div class="btns"><button class="btn primary" data-act="rg_save">${edit ? 'บันทึกโปรไฟล์' : 'สมัครเป็นนักแสดง'}</button></div></div>`;
}

function pgProfile() {
  const me = meActor();
  if (S.pfLoaded !== me.id) { F['pf.name'] = me.name; F['pf.bio'] = me.bio; F['pf.sk'] = me.skills.slice(); S.pfLoaded = me.id; S.wkEdit = null; }
  const rd = readiness(me), ed = S.wkEdit && me.works.find(w => w.id === S.wkEdit);
  const ck = (ok, t) => `<span class="${ok ? 'done' : ''}">${ok ? '✓' : '○'} ${t}</span>`;
  return pgHead('สำหรับนักแสดง', 'โปรไฟล์และผลงานของฉัน', 'ใส่ชื่อ แท็กทักษะ และผลงาน เพื่อให้ผู้จัดงานเห็นคุณตอนเลือกนักแสดง ถ้ายังไม่ใส่อะไร คนอื่นจะไม่เห็นคุณ') + actorBar() + '<div style="height:1rem"></div>' +
    `<div class="vis ${me.pub ? 'on' : ''}"><div class="ic">${eyeIcon(!me.pub, me.pub ? '#2F6F57' : '#6E6468')}</div><div><h3>${me.pub ? 'ผู้จัดงานเห็นโปรไฟล์ของคุณอยู่' : 'โปรไฟล์ของคุณยังซ่อนอยู่'}</h3>
      <p>${me.pub ? 'คุณจะอยู่ในแคตตาล็อก ผลค้นหา และรายชื่อจับคู่ ปิดได้ทุกเมื่อ' : 'ผู้จัดงานจะไม่เห็นคุณในแคตตาล็อก ค้นหา หรือจับคู่ จนกว่าจะเผยแพร่'}</p>
      <div class="checks">${ck(rd.hasName, 'มีชื่อ')}${ck(rd.nSkills > 0, `แท็กทักษะ ${rd.nSkills}`)}${ck(rd.nWorks > 0, `ผลงาน ${rd.nWorks}`)}${ck(rd.hasBio, 'แนะนำตัว (ไม่บังคับ)')}</div>
      <div class="btns">${me.pub ? '<button class="btn" data-act="pf_hide">ซ่อนโปรไฟล์</button>' : `<button class="btn primary" data-act="pf_pub" ${rd.ready ? '' : 'disabled'}>เผยแพร่โปรไฟล์</button>`}${!rd.ready ? '<span class="hint">เลือกทักษะหรือเพิ่มผลงานอย่างน้อย 1 อย่างก่อน</span>' : ''}</div></div></div>` +
    sec('ชื่อ แนะนำตัว และแท็กทักษะ') + `<div class="form-card">${fld('ชื่อที่แสดง', inp('pf.name'))}<div style="margin-top:.8rem">${fld('แนะนำตัว (ไม่เกิน 500 ตัวอักษร)', ta('pf.bio', { max: 500 }))}</div>
      <div class="lab" style="margin:1rem 0 .2rem">แท็กทักษะ</div>${skillPicker('pf.sk')}<div class="btns"><button class="btn primary" data-act="pf_save">บันทึก</button></div></div>` +
    sec('ผลงาน', `${me.works.length}/${MAX_WORKS} ชิ้น`) +
    (me.works.length ? `<div class="works">${me.works.slice().sort((a, b) => b.year - a.year || b.id - a.id).map(w => `<div>${workHtml(w)}<div class="btns" style="margin:.3rem 0 .6rem"><button class="btn sm" data-act="wk_edit" data-id="${w.id}">แก้ไข</button><button class="btn sm danger" data-act="wk_del" data-id="${w.id}">ลบ</button></div></div>`).join('')}</div>` : '<div class="empty">ยังไม่มีผลงาน เพิ่มชิ้นแรกได้ด้านล่าง</div>') +
    `<div class="form-card" style="margin-top:1rem"><h3 style="font:500 1.15rem var(--serif);margin-bottom:.8rem">${ed ? 'แก้ไขผลงาน' : 'เพิ่มผลงาน'}</h3><div class="grid g2">${fld('ชื่อผลงาน', inp('wk.title', { ph: "เช่น แคมเปญ 'ฤดูร้อน'" }))}${fld('ประเภท', sel('wk.type', objOpts(L.work)))}
      ${fld('บทที่รับ / หน้าที่', inp('wk.role', { ph: 'เช่น นางแบบหลัก' }))}${fld('ปี (ค.ศ.)', inp('wk.year', { type: 'number', def: new Date().getFullYear(), attr: 'inputmode="numeric"' }))}</div>
      <div style="margin-top:.8rem">${fld('รายละเอียด (ไม่บังคับ)', ta('wk.desc', { max: 500, rows: 2 }))}</div><div style="margin-top:.8rem">${fld('ลิงก์ผลงาน (ไม่บังคับ ขึ้นต้น https://)', inp('wk.url', { ph: 'https://' }))}</div>
      <div class="btns"><button class="btn primary" data-act="wk_save">${ed ? 'บันทึกการแก้ไข' : '+ เพิ่มผลงาน'}</button>${ed ? '<button class="btn" data-act="wk_cancel">ยกเลิกการแก้ไข</button>' : ''}</div></div>` +
    sec('ผู้จัดงานจะเห็นแบบนี้', me.pub ? '' : 'ตอนนี้ยังซ่อนอยู่ นี่คือตัวอย่างหลังเผยแพร่') + `<div class="card">${profileHtml(me)}</div>`;
}

function pgJobs() {
  const me = meActor(), roles = DB.roles.filter(r => r.actor === me.id).sort((a, b) => b.id - a.id), wait = roles.filter(r => r.status === 'Selected').length;
  return pgHead('สำหรับนักแสดง', 'งานของฉัน', 'บทที่ผู้จัดงานเลือกคุณ กดยอมรับหรือปฏิเสธได้เมื่อสถานะเป็น “รอนักแสดงตอบรับ”') + actorBar() + '<div style="height:1rem"></div>' +
    (wait ? alertBox('warn', `มี ${wait} งานรอคุณตอบรับ`) : '') +
    (roles.length ? `<div class="cardlist">${roles.map(r => `<div class="card">${roleHead(r, `โปรเจกต์ ${projOf(r.project).name} · ${L.projType[projOf(r.project).type]} · ลูกค้า ${projOf(r.project).client}`)}${roleDetail(r)}
      ${r.status === 'Selected' ? `<div class="btns"><button class="btn primary" data-act="job_ok" data-id="${r.id}">ยอมรับงาน</button><button class="btn danger" data-act="job_no" data-id="${r.id}">ปฏิเสธงาน</button></div>` : ''}</div>`).join('')}</div>` : alertBox('info', 'ยังไม่มีผู้จัดงานเลือกคุณเข้าบท'));
}
function pgSchedule() {
  const me = meActor(), rows = DB.roles.filter(r => r.actor === me.id && BUSY.includes(r.status)).flatMap(r => r.sched.map(s => ({ ...s, role: r, proj: projOf(r.project) }))).sort((a, b) => a.date.localeCompare(b.date) || a.start.localeCompare(b.start));
  return pgHead('สำหรับนักแสดง', 'ตารางนัดของฉัน', 'นัดทั้งหมดของบทที่ยังไม่ถูกปฏิเสธหรือยกเลิก ระบบใช้ตารางนี้ตรวจคิวชนตอนผู้จัดงานเลือกคุณ') + actorBar() + '<div style="height:1rem"></div>' +
    tableHtml([{ h: 'วันที่', f: s => `<b>${thDate(s.date)}</b>${s.date < TODAY() ? ' <span class="hint">ผ่านมาแล้ว</span>' : s.date === TODAY() ? ' ' + badge('info', 'วันนี้') : ''}` }, { h: 'เวลา', f: s => `${s.start}-${s.end}` }, { h: 'ประเภท', f: s => L.event[s.type] }, { h: 'บท', f: s => esc(s.role.name) }, { h: 'โปรเจกต์', f: s => esc(s.proj.name) }, { h: 'สถานะบท', f: s => roleBadge(s.role.status) }], rows);
}
function pgMyPay() {
  const me = meActor(), rows = allPayments().filter(p => p.role.actor === me.id).sort((a, b) => a.due.localeCompare(b.due));
  const sm = st => rows.filter(p => p.status === st).reduce((s, p) => s + p.amount, 0), ov = rows.filter(isOverdue);
  return pgHead('สำหรับนักแสดง', 'การจ่ายเงินของฉัน', 'งวดค่าตัวทั้งหมดของคุณ ผู้จัดงานเป็นคนกดบันทึกว่าจ่ายแล้ว') + actorBar() + '<div style="height:1rem"></div>' +
    `<div class="stats">${stat('ได้รับแล้ว', money(sm('Paid')), 'บาท', 'ok')}${stat('รอจ่าย', money(sm('Pending')), 'บาท')}${stat('งวดเลยกำหนด', ov.length, ov.length ? `รวม ${money(ov.reduce((s, p) => s + p.amount, 0))} บาท` : 'ไม่มีงวดค้าง', ov.length ? 'bad' : 'ok')}</div>` +
    tableHtml([{ h: 'โปรเจกต์ / บท', f: p => `<b>${esc(p.project.name)}</b><br><span class="hint">${esc(p.role.name)}</span>` }, { h: 'ครบกำหนด', f: p => thDate(p.due) }, { h: 'จำนวนเงิน (บาท)', num: 1, f: p => money(p.amount) }, { h: 'สถานะ', f: p => payBadge(p) }], rows);
}
