#!/bin/bash
# ดับเบิลคลิกเพื่อ "แชร์เว็บให้เพื่อนเปิดผ่านอินเทอร์เน็ต" (Mac)
# ต้องเปิด MySQL ใน XAMPP ก่อน และติดตั้ง cloudflared ครั้งเดียว:  brew install cloudflared
# พอรันแล้วจะมีลิงก์รูปแบบ https://xxxx.trycloudflare.com  ส่งให้เพื่อนเปิดได้ทั้งมือถือและคอม
# (ลิงก์ใช้ได้เฉพาะตอนหน้าต่างนี้เปิดอยู่ และเครื่องคุณต้องเปิดค้างไว้)
cd "$(dirname "$0")"
if ! command -v cloudflared >/dev/null 2>&1; then
  echo "ยังไม่ได้ติดตั้ง cloudflared  -> เปิด Terminal พิมพ์:  brew install cloudflared"
  echo "(ยังไม่มี brew? ดู https://brew.sh หรือใช้ลิงก์ในหัวข้อ 13 ของ README)"
  read -p "กด Enter เพื่อปิด"; exit 1
fi
python3 -m streamlit run app.py --server.port 8501 --server.headless true > /tmp/casting-app.log 2>&1 &
APP=$!
trap "kill $APP 2>/dev/null" EXIT
sleep 4
echo "=========================================="
echo " รอสักครู่ จะมีลิงก์ https://....trycloudflare.com ขึ้นด้านล่าง"
echo " ส่งลิงก์นั้นให้เพื่อนได้เลย  หยุดแชร์: กด Ctrl+C"
echo " คำเตือน: เว็บนี้ไม่มีระบบล็อกอิน ใครมีลิงก์ก็กดได้ทุกปุ่ม แชร์เฉพาะตอนเดโม"
echo "=========================================="
cloudflared tunnel --url http://localhost:8501
