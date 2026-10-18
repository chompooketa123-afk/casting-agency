@echo off
chcp 65001 >nul
REM ดับเบิลคลิกเพื่อแชร์เว็บให้เพื่อนเปิดผ่านอินเทอร์เน็ต (Windows)
REM ต้องเปิด MySQL ใน XAMPP ก่อน และติดตั้ง cloudflared ครั้งเดียว:  winget install Cloudflare.cloudflared
REM จะมีลิงก์ https://....trycloudflare.com ขึ้นในหน้าต่างนี้ ส่งให้เพื่อนได้ (ใช้ได้ตอนหน้าต่างนี้เปิดอยู่)
REM คำเตือน: เว็บนี้ไม่มีระบบล็อกอิน ใครมีลิงก์ก็กดได้ทุกปุ่ม แชร์เฉพาะตอนเดโม
cd /d "%~dp0"
where cloudflared >nul 2>nul
if errorlevel 1 (
  echo ยังไม่ได้ติดตั้ง cloudflared  -^> เปิด PowerShell พิมพ์:  winget install Cloudflare.cloudflared
  pause
  exit /b 1
)
start "casting-app" /min python -m streamlit run app.py --server.port 8501 --server.headless true
timeout /t 5 >nul
cloudflared tunnel --url http://localhost:8501
pause
