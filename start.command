#!/bin/bash
# ดับเบิลคลิกไฟล์นี้เพื่อเปิดเว็บ (Mac)  -- ต้องเปิด MySQL ใน XAMPP ก่อน
# เปิดให้มือถือที่ต่อ Wi-Fi เดียวกันเข้าได้ด้วย: ดูที่อยู่ "Network URL" ที่ขึ้นด้านล่าง
cd "$(dirname "$0")"
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
echo "=========================================="
echo " Casting Agency"
echo " บนคอม     : http://localhost:8501"
if [ -n "$IP" ]; then
echo " บนมือถือ  : http://$IP:8501   (ต้องต่อ Wi-Fi เดียวกับเครื่องนี้)"
fi
echo " หยุดเว็บ  : กด Ctrl+C หรือปิดหน้าต่างนี้"
echo "=========================================="
exec python3 -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
