#export GOOGLE_APPLICATION_CREDENTIALS="/data1/home/yyk/ICT_proj/magnificent-ray-469309-m3-b4681165c18a.json"
import sqlite3
import random
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_google_vertexai import ChatVertexAI
import vertexai

#--------------------- DB에서 무작위 질문 뽑기 -------------------------
def get_random_question(db_path='interview_questions.db'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, question, interview_type FROM interview_questions")
    questions = cur.fetchall()
    conn.close()
    if not questions:
        return None
    return random.choice(questions)  # (id, question, interview_type)

#---------------------LangChain PromptTemplate 적용-------------------------
def init_llm_chain():
    PROJECT_ID = "magnificent-ray-469309-m3"
    REGION = "us-central1"

    # Vertex AI 초기화
    vertexai.init(project=PROJECT_ID, location=REGION)
    llm = ChatVertexAI(model="gemini-2.0-flash-001", temperature=0.7)

    persona_template = """
    당신은 {interview_type} 면접을 진행하는 면접관입니다.
    면접 대상자는 {job_role} 직무를 희망하는 지원자이며,  
    면접 난이도는 {difficulty} 수준입니다.

    지금까지 다음과 같은 질문을 했고, 지원자는 이렇게 답변했습니다:
    질문: {previous_question}
    답변: {previous_answer}

    지원자의 답변을 분석하여 강점과 약점을 메모리에 기록하면서,  
    중복되지 않고 이 답변과 관련된, {interview_type} 면접 특성에 맞는  
    후속 질문을 하나만 제시해 주세요.

    후속 질문은 구체적이고 심층적이어야 합니다.
    """
    prompt = ChatPromptTemplate.from_template(persona_template)
    return LLMChain(llm=llm, prompt=prompt)

def main():
    # 무작위 질문 뽑기
    q = get_random_question()
    if not q:
        print("질문 데이터가 없습니다.")
        return
    
    print(get_random_question())

    q_id, question_text, interview_type = q
    print(f"면접 질문: {question_text}")

    # 사용자 답변 입력 받기
    user_answer = input("답변을 입력하세요: ")

    persona_chain = init_llm_chain()
    response = persona_chain.run(
        interview_type=interview_type,
        job_role="백엔드 개발자",
        difficulty="중간",
        previous_question=question_text,
        previous_answer=user_answer
    )

    print("\n[LLM 후속 질문]")
    print(response)

if __name__ == "__main__":
    main()