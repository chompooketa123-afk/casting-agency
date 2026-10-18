/* ====================== เมนู + หน้าเว็บ ====================== */
const PAGES = {
  home: { g: 'home', t: 'หน้าแรก', fn: pgHome }, talent: { g: 'talent', t: 'แคตตาล็อก', fn: pgTalent },
  org_search: { g: 'org', t: 'ค้นหานักแสดง', fn: pgSearch }, org_projects: { g: 'org', t: 'โปรเจกต์', fn: pgProjects },
  org_casting: { g: 'org', t: 'สร้างบท + จับคู่', fn: pgCasting }, org_roles: { g: 'org', t: 'จัดการบท', fn: pgRoles },
  org_payments: { g: 'org', t: 'งวดจ่ายเงิน', fn: pgOrgPay }, dashboard: { g: 'org', t: 'Dashboard', fn: pgDash },
  actor_register: { g: 'actor', t: 'สมัคร / แก้โปรไฟล์', fn: pgRegister }, actor_profile: { g: 'actor', t: 'โปรไฟล์และผลงานของฉัน', fn: pgProfile },
  actor_jobs: { g: 'actor', t: 'งานของฉัน', fn: pgJobs }, actor_schedule: { g: 'actor', t: 'ตารางนัด', fn: pgSchedule }, actor_payments: { g: 'actor', t: 'การจ่ายเงิน', fn: pgMyPay },
};
const GROUPS = [['home', 'หน้าแรก', 'home'], ['talent', 'แคตตาล็อก', 'talent'], ['org', 'ผู้จัดงาน', 'org_search'], ['actor', 'นักแสดง', 'actor_profile']];
let THEME = 'system';
try { THEME = localStorage.getItem('casting-theme') || 'system'; } catch (e) {}
function applyTheme() { const r = $('#app'); if (THEME === 'system') r.removeAttribute('data-theme'); else r.setAttribute('data-theme', THEME); }

function shell() {
  const pg = PAGES[S.page] || PAGES.home, g = pg.g;
  const sub = (g === 'org' || g === 'actor') ? Object.entries(PAGES).filter(([, v]) => v.g === g) : [];
  const waiting = DB.roles.filter(r => r.actor === DB.me && r.status === 'Selected').length;
  return `<header class="top"><div class="row"><button class="brand" data-act="nav" data-p="home" aria-label="หน้าแรก">Casting<span style="color:var(--gilt)">.</span></button>
    ${GROUPS.map(([k, t, p]) => `<button class="pill" data-act="nav" data-p="${p}" aria-pressed="${g === k}">${t}${k === 'actor' && waiting ? ` <span class="badge b-wait" style="padding:0 .45rem">${waiting}</span>` : ''}</button>`).join('')}
    <button class="pill theme" data-act="theme" aria-label="สลับธีม" title="สลับธีม สว่าง/มืด">${THEME === 'dark' ? '☾ มืด' : THEME === 'light' ? '☀ สว่าง' : '◐ อัตโนมัติ'}</button></div>
    ${sub.length ? `<nav class="sub" aria-label="เมนูย่อย">${sub.map(([k, v]) => `<button class="pill" data-act="nav" data-p="${k}" aria-pressed="${S.page === k}">${v.t}</button>`).join('')}</nav>` : ''}</header>
  <div class="wrap"><main class="page">${pg.fn()}</main></div>
  <div class="wrap" style="padding-bottom:2rem">${sqlPanel()}<footer class="foot"><div class="cols"><div><b>Casting Agency</b><br>ระบบเอเจนซี่นักแสดงและโมเดลลิ่ง · CSS222 Database Systems<br>ข้อมูลทั้งหมดเป็นข้อมูลสมมติเพื่อสาธิต</div>
    <div><b>Streamlit + MySQL</b><br>ข้อมูลอยู่ในฐานข้อมูลร่วมกันทั้งกลุ่ม<br><button class="btn sm" data-act="refresh" style="margin-top:.5rem">รีเฟรชข้อมูล</button></div></div>
    <div class="mark" aria-hidden="true">CASTING</div></footer></div>`;
}
function sqlPanel() {
  const x = S.lastSql; if (!x || !x.sql || !x.sql.length) return '';
  return `<details class="fold sqlbox"><summary>SQL ที่เพิ่งรัน <span class="hint">คำสั่ง ${esc(x.op)} · ตาราง ${esc(x.touch || '-')}</span></summary><div class="in">${x.sql.map(r => `<pre>${esc(r.sql)}${r.params && r.params.length ? '\n-- ค่า: ' + esc(r.params.join(', ')) : ''}</pre>`).join('')}</div></details>`;
}
function overlay() {
  if (!S.dlg) return '';
  const a = actorOf(S.dlg.id); if (!a) return '';
  return `<div class="ov" data-act="close_bg"><div class="dlg" role="dialog" aria-modal="true" aria-label="โปรไฟล์ ${esc(a.name)}"><button class="x" data-act="close" aria-label="ปิด">×</button><h2 class="t">โปรไฟล์นักแสดง</h2>${profileHtml(a)}</div></div>`;
}

