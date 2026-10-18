"""
หน้า: ตารางนัดของฉัน (ฝั่งนักแสดง)

หน้านี้ดึง schedule_of_actor  ->  SCHEDULE JOIN ROLE JOIN PROJECT
(เฉพาะบทที่สถานะ Selected/Confirmed เพราะบทที่ปฏิเสธหรือยกเลิกแล้วไม่ต้องไปตามนัด)
"""
import altair as alt
import pandas as pd
import streamlit as st

import queries as q
import ui
from config import EVENT_TYPE_LABEL

ui.page_header("ตารางนัดของฉัน", "นัดถ่ายทำ ฟิตติ้ง และซ้อม ของบทที่รอตอบรับและยืนยันแล้ว")
actor_id = ui.actor_picker()
if not actor_id:
    st.stop()

rows = q.schedule_of_actor(actor_id)
if not rows:
    st.info("ยังไม่มีนัดหมาย")
    st.stop()

for r in rows:
    r["event_type"] = EVENT_TYPE_LABEL[r["event_type"]]

ui.table(rows, {"event_date": "วันที่", "start_time": "เริ่ม", "end_time": "เลิก", "event_type": "ประเภท",
                "project_name": "โปรเจกต์", "role_name": "บท", "role_status": "สถานะบท"},
         badges={"role_status": lambda r: ui.role_badge(r["role_status"])})

ui.section("ไทม์ไลน์", "แท่งคือช่วงเวลาที่มีนัดในแต่ละวัน")

# กราฟไทม์ไลน์ : แกนตั้ง = วัน, แกนนอน = ชั่วโมง, แท่ง = ช่วงเวลาที่มีนัด
df = pd.DataFrame(rows)
df["date"] = df["event_date"].astype(str)
df["start_h"] = df["start_time"].str[:2].astype(int) + df["start_time"].str[3:5].astype(int) / 60
df["end_h"] = df["end_time"].str[:2].astype(int) + df["end_time"].str[3:5].astype(int) / 60
chart = (
    alt.Chart(df)
    .mark_bar(cornerRadius=6, height=24)
    .encode(
        y=alt.Y("date:N", title="วันที่", sort=None),
        x=alt.X("start_h:Q", title="ชั่วโมง", scale=alt.Scale(domain=[6, 22])),
        x2="end_h:Q",
        color=alt.Color("project_name:N", title=None,
                        scale=alt.Scale(range=["#B5174F", "#B8893B", "#1F7A5A", "#5B3A6E", "#E58AA6", "#7D6773"])),
        tooltip=["project_name", "role_name", "event_type", "start_time", "end_time"],
    )
    .properties(height=max(120, 45 * df["date"].nunique()))
)
st.altair_chart(ui._style(chart), width="stretch")
