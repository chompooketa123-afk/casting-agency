}
/* Streamlit เรียกฟังก์ชันนี้ทุกครั้งที่ข้อมูลเปลี่ยน: เปิดหน้าตาครั้งเดียว แล้วส่งข้อมูลล่าสุดเข้าไป */
export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  let c = window.__CASTING;
  if (!c || c.root !== parentElement) { c = bootApp(parentElement); window.__CASTING = c; }
  c.update(data, setTriggerValue);
}