function snap() {
  $$('[data-f]').forEach(el => { F[el.dataset.f] = el.type === 'checkbox' ? el.checked : el.value; });
  $$('[data-r]').forEach(el => { const r = R[el.dataset.r]; if (r && r[el.dataset.i]) r[el.dataset.i][el.dataset.k] = el.value; });
  $$('details[data-d]').forEach(d => { F['d.' + d.dataset.d] = d.open; });
}
function scroller() {
  let n = ROOT.host;
  while (n) {
    n = n.parentElement || (n.getRootNode && n.getRootNode().host);
    if (n && n !== document.body && n !== document.documentElement && /(auto|scroll)/.test(getComputedStyle(n).overflowY) && n.scrollHeight > n.clientHeight) return n;
  }
  return document.scrollingElement || document.documentElement;
}
function render() {
  if (!DB) { $('#root').innerHTML = '<div class="loading">กำลังโหลดข้อมูลจากฐานข้อมูล…</div>'; return; }
  const sc = scroller(), y = sc.scrollTop, ae = ROOT.activeElement;
  let fsel = null, caret = null;
  if (ae && ae.dataset && (ae.dataset.f || ae.dataset.r)) {
    fsel = ae.dataset.f ? `[data-f="${CSS.escape(ae.dataset.f)}"]` : `[data-r="${ae.dataset.r}"][data-i="${ae.dataset.i}"][data-k="${ae.dataset.k}"]`;
    try { caret = [ae.selectionStart, ae.selectionEnd]; } catch (e) {}
  }
  $('#root').innerHTML = shell();
  $('#ov').innerHTML = overlay();
  if (fsel) { const n = $(fsel); if (n) { n.focus({ preventScroll: true }); try { if (caret && caret[0] != null) n.setSelectionRange(caret[0], caret[1]); } catch (e) {} } }
  sc.scrollTo(0, y);
}
function toast(msg, kind = 'ok') {
  const t = $('#toast'); t.innerHTML = `<div class="toast ${kind}" role="status">${esc(msg)}</div>`;
  clearTimeout(toast.t); toast.t = setTimeout(() => { t.innerHTML = ''; }, kind === 'bad' ? 5600 : 3600);
}
/* ---------- คุยกับ Python (bridge.py) ---------- */
let SEND = null, SEQ = 0, LASTVER = null, chain = Promise.resolve();
const PENDING = {};
const busy = () => Object.keys(PENDING).length > 0;
function remote(op, args) {
  const p = chain.then(() => new Promise(res => {
    const id = `${Date.now()}-${++SEQ}`;
    PENDING[id] = res;
    SEND({ id, op, args: args || {} });
    setTimeout(() => { if (PENDING[id]) { delete PENDING[id]; res({ id, ok: false, error: 'เซิร์ฟเวอร์ไม่ตอบสนอง ลองใหม่อีกครั้ง' }); } }, 25000);
  }));
  chain = p.then(() => {}, () => {});
  return p;
}
/* fn = ตรวจกฎ+ลองทำบนข้อมูลในหน้าเว็บก่อน (ผิดกฎก็แจ้งทันที)  op = [ชื่อคำสั่ง, ข้อมูล] ส่งไปให้ MySQL ทำจริง */
async function doit(fn, okMsg, op) {
  let r0;
  try { r0 = fn ? fn() : undefined; }
  catch (e) { if (e instanceof BizErr) { toast(e.message, 'bad'); return { ok: false }; } throw e; }
  if (op) {
    toast('กำลังบันทึกลงฐานข้อมูล…', 'info');
    const rep = await remote(op[0], op[1]);
    if (rep.sql) S.lastSql = { op: op[0], touch: rep.touch, sql: rep.sql };
    if (!rep.ok) { toast(rep.error, 'bad'); render(); return { ok: false }; }
    if (rep.result !== null && rep.result !== undefined) r0 = rep.result;
  }
  if (okMsg) toast(typeof okMsg === 'function' ? okMsg(r0) : okMsg);
  return { ok: true, r: r0 };
}
function go(p, mode) {
  S.page = p; S.dlg = null; S.confirmReset = false;
  if (mode) { S.rgMode = mode; if (mode === 'new') clearRg(); }
  render(); scroller().scrollTo(0, 0);
}
const toggleIn = (arr, v) => (arr.includes(v) ? arr.filter(x => x !== v) : arr.concat([v]));

