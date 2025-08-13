import pymysql

try:
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",  # 실제 비밀번호 입력
        database="bobbot"
    )
    print("DB 연결 성공!")
    conn.close()
except Exception as e:
    print("DB 연결 실패:", e)