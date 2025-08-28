import os
import pymysql
from dotenv import load_dotenv
from datetime import datetime

# =========================
# 0) 환경변수 로드 (.env)
# =========================
load_dotenv() 

# =========================
# 1) MySQL 연결 헬퍼
# =========================
def get_conn():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DB", "ict"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,  # tuple 형태 반환
        autocommit=True
    )

# =====================================
# 2) 질문 뽑기 (ict5.question 테이블 기준)
# =====================================
def fetch_questions(interview_type: str):
    conn = get_conn()
    cur = conn.cursor()

    selected = []

    # 1) 선택한 인터뷰 유형 3개
    cur.execute("""
        SELECT question_id, content, interview_type
        FROM question
        WHERE interview_type = %s
        ORDER BY RAND() LIMIT 3
    """, (interview_type,))
    selected.extend(cur.fetchall())

    # 2) 다른 유형에서 1개씩
    all_types = ["인성", "직무", "가치관"]
    other_types = [t for t in all_types if t != interview_type]

    for t in other_types:
        cur.execute("""
            SELECT question_id, content, interview_type
            FROM question
            WHERE interview_type = %s
            ORDER BY RAND() LIMIT 1
        """, (t,))
        row = cur.fetchone()
        if row:
            selected.append(row)

    # 3) 총 5개 보장 (부족 시 랜덤 보충)
    if len(selected) < 5:
        used_ids = [r[0] for r in selected]
        remain = 5 - len(selected)
        if used_ids:
            placeholders = ",".join(["%s"] * len(used_ids))
            sql = f"""
                SELECT question_id, content, interview_type
                FROM question
                WHERE question_id NOT IN ({placeholders})
                ORDER BY RAND() LIMIT %s
            """
            cur.execute(sql, (*used_ids, remain))
        else:
            cur.execute("""
                SELECT question_id, content, interview_type
                FROM question
                ORDER BY RAND() LIMIT %s
            """, (remain,))
        selected.extend(cur.fetchall())

    cur.close()
    conn.close()
    return selected[:5]

def upsert_free_text_question(text_content: str, interview_type: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT question_id FROM question
        WHERE content=%s AND interview_type=%s AND (category IS NULL OR category='')
        LIMIT 1
    """, (text_content, interview_type))
    row = cur.fetchone()
    if row:
        qid = row[0]
    else:
        cur.execute("""
            INSERT INTO question (content, category, interview_type, keywords, source)
            VALUES (%s, %s, %s, %s, %s)
        """, (text_content, "", interview_type, None, "generated"))
        qid = cur.lastrowid
    cur.close()
    conn.close()
    return qid

def ensure_demo_user(user_id: int) -> None:
    """user_id가 없으면 demo user를 생성"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM user WHERE id=%s", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO user (id, email, username, createDate)
            VALUES (%s, %s, %s, %s)
        """, (user_id, f"demo{user_id}@example.com", f"데모사용자{user_id}", datetime.now()))
    cur.close()
    conn.close()

# =====================================
# 3) 세션/질문/답변 로그 (simulation_*)
# =====================================
def start_session(user_id: int, total_questions: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO simulation_session (user_id, status, total_questions, current_step, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, "진행중", total_questions, 0, datetime.now()))
    session_id = cur.lastrowid
    cur.close()
    conn.close()
    return session_id


def log_question(session_id: int, question_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO simulation_question (session_id, question_id)
        VALUES (%s, %s)
    """, (session_id, question_id))
    sim_question_id = cur.lastrowid

    # 진행 단계 +1
    cur.execute("""
        UPDATE simulation_session
        SET current_step = current_step + 1
        WHERE session_id = %s
    """, (session_id,))

    # 자동 종료 체크
    cur.execute("""
        SELECT current_step, total_questions
        FROM simulation_session
        WHERE session_id = %s
    """, (session_id,))
    row = cur.fetchone()

    if row:
        current_step, total_questions = row
        if current_step >= total_questions:
            cur.execute("""
                UPDATE simulation_session
                SET status=%s, end_reason=%s, ended_at=%s
                WHERE session_id=%s
            """, ("완료", "limit_reached", datetime.now(), session_id))

    conn.commit()
    cur.close()
    conn.close()
    
    return sim_question_id

def log_answer(sim_question_id: int, answer_text: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO simulation_answer (sim_question_id, content, created_at)
        VALUES (%s, %s, %s)
    """, (sim_question_id, answer_text, datetime.now()))
    cur.close()
    conn.close()

def end_session(session_id: int, reason: str) -> None:
    """reason: 'limit_reached' or 'user_stop' 등"""
    conn = get_conn()
    cur = conn.cursor()
    status = "완료" if reason == "limit_reached" else "중단"
    cur.execute("""
        UPDATE simulation_session
        SET status=%s, end_reason=%s, ended_at=%s
        WHERE session_id=%s
    """, (status, reason, datetime.now(), session_id))
    cur.close()
    conn.close()

#db에 있는 이력서 분석 키워드 가져오기
def fetch_keywords(user_id: int) -> list[str]:
    """
    특정 사용자의 resume_question 테이블에서 키워드(question 컬럼) 불러오기
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT question
        FROM resume_question
        WHERE user_id = %s
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows] if rows else []