/* ====================== ปุ่มทั้งหมด ====================== */
const A = {
  nav: el => go(el.dataset.p, el.dataset.mode),
  theme: () => { THEME = THEME === 'system' ? 'dark' : THEME === 'dark' ? 'light' : 'system'; try { localStorage.setItem('casting-theme', THEME); } catch (e) {} applyTheme(); render(); },
  view: el => { S.dlg = { id: Number(el.dataset.id) }; render(); },
  close: () => { S.dlg = null; render(); },
  close_bg: (el, ev) => { if (ev.target === el) A.close(); },
  tg: el => { const k = el.dataset.k, v = el.dataset.v, val = v !== '' && !isNaN(v) ? Number(v) : v; F[k] = toggleIn(picked(k), val); render(); },
  tab: el => { S.tab[el.dataset.k] = el.dataset.v; render(); },
  refresh: async () => { toast('กำลังโหลดข้อมูลล่าสุด…', 'info'); const rep = await remote('refresh'); render(); toast(rep.ok ? 'ข้อมูลเป็นปัจจุบันแล้ว' : rep.error, rep.ok ? 'ok' : 'bad'); },
  row_add: el => { const n = el.dataset.n; R[n].push(n === 'cs' ? { type: 'Shoot', date: addDays(TODAY(), 7), start: '09:00', end: '17:00' } : { due: addDays(TODAY(), 30), amount: 0 }); render(); },
  row_del: el => { R[el.dataset.n].splice(Number(el.dataset.i), 1); render(); },
  /* ค้นหา (อ่านข้อมูลล่าสุดจาก MySQL ที่โหลดมาแล้ว) */
  do_search: async () => {
    const avail = F['srch.avail'] ? { date: F['srch.date'], start: F['srch.start'], end: F['srch.end'] } : null;
    const r = await doit(() => { if (avail && (!avail.date || !avail.start || !avail.end)) fail('กรุณาเลือกวันที่และเวลา'); return searchActors({ gender: F['srch.gender'], skills: pickedSkills('srch.sk'), text: F['srch.text'], avail, onlyActive: !F['srch.inactive'], traits: readTraits('srch') }).map(a => a.id); });
    if (r.ok) S.srch = r.r; render();
  },
  clear_search: () => { Object.keys(F).filter(k => k.startsWith('srch.') && !['srch.date', 'srch.start', 'srch.end'].includes(k)).forEach(k => delete F[k]); S.srch = null; render(); },
  /* โปรเจกต์ */
  proj_create: async () => {
    const args = { name: F['pj.name'], type: F['pj.type'] || 'Series', client: F['pj.client'] };
    const r = await doit(() => createProject(args.name, args.type, args.client), id => `สร้างโปรเจกต์ #${id} แล้ว`, ['createProject', args]);
    if (r.ok) { F['pj.name'] = ''; F['pj.client'] = ''; } render();
  },
  /* จับคู่ */
  cast_find: async () => {
    const r = await doit(() => {
      const name = (F['cast.role'] || '').trim(); if (!name) fail('กรุณากรอกชื่อบท');
      const fee = Number(F['cast.fee']); if (!(fee > 0)) fail('ค่าตัวต้องมากกว่า 0');
      const slots = R.cs.map(s => ({ type: s.type, date: s.date, start: s.start, end: s.end }));
      const inst = R.cp.map(p => ({ due: p.due, amount: Number(p.amount) || 0 }));
      validateSlots(slots); validateInst(inst, fee);
      const skills = pickedSkills('cast.sk'), gender = F['cast.gender'] || '', traits = readTraits('ct');
      const el = findMatching(skills, slots, gender, traits).map(a => a.id);
      return { project: Number(F['cast.project'] || ($('[data-f="cast.project"]') || {}).value), roleName: name, fee, skills, gender, traits, slots, inst, eligible: el, excluded: explainExcluded(skills, slots, el, gender, traits), sql: buildSql(skills, slots, gender, traits) };
    });
    if (r.ok) { S.match = r.r; S.tab.cast = 'ok'; } render();
  },
  cast_clear: () => { S.match = null; render(); },
  cast_pick: async el => {
    const a = actorOf(Number(el.dataset.id)), m = S.match;
    const args = { m: { project: m.project, roleName: m.roleName, fee: m.fee, skills: m.skills, slots: m.slots, inst: m.inst }, actor: a.id };
    const r = await doit(() => createRole(m, a.id), () => `สร้างบท '${m.roleName}' และเลือก ${a.name} แล้ว สถานะ: รอนักแสดงตอบรับ`, ['createRole', args]);
    if (r.ok) { S.match = null; resetCastForm(); F['cast.role'] = ''; F['cast.sk'] = []; }
    render();
  },
  sure: el => { S.confirmCancel[el.dataset.id] = el.checked; render(); },
  role_cancel: async el => {
    const id = Number(el.dataset.id), r = DB.roles.find(x => x.id === id);
    await doit(() => cancelRole(id), `ยกเลิกการจ้างบท '${r.name}' แล้ว (งวดที่ยังไม่จ่ายถูกยกเลิกด้วย)`, ['cancelRole', { rid: id }]);
    delete S.confirmCancel[id]; render();
  },
  pay_mark: async el => { const id = Number(el.dataset.id); await doit(() => markPaid(id), 'บันทึกว่าจ่ายแล้ว', ['markPaid', { pid: id }]); render(); },
  /* นักแสดง */
  rg_mode: el => { S.rgMode = el.dataset.v; if (S.rgMode === 'new') clearRg(); else S.rgLoaded = null; render(); },
  rg_save: async () => {
    const edit = S.rgMode === 'edit', f = gatherRg(), sk = pickedSkills('rg.sk');
    if (edit) {
      const me = meActor();
      const r = await doit(() => updateActor(me.id, f, sk), v => v ? 'บันทึกโปรไฟล์แล้ว' : 'บันทึกแล้ว (โปรไฟล์ซ่อนอยู่ เพราะยังไม่มีทักษะหรือผลงาน)', ['updateActor', { id: me.id, f, skills: sk }]);
      if (r.ok) S.pfLoaded = null; render(); return;
    }
    const publish = !!F['rg.publish'];
    const r = await doit(() => registerActor(f, sk, publish), id => `สมัครสำเร็จ รหัส #${id}`, ['registerActor', { f, skills: sk, publish }]);
    if (r.ok) {
      setMe(r.r); const a = actorOf(r.r); clearRg(); S.pfLoaded = null; S.page = 'actor_profile';
      if (a && !a.pub) toast(`สมัครสำเร็จ รหัส #${a.id} · โปรไฟล์ยังซ่อนอยู่ เพิ่มทักษะหรือผลงานแล้วกดเผยแพร่`);
      render(); scroller().scrollTo(0, 0);
    } else render();
  },
  me_change: el => { setMe(Number(el.value)); S.pfLoaded = null; S.rgLoaded = null; S.wkEdit = null; render(); },
  pf_save: async () => {
    const me = meActor(), f = { ...me, name: F['pf.name'], bio: F['pf.bio'] }, sk = pickedSkills('pf.sk');
    const r = await doit(() => updateActor(me.id, f, sk), v => v ? 'บันทึกแล้ว' : 'บันทึกแล้ว แต่โปรไฟล์ถูกซ่อน เพราะไม่เหลือทักษะและผลงาน', ['updateActor', { id: me.id, f, skills: sk }]);
    if (r.ok) S.pfLoaded = null; render();
  },
  pf_pub: async () => { const id = meActor().id; await doit(() => setPublic(id, true), 'เผยแพร่แล้ว ผู้จัดงานเห็นคุณในแคตตาล็อกและผลค้นหา', ['setPublic', { id, pub: true }]); render(); },
  pf_hide: async () => { const id = meActor().id; await doit(() => setPublic(id, false), 'ซ่อนโปรไฟล์แล้ว ผู้จัดงานจะไม่เห็นคุณ', ['setPublic', { id, pub: false }]); render(); },
  wk_save: async () => {
    const me = meActor(), w = { title: F['wk.title'], type: F['wk.type'] || 'Film', role: F['wk.role'], year: F['wk.year'] || new Date().getFullYear(), desc: F['wk.desc'], url: F['wk.url'] };
    const wid = S.wkEdit;
    const r = await doit(() => { wid ? updateWork(me.id, wid, w) : addWork(me.id, w); }, wid ? 'บันทึกผลงานแล้ว' : 'เพิ่มผลงานแล้ว', wid ? ['updateWork', { aid: me.id, wid, w }] : ['addWork', { aid: me.id, w }]);
    if (r.ok) { ['title', 'role', 'desc', 'url'].forEach(k => { F['wk.' + k] = ''; }); F['wk.year'] = new Date().getFullYear(); S.wkEdit = null; } render();
  },
  wk_edit: el => { const w = meActor().works.find(x => x.id === Number(el.dataset.id)); if (!w) return; S.wkEdit = w.id; F['wk.title'] = w.title; F['wk.type'] = w.type; F['wk.role'] = w.role; F['wk.year'] = w.year; F['wk.desc'] = w.desc; F['wk.url'] = w.url; render(); },
  wk_cancel: () => { S.wkEdit = null; ['title', 'role', 'desc', 'url'].forEach(k => { F['wk.' + k] = ''; }); render(); },
  wk_del: async el => {
    const me = meActor(), wid = Number(el.dataset.id);
    const r = await doit(() => deleteWork(me.id, wid), v => v ? 'ลบผลงานแล้ว' : 'ลบผลงานแล้ว โปรไฟล์ถูกซ่อน เพราะไม่เหลือทักษะและผลงาน', ['deleteWork', { aid: me.id, wid }]);
    if (r.ok && S.wkEdit === wid) S.wkEdit = null; render();
  },
  job_ok: async el => { const id = Number(el.dataset.id); await doit(() => respondRole(id, DB.me, true), 'ยอมรับงานแล้ว', ['respondRole', { rid: id, actor: DB.me, accept: true }]); render(); },
  job_no: async el => { const id = Number(el.dataset.id); await doit(() => respondRole(id, DB.me, false), 'ปฏิเสธงานแล้ว งวดที่ยังไม่จ่ายถูกยกเลิก', ['respondRole', { rid: id, actor: DB.me, accept: false }]); render(); },
};
const CHG = {
  me_change: A.me_change, rerender: () => render(),
  proj_status: async el => {
    const id = Number(el.dataset.id), p = projOf(id), st = el.value;
    await doit(() => { p.status = st; }, `เปลี่ยนสถานะ '${p.name}' เป็น ${L.projSt[st]}`, ['setProjectStatus', { id, status: st }]); render();
  },
};

