# streamlit run 1.py

import os
import streamlit as st
import pandas as pd
import pymysql
from dotenv import load_dotenv

# 1. .env 파일 로드
load_dotenv()

# 2. 환경변수에서 불러오기
host = os.getenv("MYSQL_HOST")
port = int(os.getenv("MYSQL_PORT", 3306))
user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
database = os.getenv("MYSQL_DATABASE")

# ✅ DB 연결
connection = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

st.title("PopPang 관리자 페이지")

# ✅ 데이터 조회
query = "SELECT * FROM users LIMIT 20;"
df = pd.read_sql(query, connection)

st.dataframe(df)

# ✅ CRUD 예시
new_nickname = st.text_input("닉네임 변경 (ID=1)")
if st.button("업데이트"):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE users SET nickname=%s WHERE id=1", (new_nickname,))
        connection.commit()
        st.success("닉네임이 변경되었습니다!")

connection.close()
