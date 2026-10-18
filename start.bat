@echo off
chcp 65001 >nul
REM ดับเบิลคลิกไฟล์นี้เพื่อเปิดเว็บ (Windows)  -- ต้องเปิด MySQL ใน XAMPP ก่อน
REM มือถือที่ต่อ Wi-Fi เดียวกันเข้าได้ที่ "Network URL" ที่ขึ้นด้านล่าง
cd /d "%~dp0"
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
pause