ROOT.addEventListener('click', ev => {
  const el = ev.target.closest('[data-act]'); if (!el) return;
  const act = el.dataset.act; if (!A[act]) return;
  snap(); A[act](el, ev);
});
ROOT.addEventListener('keydown', ev => {
  if ((ev.key === 'Enter' || ev.key === ' ') && ev.target.matches && ev.target.matches('.tcard[data-act]')) { ev.preventDefault(); snap(); A[ev.target.dataset.act](ev.target, ev); }
});
document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && S.dlg && window.__CASTING && window.__CASTING.root === ROOT) A.close(); });
ROOT.addEventListener('change', ev => {
  const el = ev.target;
  const c = el.closest('[data-chg]');
  if (c) { snap(); CHG[c.dataset.chg](c, ev); return; }
  if (!el.dataset) return;
  if (el.dataset.live) { snap(); render(); }
  else if (el.dataset.f === 'cast.fee' || el.dataset.r === 'cp') { snap(); const s = $('#sumchk'); if (s) s.innerHTML = sumHtml(); }
});
ROOT.addEventListener('input', ev => { const el = ev.target; if (el.dataset && el.dataset.live) { snap(); render(); } });

/* ---------- รับข้อมูลใหม่จาก Python (เรียกทุกครั้งที่ Streamlit รันใหม่) ---------- */
function update(data, setTrigger) {
  SEND = x => setTrigger('call', x);
  const rep = data && data.reply;
  if (!data || !data.snap) return;
  if (rep && PENDING[rep.id]) {
    const done = PENDING[rep.id]; delete PENDING[rep.id];
    applySnap(data.snap); LASTVER = data.ver; done(rep); return;
  }
  if (!busy() && data.ver !== LASTVER) { const first = !DB; applySnap(data.snap); LASTVER = data.ver; render(); if (first) applyTheme(); }
}
/* ดึงข้อมูลล่าสุดอัตโนมัติทุก 20 วินาที (เพื่อนในกลุ่มแก้อะไรจะเห็น) ยกเว้นตอนกำลังพิมพ์/เปิดหน้าต่างโปรไฟล์ */
const timer = setInterval(() => {
  if (window.__CASTING && window.__CASTING.root !== ROOT) { clearInterval(timer); return; }
  const ae = ROOT.activeElement;
  if (!SEND || busy() || S.dlg || (ae && /^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName)) || document.hidden) return;
  remote('refresh');
}, 20000);
applyTheme();
return { root: ROOT, update, render };
