import sqlite3
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_google_vertexai import ChatVertexAI
import vertexai
import random

def fetch_questions(interview_type, db_path='interview_questions.db'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    selected_questions = []

    # 1️⃣ 먼저 - 주 인터뷰 유형 질문 3개
    cur.execute("""
        SELECT id, question, interview_type FROM interview_questions
        WHERE interview_type = ?
        ORDER BY RANDOM() LIMIT 3
    """, (interview_type,))
    main_questions = cur.fetchall()
    selected_questions.extend(main_questions)

    # 2️⃣ 이후 - 다른 유형에서 1개씩 뽑기
    other_types = ["인성", "경험", "상황"]
    other_types.remove(interview_type)

    for q_type in other_types:
        cur.execute("""
            SELECT id, question, interview_type FROM interview_questions
            WHERE interview_type = ?
            ORDER BY RANDOM() LIMIT 1
        """, (q_type,))
        q = cur.fetchone()
        if q:
            selected_questions.append(q)

    conn.close()

    # 3️⃣ 총 5개 보장 (혹시 DB 부족할 경우 랜덤 보충)
    if len(selected_questions) < 5:
        used_ids = [q[0] for q in selected_questions]
        placeholder = ",".join("?" * len(used_ids))
        if used_ids:
            cur.execute(f"""
                SELECT id, question, interview_type FROM interview_questions
                WHERE id NOT IN ({placeholder})
                ORDER BY RANDOM() LIMIT ?
            """, (*used_ids, 5 - len(selected_questions)))
        else:
            cur.execute("""
                SELECT id, question, interview_type FROM interview_questions
                ORDER BY RANDOM() LIMIT ?
            """, (5 - len(selected_questions),))
        selected_questions.extend(cur.fetchall())

    return selected_questions[:5]

def init_llm_chain():
    PROJECT_ID = "magnificent-ray-469309-m3"
    REGION = "us-central1"

    vertexai.init(project=PROJECT_ID, location=REGION)
    llm = ChatVertexAI(model="gemini-2.0-flash-001", temperature=0.7)

    system_message = SystemMessage(content="""
    당신은 면접관입니다. 다음 원칙을 반드시 지키세요:
    - 질문은 항상 한 개씩만 생성하세요.
    - 이미 생성된 질문은 다시 하지 마세요.
    - 질문은 전달받은 이력서 키워드를 기반으로 만들어야 합니다.
    - 허구 내용 생성은 금지입니다.
    - 질문은 불필요하게 장황하지 않게, 간결하고 명확하게 작성하세요.
    - 한 가지 주제에 대해 꼬리질문 3개이상 금지입니다.
    - 이력서 키워드를 기반으로 질문을 생성하되 무조건 직무관련 질문일 필요는 없습니다.
    - 질문을 할 때 괄호로 예시 내용을 제공하지 마세요.
     """)

    persona_template = ChatPromptTemplate.from_messages([
        ("system", system_message.content),
        ("human", """
        면접 유형: {interview_type}
        면접관 성향: {personality}

        지금까지 질문: {previous_question}
        지원자 답변: {previous_answer}

        지원자의 이력서 키워드: {keywords}
            
        이전 대화 내용: {history}

        위 정보를 참고하여, 중복되지 않고 심층적인 다음 질문을 한 개 생성하세요.
        해당 질문은 면접 유형과 부합하며, 질문만 출력하고 분석이나 설명은 하지 마세요.
        """)
    ])

    memory = ConversationBufferMemory(
        memory_key="history",
        input_key="previous_answer",
        return_messages=False
    )

    # LLMChain을 persona_template과 결합
    chain = LLMChain(llm=llm, prompt=persona_template, memory=memory, verbose=True)
    return chain

def generate_follow_up_questions(chain, question, answer, keywords, interview_type, personality):
    # 꼬리 질문 2개 생성용 LLM 호출
    # 프롬프트에는 이전 질문, 답변, 키워드, 면접 유형 포함
    variables = {
        "previous_question": question,
        "previous_answer": answer,
        "keywords": ", ".join(keywords),
        "interview_type": interview_type,
        "personality": personality,
    }
    # LLM이 꼬리 질문 2개를 생성하도록 지시해야 함 (prompt 템플릿이나 persona에서 조정 가능)
    response = chain.run(variables)

    return response

def get_user_interview_preferences():
    valid_types = ["인성", "경험", "상황"]
    valid_personalities = ["친절", "까다로움", "중립"]  # 예시

    while True:
        interview_type = input(f"면접 유형을 선택하세요 {valid_types}: ").strip()
        if interview_type in valid_types:
            break
        print("올바른 면접 유형을 선택하세요.")

    while True:
        personality = input(f"면접관 성향을 선택하세요 {valid_personalities}: ").strip()
        if personality in valid_personalities:
            break
        print("올바른 면접관 성향을 선택하세요.")

    return interview_type, personality

def main():
    interview_type, personality = get_user_interview_preferences()

    # 질문 DB에서 유형별 질문 총 5개 가져오기
    questions = fetch_questions(interview_type)

    # 이력서에서 추출된 키워드 리스트 예시
    keywords = [
    # 분야 및 직무
    "DT 직무", "디지털 기술", "산업 혁신", "업무 효율화", "산업 발전",

    # 기술 및 연구 경험
    "AI 모델 실험", "프롬프트 설계", "저해상도 이미지 복원", "Chain of Thought (CoT)", 
    "Azure 보행자 분류 모델", "대규모 데이터셋 처리", "Pytorch DataLoader", "데이터셋 증강", "모델 성능 향상",

    # 업무 역량 및 태도
    "문제 해결력", "전략 수립", "업무 효율성 개선", "팀 소통", "책임감", "협업", "팀 리더십", "갈등 조율",

    # 언어 및 국제 경험
    "캐나다 어학연수", "영어 회화 능력", "OPIc AL 등급",

    # 개인 성장
    "도전 정신", "호기심", "적극적인 태도", "자기 주도성"
    ]

    chain = init_llm_chain()

    for q_id, question, interview_type in questions:
        print(f"\n[질문] {question}")
        answer = input("답변을 입력하세요: ")

        for i in range(2):
            follow_up = generate_follow_up_questions(chain, question, answer, keywords, interview_type, personality)
            print(f"[꼬리 질문 {i+1}] {follow_up}")
            answer = input("꼬리 질문 답변을 입력하세요: ")

if __name__ == "__main__":
    main()
